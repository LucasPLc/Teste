#!/bin/bash

# Instalação do pacote
python -m pip install --no-cache-dir 'https://github.com/LucasPLc/Teste/archive/refs/tags/v0.1.0.zip'

# Execução do servidor MCP
python -m saam_rotina178.server
