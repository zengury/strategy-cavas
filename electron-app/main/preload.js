const { contextBridge } = require('electron');

// Minimal preload — the web frontend handles all UI via WebSocket to the Python backend.
// Expose only desktop-specific info.

contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  isElectron: true,
});
