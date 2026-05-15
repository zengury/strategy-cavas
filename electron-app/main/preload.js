const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  sendChat(text) { ipcRenderer.send('chat:send', text); },
  onThinking(callback) { ipcRenderer.on('chat:thinking', callback); },
  onResponse(callback) { ipcRenderer.on('chat:response', (e, data) => callback(data)); },
  getApiKey() { return ipcRenderer.invoke('settings:getApiKey'); },
  setApiKey(key) { return ipcRenderer.invoke('settings:setApiKey', key); },
  getModel() { return ipcRenderer.invoke('settings:getModel'); },
  setModel(model) { return ipcRenderer.invoke('settings:setModel', model); },
  resetSession() { return ipcRenderer.invoke('session:reset'); },
  removeListeners() {
    ipcRenderer.removeAllListeners('chat:thinking');
    ipcRenderer.removeAllListeners('chat:response');
  },
});
