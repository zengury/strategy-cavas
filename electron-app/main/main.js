const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow = null;

function createWindow() {
  const opts = {
    width: 1600, height: 900,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.js'),
    },
  };
  if (process.platform === 'darwin') opts.titleBarStyle = 'hiddenInset';

  mainWindow = new BrowserWindow(opts);
  mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  mainWindow.on('closed', () => { mainWindow = null; });
}

const registerIpcHandlers = require('./ipc-handlers');

app.whenReady().then(() => {
  createWindow();
  registerIpcHandlers(ipcMain, mainWindow);
});

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
    registerIpcHandlers(ipcMain, mainWindow);
  }
});
