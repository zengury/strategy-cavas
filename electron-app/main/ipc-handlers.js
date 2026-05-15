const path = require('path');
const { app } = require('electron');
const store = require('./store');
const ConversationEngine = require('./engine/conversation');
const { SkillRegistry } = require('./engine/skill-registry');
const { SkillRouter } = require('./engine/skill-router');
const { ContextBus } = require('./engine/context-bus');
const { CanvasStateManager } = require('./engine/canvas-state');

let engine = null;

function getSkillsDir() {
  return app.isPackaged
    ? path.join(process.resourcesPath, 'skills')
    : path.join(__dirname, '../../skills');
}

function initEngine() {
  const apiKey = store.getApiKey();
  const model = store.getModel();
  if (!apiKey) { engine = null; return; }

  const Anthropic = require('@anthropic-ai/sdk').default || require('@anthropic-ai/sdk');
  const client = new Anthropic({ apiKey });
  const registry = new SkillRegistry(getSkillsDir());
  const router = new SkillRouter(registry, client, model);
  const contextBus = new ContextBus();
  const canvasManager = new CanvasStateManager();
  engine = new ConversationEngine(registry, router, contextBus, canvasManager, client, model);
}

function registerIpcHandlers(ipcMain, mainWindow) {
  initEngine();

  ipcMain.on('chat:send', async (event, text) => {
    try {
      mainWindow.webContents.send('chat:thinking');
      if (!engine) initEngine();
      if (!engine) {
        mainWindow.webContents.send('chat:response', { error: true, message: 'Please set your API key in settings.' });
        return;
      }
      const result = await engine.processTurn(text);
      mainWindow.webContents.send('chat:response', result);
    } catch (err) {
      mainWindow.webContents.send('chat:response', { error: true, message: err.message || 'Unexpected error' });
    }
  });

  ipcMain.handle('settings:getApiKey', () => store.getApiKey());
  ipcMain.handle('settings:setApiKey', (e, key) => { store.setApiKey(key); initEngine(); return true; });
  ipcMain.handle('settings:getModel', () => store.getModel());
  ipcMain.handle('settings:setModel', (e, model) => { store.setModel(model); initEngine(); return true; });
  ipcMain.handle('session:reset', () => { initEngine(); return true; });
}

module.exports = registerIpcHandlers;
