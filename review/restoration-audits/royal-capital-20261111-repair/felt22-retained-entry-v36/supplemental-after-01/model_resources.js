// Live2DModel.from shares PIXI textures between model instances in this page.
// A model owns its Cubism state, but cannot individually own those textures.
// Count completed users and keep zero-user textures alive while another model
// is loading: that pending factory may already hold the same texture before
// its promise resolves. This also covers separate inspector/sampler viewers.
const textureUsers = new Map();
let pendingModels = 0;

function disposeUnusedTextures() {
  if (pendingModels) return;
  for (const [texture, users] of textureUsers) {
    if (users) continue;
    const uid = texture.baseTexture.uid;
    textureUsers.delete(texture);
    texture.destroy(true);
    console.info('MODEL_TEXTURE_DISPOSE', uid);
  }
}

export async function loadLive2DModel(document, options) {
  pendingModels++;
  try {
    const model = await PIXI.live2d.Live2DModel.from(document, options);
    for (const texture of new Set(model.textures)) {
      const users = (textureUsers.get(texture) || 0) + 1;
      textureUsers.set(texture, users);
      console.info('MODEL_TEXTURE_RETAIN', document.url, texture.baseTexture.uid, users);
    }
    return model;
  } finally {
    pendingModels--;
    disposeUnusedTextures();
  }
}

export function releaseLive2DModel(model) {
  const textures = new Set(model.textures);
  // Destroy the instance's renderer/moc/animation state only. Passing texture
  // destruction flags here invalidates other instances using the same atlas.
  model.destroy();
  for (const texture of textures) {
    const users = textureUsers.get(texture) - 1;
    textureUsers.set(texture, users);
    console.info('MODEL_TEXTURE_RELEASE', texture.baseTexture.uid, users, pendingModels);
  }
  disposeUnusedTextures();
}
