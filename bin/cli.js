#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');

const python = process.env.PYTHON_EXEC || 'python';
const serverPy = path.resolve(__dirname, '..', 'saam_rotina178', 'server.py');
const args = process.argv.slice(2);

const child = spawn(python, [serverPy, ...args], {
  stdio: 'inherit',
  env: { ...process.env, PYTHONUNBUFFERED: '1' }
});

child.on('exit', code => process.exit(code));
