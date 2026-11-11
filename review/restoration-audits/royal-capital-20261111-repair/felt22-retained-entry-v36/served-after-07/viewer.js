import {decodeMotion, applyMotion} from './motion.js';
import {VoiceLipSync} from './lipsync.js';
import {loadLive2DModel, releaseLive2DModel} from './model_resources.js';

export const assetURL = member => '/asset/' + member.split('/').map(encodeURIComponent).join('/');

async function getJSON(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`资源读取失败 (${response.status})：${url}`);
  return response.json();
}

export class PairingViewer {
  constructor(stage, canvas, onTime, onError, {app, visibleOnLoad = true} = {}) {
    this.stage = stage;
    this.onTime = onTime;
    this.onError = onError;
    this.visibleOnLoad = visibleOnLoad;
    // All actors in one document must share one GL context: Cubism's shader
    // singleton owns GL programs. Each viewer still owns its model and clocks.
    this.app = app || new PIXI.Application({view: canvas, resizeTo: stage, backgroundAlpha: 0,
      antialias: true, autoDensity: true, resolution: Math.min(devicePixelRatio, 2)});
    this.audio = new Audio();
    this.audio.volume = 0.8;
    this.generation = 0;
    this.loadGeneration = 0;
    this.tracks = [];
    this.heldTracks = [];
    this.neutral = [];
    this.time = 0;
    this.duration = 0;
    this.speed = 1;
    this.loop = false;
    this.playing = false;
    this.hasAudio = false;
    this.ready = false;
    this.envelope = null;
    this.audio.addEventListener('error', () => onError(new Error('语音读取失败，请查看日志。')));
    this.app.ticker.add(() => this.tick());
    new ResizeObserver(() => this.fit()).observe(stage);
    let drag;
    canvas.addEventListener('pointerdown', event => {
      if (!this.model || this.lockPlacement) return;
      drag = {x: event.clientX, y: event.clientY, mx: this.model.x, my: this.model.y};
      canvas.setPointerCapture(event.pointerId);
    });
    canvas.addEventListener('pointermove', event => {
      if (drag && this.model) this.model.position.set(drag.mx + event.clientX - drag.x,
                                                     drag.my + event.clientY - drag.y);
    });
    canvas.addEventListener('pointerup', () => {drag = null;});
    canvas.addEventListener('wheel', event => {
      event.preventDefault();
      if (!this.model || this.lockPlacement) return;
      const factor = Math.exp(-event.deltaY * 0.001);
      const next = Math.max(this.fitScale * 0.3, Math.min(this.fitScale * 6, this.model.scale.x * factor));
      this.model.scale.set(next);
    }, {passive: false});
  }

  async load(detail) {
    const generation = ++this.loadGeneration;
    this.stop();
    this.ready = false;
    const url = assetURL(detail.member);
    const document = await getJSON(url);
    const groups = document.Groups || [];
    // The archive groups all motions under an unnamed group. Do not let the
    // display library preload thousands of clips or choose an idle animation.
    // Our explicit tracks drive original parameter curves at a shared time.
    document.FileReferences.Motions = {};
    document.url = new URL(url, location.href).href;
    const model = await loadLive2DModel(document,
      {autoInteract: false, motionPreload: 'NONE', idleMotionGroup: '__manual__'});
    // A loaded candidate holds a texture lease until it is installed or
    // discarded. Cancellation and preparation errors release that same lease;
    // neither path may destroy an atlas used by the currently visible model.
    let installed = false;
    try {
      const neutral = await Promise.all(detail.motions
        .filter(row => this.config.neutral_motions.includes(row.token))
        .sort((a, b) => (a.kind === 'face') - (b.kind === 'face'))
        .map(row => getJSON(assetURL(row.member)).then(decodeMotion)));
      const mouthRows = [this.config.lip_sync.closed_motion, this.config.lip_sync.range_motion]
        .map(token => detail.motions.find(row => row.token === token));
      const mouth = mouthRows.every(Boolean) ? await Promise.all(mouthRows
        .map(row => getJSON(assetURL(row.member)).then(decodeMotion))) : [];
      if (generation !== this.loadGeneration) return false;
      if (this.model) {
        this.app.stage.removeChild(this.model);
        releaseLive2DModel(this.model);
      }
      this.model = model;
      this.detail = detail;
      this.groups = groups;
      this.motionCache = new Map();
      this.tracks = [];
      this.neutral = neutral;
      this.lips = new VoiceLipSync(this.config.lip_sync, groups, ...mouth);
      this.core = model.internalModel.coreModel;
      const native = this.core.getModel();
      this.parameters = native.parameters.defaultValues.slice();
      this.parts = native.parts.opacities.slice();
      this.baseWidth = model.width;
      this.baseHeight = model.height;
      // Group composition owns the reveal. Set visibility before attaching
      // the model: animation and lighting preparation continue asynchronously
      // after this method returns, while PIXI can render between those awaits.
      model.visible = this.visibleOnLoad;
      this.app.stage.addChild(model);
      model.internalModel.on('beforeModelUpdate', () => this.renderPose());
      this.fit();
      this.ready = true;
      installed = true;
      console.info('MODEL_READY', detail.id, native.parameters.count, this.baseWidth, this.baseHeight, 'visible='+model.visible);
      return true;
    } finally {
      if (!installed) releaseLive2DModel(model);
    }
  }

  fit() {
    if (!this.model) return;
    this.fitScale = Math.min(this.stage.clientWidth / this.baseWidth,
                            this.stage.clientHeight / this.baseHeight) * 0.97;
    this.model.scale.set(this.fitScale);
    this.model.anchor.set(0.5, 0.5);
    this.model.position.set(this.stage.clientWidth/2, this.stage.clientHeight/2);
  }

  motion(row) {
    if (!this.motionCache.has(row.member))
      this.motionCache.set(row.member, getJSON(assetURL(row.member)).then(decodeMotion));
    return this.motionCache.get(row.member);
  }

  async play(selection, mode) {
    if (!this.ready) throw new Error('请等待模型加载完成。');
    this.stop();
    const generation = this.generation;
    const tracks = mode === 'voice' ? [] : await Promise.all(
      this.detail.motions.filter(r => [selection.body, selection.face,...(selection.extra||[])].includes(r.token))
        .sort((a, b) => (a.kind === 'face') - (b.kind === 'face')).map(r => this.motion(r)));
    // Story review can retain selected upstream layers at their last pose.
    // Explicit tracks still animate from zero, and voice-only/home previews
    // retain their existing direct-selection behavior.
    const heldTracks = mode === 'voice' ? [] : await Promise.all(
      this.detail.motions.filter(r => (selection.held||[]).includes(r.token))
        .sort((a,b)=>(a.kind==='face')-(b.kind==='face')).map(r=>this.motion(r)));
    if (generation !== this.generation) return;
    const audio = mode !== 'motion' && selection.voice;
    const envelope = audio && this.lips.parameters.length
      ? await this.lips.envelope(assetURL(selection.voice.member)) : null;
    if (generation !== this.generation) return;
    if (audio) {
      await new Promise((resolve, reject) => {
        this.audio.onloadedmetadata = resolve;
        this.audio.onerror = () => reject(new Error('无法读取所选语音。'));
        this.audio.src = assetURL(selection.voice.member);
        this.audio.load();
      });
    }
    if (generation !== this.generation) return;
    this.tracks = tracks;
    this.heldTracks = heldTracks;
    this.envelope = envelope;
    if (envelope) console.info('VOICE_ENVELOPE_READY', selection.voice.cue,
      envelope.duration, this.lips.parameters.map(parameter => parameter.id).join(','));
    this.hasAudio = Boolean(audio);
    this.duration = Math.max(0, ...tracks.map(track => track.duration), audio ? this.audio.duration : 0);
    if (!this.duration&&!selection.allowStill) throw new Error('请选择要预览的动作或语音。');
    this.time = 0;
    this.started = performance.now();
    this.playing = true;
    this.audio.playbackRate = this.speed;
    if (audio) await this.audio.play();
    console.info('PREVIEW_STARTED', mode, selection.body, selection.face, selection.voice?.cue, this.duration);
  }

  stop() {
    this.generation++;
    this.playing = false;
    this.audio.pause();
    this.audio.currentTime = 0;
    this.hasAudio = false;
    this.envelope = null;
    this.time = 0;
    this.tracks = [];
    this.heldTracks = [];
    this.onTime(this.time, this.duration);
  }

  seek(seconds) {
    this.time = seconds;
    this.started = performance.now() - seconds / this.speed * 1000;
    if (this.hasAudio) {
      this.audio.currentTime = Math.min(seconds, this.audio.duration);
      if (this.playing && seconds < this.audio.duration) this.audio.play().catch(this.onError);
    }
    this.onTime(this.time, this.duration);
  }

  setSpeed(speed) {
    this.speed = speed;
    this.audio.playbackRate = speed;
    this.started = performance.now() - this.time / speed * 1000;
  }

  tick() {
    if (!this.playing) return;
    // Audio is the clock while it plays; after a short voice ends, let the
    // remaining body/face motion finish using the synchronized wall clock.
    if (this.hasAudio && !this.audio.paused && !this.audio.ended) {
      this.time = this.audio.currentTime;
      this.started = performance.now() - this.time / this.speed * 1000;
    } else this.time = (performance.now() - this.started) / 1000 * this.speed;
    if (this.time >= this.duration) {
      if (this.loop) {
        this.time = 0;
        this.started = performance.now();
        if (this.hasAudio) {this.audio.currentTime = 0; this.audio.play().catch(this.onError);}
      } else {
        this.time = this.duration;
        this.playing = false;
        this.audio.pause();
      }
    }
    this.onTime(this.time, this.duration);
  }

  poseTracks() {
    return [...this.heldTracks.map(track => ({track, time: track.duration})),
      ...this.tracks.map(track => ({track, time: this.time}))];
  }

  renderPose() {
    try {
      const native = this.core.getModel();
      native.parameters.values.set(this.parameters);
      native.parts.opacities.set(this.parts);
      this.model.alpha = 1;
      const opacity = value => {this.model.alpha = value;};
      for (const track of this.neutral) applyMotion(this.core, track, 0, this.groups, opacity);
      for (const {track, time} of this.poseTracks()) applyMotion(this.core, track, time, this.groups, opacity);
      // Speech always owns mouth opening after the expression has been applied.
      // A cleared envelope closes the mouth on Stop; scrubbing uses the same
      // voice time. No manual mouth choice is saved into a Home action.
      this.lips.apply(this.core, this.envelope, this.time);
    } catch (error) {
      this.tracks = [];
      this.neutral = [];
      this.stop();
      this.onError(error);
    }
  }
}
