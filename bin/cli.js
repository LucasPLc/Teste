#!/usr/bin/env node
/**
 * CLI do pacote npm "saam-rotina178".
 * - Instala requirements Python (idempotente)
 * - Sobe server.py em STDIO
 * - Faz auto-registro no MCP Manager
 */

const { spawn, spawnSync } = require('child_process');
const path = require('path');
const fs   = require('fs');

// ---------- Configurações ----------
const PYTHON = process.env.PYTHON_EXEC || 'python3';
const PROJECT_ROOT = path.resolve(__dirname, '..');
const SERVER_PY    = path.join(PROJECT_ROOT, 'saam_rotina178', 'server.py');
const REQUIREMENTS = path.join(PROJECT_ROOT, 'requirements.txt');

const API_BASE_URL   = process.env.API_BASE_URL   || 'http://localhost:8080/api';
const MCP_MANAGER_URL = process.env.MCP_MANAGER_URL || 'http://localhost:8000';

// ---------- 1. Garante libs Python ----------
if (fs.existsSync(REQUIREMENTS)) {
  console.log('[CLI] Instalando dependências Python… (idempotente)');
  spawnSync(
    PYTHON,
    ['-m', 'pip', 'install', '--quiet', '-r', REQUIREMENTS],
    { stdio: 'inherit' }
  );
}

// ---------- 2. Sobe o server.py ----------
const extraArgs = process.argv.slice(2);  // permite repassar flags
const child = spawn(
  PYTHON,
  [SERVER_PY, ...extraArgs],
  {
    stdio: 'inherit',
    env: { ...process.env, PYTHONUNBUFFERED: '1', API_BASE_URL }
  }
);

child.on('exit', code => process.exit(code));

// ---------- 3. Auto-registro no MCP Manager ----------
(async () => {
  // Pequeno delay para dar tempo do FastMCP inicializar
  await new Promise(r => setTimeout(r, 1000));

  const payload = {
    name: 'saam_rotina178',
    command: PYTHON,
    args: [SERVER_PY],
    cwd:  PROJECT_ROOT,
    env:  { API_BASE_URL }
  };

  try {
    const res = await fetch(`${MCP_MANAGER_URL}/startServer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config: payload, timeout: 30 })
    });

    if (!res.ok) {
      const txt = await res.text();
      console.error(`[CLI] ⚠️  Falha ao registrar MCP: ${res.status} – ${txt}`);
    } else {
      console.log('[CLI] ✅ MCP registrado com sucesso.');
    }
  } catch (err) {
    console.error('[CLI] ⚠️  Erro no auto-registro MCP:', err.message);
  }
})();
