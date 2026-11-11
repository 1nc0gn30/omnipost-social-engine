#!/usr/bin/env node
/**
 * Omnipost Social Engine — Unified Workstation & CLI Launcher
 * Launches the loopback Web UI (port 8091), Electron Desktop Workstation, or Python CLI/MCP server.
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const rootDir = path.resolve(__dirname, '..');
const srcDir = path.join(rootDir, 'src');
const args = process.argv.slice(2);
const defaultPort = process.env.PORT || '8091';

const isWeb = args[0] === 'web' || args.includes('--web');
const isAppRequest =
  !isWeb &&
  (args.length === 0 ||
    args.includes('--gui') ||
    args.includes('--app') ||
    args.includes('--desktop') ||
    args[0] === 'app' ||
    args[0] === 'desktop' ||
    args[0] === 'gui');

if (isWeb) {
  console.log(`[OmniPost] Launching Web UI on http://127.0.0.1:${defaultPort} ...`);
  const pyChild = spawn(
    'python3',
    ['-m', 'omnipost_social_engine.cli', 'serve', '--host', '127.0.0.1', '--port', String(defaultPort)],
    {
      cwd: rootDir,
      stdio: 'inherit',
      env: {
        ...process.env,
        PYTHONPATH: process.env.PYTHONPATH ? `${srcDir}:${process.env.PYTHONPATH}` : srcDir,
        ZOTH_ZERO_EGRESS: 'true',
      },
    }
  );
  pyChild.on('error', (pyErr) => {
    console.error('[OmniPost] Failed to start web server:', pyErr);
  });
} else if (isAppRequest) {
  console.log('[OmniPost] Launching Desktop Workstation...');

  const candidateElectronPaths = [
    path.join(rootDir, 'node_modules', '.bin', 'electron'),
    '/usr/local/bin/electron',
    '/usr/bin/electron',
  ];

  let electronCmd = 'electron';
  for (const p of candidateElectronPaths) {
    if (fs.existsSync(p)) {
      electronCmd = p;
      break;
    }
  }

  const child = spawn(electronCmd, ['.'], {
    cwd: rootDir,
    stdio: 'inherit',
    env: {
      ...process.env,
      PORT: String(defaultPort),
      PYTHONPATH: process.env.PYTHONPATH ? `${srcDir}:${process.env.PYTHONPATH}` : srcDir,
      ELECTRON_ENABLE_LOGGING: '1',
      ZOTH_ZERO_EGRESS: 'true',
    },
  });

  child.on('error', (err) => {
    console.warn(`[OmniPost] Electron notice: ${err.message}. Starting web UI on port ${defaultPort}...`);
    const pyChild = spawn(
      'python3',
      ['-m', 'omnipost_social_engine.cli', 'serve', '--host', '127.0.0.1', '--port', String(defaultPort)],
      {
        cwd: rootDir,
        stdio: 'inherit',
        env: {
          ...process.env,
          PYTHONPATH: process.env.PYTHONPATH ? `${srcDir}:${process.env.PYTHONPATH}` : srcDir,
        },
      }
    );
    pyChild.on('error', (pyErr) => {
      console.error('[OmniPost] Failed to start backend:', pyErr);
    });
  });
} else {
  const child = spawn('python3', ['-m', 'omnipost_social_engine.cli', ...args], {
    cwd: rootDir,
    stdio: 'inherit',
    env: {
      ...process.env,
      PYTHONPATH: process.env.PYTHONPATH ? `${srcDir}:${process.env.PYTHONPATH}` : srcDir,
    },
  });

  child.on('exit', (code) => {
    process.exit(code || 0);
  });
}
