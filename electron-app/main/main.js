const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const net = require('net');

let mainWindow = null;
let pythonProcess = null;
let pythonPort = null;

// ── Port discovery ──────────────────────────────────────────

function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
    server.on('error', reject);
  });
}

// ── Python backend ──────────────────────────────────────────

async function startPythonBackend() {
  pythonPort = await findFreePort();

  const pythonPath = app.isPackaged
    ? path.join(process.resourcesPath, 'python-backend', 'main.py')
    : path.join(__dirname, '../../main.py');

  const skillsDir = app.isPackaged
    ? path.join(process.resourcesPath, 'python-backend', 'skills')
    : path.join(__dirname, '../../skills');

  const configDir = app.isPackaged
    ? path.join(process.resourcesPath, 'python-backend', 'config')
    : path.join(__dirname, '../../config');

  const env = {
    ...process.env,
    PORT: String(pythonPort),
    SKILLS_DIR: skillsDir,
    CONFIG_DIR: configDir,
    DEEPSEEK_API_KEY: process.env.DEEPSEEK_API_KEY || '',
  };

  pythonProcess = spawn('python3', [pythonPath, '--port', String(pythonPort)], {
    env,
    stdio: ['pipe', 'pipe', 'pipe'],
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[python] ${data.toString().trim()}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`[python:err] ${data.toString().trim()}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`[python] exited with code ${code}`);
    pythonProcess = null;
  });

  // Wait for server to be ready
  await waitForServer(`http://127.0.0.1:${pythonPort}`, 15000);
}

function stopPythonBackend() {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM');
    pythonProcess = null;
  }
}

function waitForServer(url, timeoutMs) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const tryConnect = () => {
      const http = require('http');
      http.get(url, (res) => {
        resolve();
      }).on('error', () => {
        if (Date.now() - start > timeoutMs) {
          reject(new Error(`Server at ${url} did not start within ${timeoutMs}ms`));
        } else {
          setTimeout(tryConnect, 300);
        }
      });
    };
    setTimeout(tryConnect, 500);
  });
}

// ── Window ──────────────────────────────────────────────────

async function createWindow() {
  await startPythonBackend();

  mainWindow = new BrowserWindow({
    width: 1600,
    height: 900,
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  mainWindow.loadURL(`http://127.0.0.1:${pythonPort}`);
  mainWindow.on('closed', () => { mainWindow = null; });
}

// ── App lifecycle ────────────────────────────────────────────

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  stopPythonBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', stopPythonBackend);
