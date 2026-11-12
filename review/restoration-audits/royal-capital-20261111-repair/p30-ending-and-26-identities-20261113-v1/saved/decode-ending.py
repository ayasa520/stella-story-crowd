"""Decode the entire closed recording without inferring a player-clock origin.

Every retained video frame is available at original recording resolution.
There is no timestamp clipping, speed adjustment or image interpretation.
The delegated reviewer locates lifecycle boundaries visually after closure.
"""
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
closure = json.loads((HERE / 'closure.json').read_text())
assert all(closure.get(key) is True for key in
           ['browserProcessesExited', 'cliNoBrowsers', 'recordingFfmpegExited', 'adapterExited'])
frames = HERE / 'ending-frames'
frames.mkdir(exist_ok=False)
video = HERE / 'saved-ending-34-to-finish.webm'
probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                        'format=duration:stream=codec_name,codec_type,width,height,r_frame_rate',
                        '-of', 'json', str(video)], capture_output=True, check=True)
(HERE / 'ending-video-probe.json').write_bytes(probe.stdout)
command = ['ffmpeg', '-nostdin', '-hide_banner', '-threads', '1',
           '-filter_threads', '1', '-filter_complex_threads', '1', '-i', str(video),
           '-map', '0:v:0', '-an', '-pix_fmt', 'yuvj420p', '-c:v', 'mjpeg',
           '-threads:v', '1', '-q:v', '3', '-fps_mode', 'passthrough',
           str(frames / 'frame-%05d.jpg')]
with (HERE / 'decode-ending.stdout.txt').open('wb') as stdout, \
        (HERE / 'decode-ending.stderr.txt').open('wb') as stderr:
    result = subprocess.run(command, stdout=stdout, stderr=stderr)
result.check_returncode()
count = len(list(frames.glob('frame-*.jpg')))
(HERE / 'ending-frame-plan.json').write_text(json.dumps(dict(
    input=str(video), directory=str(frames), count=count, decodedFromStart=True,
    originalRecordingResolution=[1280, 1000], framesResampled=False,
    unifiedFramePlayerClockOriginProven=False, nativeTimingAccepted=False,
    processExited=True, decoderThreads=1, filterThreads=1, encoderThreads=1,
    nice=19, cpuAffinity=[0, 1]), indent=2) + '\n')
print(json.dumps(dict(decodedFrames=count, decoderExited=True)), flush=True)
