
import os
import httpx
import logging
import sys
import json
from typing import Optional
from mcp.server.fastmcp import FastMCP

# --- Logging ---
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_file = "mcp_rotina178.log"
logger = logging.getLogger("MCP_Rotina178")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

API_BASE_URL = os.environ.get("API_BASE_URL", "")
USER_AGENT = "mcp-rotina178-server/1.0"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RELATORIOS_DIR = os.path.join(SCRIPT_DIR, "relatorios_json")

# --- Utilitário de request HTTP ---
async def api_request(method, endpoint, **kwargs):
    url = f"{API_BASE_URL}{endpoint}"
    headers = kwargs.pop("headers", {})
    headers["User-Agent"] = USER_AGENT
    timeout = kwargs.pop("timeout", 180.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.request(method, url, headers=headers, **kwargs)
    return response

# --- MCP Server ---
try:
    mcp = FastMCP("saam_rotina178")
    logger.info("Servidor MCP da Rotina 1.7.8 inicializado.")
except Exception as e:
    logger.exception("Erro ao inicializar FastMCP.")
    print(f"ERRO ao inicializar FastMCP: {e}", file=sys.stderr)
    raise

# --- Ajuda geral ---
@mcp.tool()
async def instrucoes_gerais() -> str:
    return (
        "Você é um agente especialista em relatórios fiscais da Rotina 1.7.8 do SAAM.\n"
        "Fluxo atualizado para JSON:\n"
        "1. Use `listar_periodos`, `listar_tipos_emissao`, `listar_tipos_operacao` e `listar_abas` para buscar as opções disponíveis.\n"
        "2. Gere o relatório em JSON com `gerar_relatorio_json`, que salva 3 arquivos para cada tabela (C100 e C170).\n"
        "3. Para analisar TODO o conteúdo dos relatórios salvos, use `extrair_todos_jsons`, que extrai em partes, se necessário.\n"
        "Os arquivos JSON podem ser baixados ou analisados pelo próprio agente via `extrair_todos_jsons`, respeitando o limite máximo por chamada."
    )

# --- Métodos de listagem para opções da IA ---
@mcp.tool()
async def listar_periodos() -> str:
    resp = await api_request("GET", "/periodos/disponiveis")
    logger.info(f"Resposta /periodos/disponiveis: {resp.text}")
    if resp.status_code == 200:
        periodos = resp.json()
        texto = "\n".join([f"De {p['dtIn']} até {p['dtFin']}" for p in periodos])
        return "Períodos disponíveis:\n" + texto
    return f"Erro ao listar períodos: {resp.status_code} - {resp.text}"

@mcp.tool()
async def listar_tipos_emissao() -> str:
    resp = await api_request("GET", "/tipos/emissao")
    logger.info(f"Resposta /tipos/emissao: {resp.text}")
    if resp.status_code == 200:
        tipos = resp.json()
        texto = "\n".join([f"{t['codigo']} - {t['descricao']}" for t in tipos])
        return "Tipos de emissão disponíveis:\n" + texto
    return f"Erro ao listar tipos de emissão: {resp.status_code} - {resp.text}"

@mcp.tool()
async def listar_tipos_operacao() -> str:
    resp = await api_request("GET", "/tipos/operacao")
    logger.info(f"Resposta /tipos/operacao: {resp.text}")
    if resp.status_code == 200:
        tipos = resp.json()
        texto = "\n".join([f"{t['codigo']} - {t['descricao']}" for t in tipos])
        return "Tipos de operação disponíveis:\n" + texto
    return f"Erro ao listar tipos de operação: {resp.status_code} - {resp.text}"

@mcp.tool()
async def listar_abas() -> str:
    resp = await api_request("GET", "/tipos/abas")
    logger.info(f"Resposta /tipos/abas: {resp.text}")
    if resp.status_code == 200:
        abas = resp.json()
        texto = "\n".join([f"{a['codigo']} - {a['descricao']}" for a in abas])
        return "Abas disponíveis:\n" + texto
    return f"Erro ao listar abas: {resp.status_code} - {resp.text}"

# --- Geração do relatório em 3 arquivos JSON para cada tabela ---
@mcp.tool()
async def gerar_relatorio_json(
    tabela: str,
    periodo_inicial: str,
    periodo_final: Optional[str] = None,
    tipo_emissao: Optional[str] = None,
    tipo_operacao: Optional[str] = None,
    aba: Optional[str] = None
) -> str:
    try:
        payload = {"periodoInicial": periodo_inicial}
        if periodo_final: payload["periodoFinal"] = periodo_final
        if tipo_emissao: payload["tipoEmissao"] = tipo_emissao
        if tipo_operacao: payload["tipoOperacao"] = tipo_operacao
        if aba: payload["aba"] = aba

        os.makedirs(RELATORIOS_DIR, exist_ok=True)
        base_name = f"{tabela}_{periodo_inicial}_{periodo_final or ''}_{tipo_emissao or ''}_{tipo_operacao or ''}_{aba or ''}".replace("/", "-")

        try:
            endpoint = f"/relatorio/buscar/{tabela.lower()}"  # Ex: /relatorio/buscar/relatorio_notas_c100
            resp = await api_request("POST", endpoint, json=payload, timeout=180.0)
        except httpx.TimeoutException:
            logger.error(f"Timeout ao buscar dados para {tabela}.")
            return f"Timeout ao buscar dados para {tabela}. Reduza o período ou use filtros mais restritos."
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar relatório {tabela}: {e}")
            return f"Erro inesperado ao buscar relatório {tabela}: {e}"

        logger.info(f"Resposta do backend ({tabela}): {resp.text[:500]}")

        if resp.status_code != 200:
            logger.error(f"Erro ao buscar relatório: {resp.status_code} - {resp.text}")
            return f"Erro ao gerar relatório: {resp.status_code} - {resp.text}"

        try:
            resultado = resp.json()
            if not isinstance(resultado, list):
                logger.error(f"Resposta inesperada do backend: {resultado}")
                return f"Erro: resposta inesperada do backend: {resultado}"
            if not resultado:
                logger.info(f"Resposta vazia para {tabela}.")
                return "Nenhum dado retornado para os filtros especificados."
        except Exception as e:
            logger.error(f"Erro ao processar resposta: {e}\nConteúdo: {resp.text[:1000]}")
            return f"Erro ao processar resposta: {e}"

        # Divide o resultado em 3 partes iguais
        total = len(resultado)
        partes = 3
        tamanho_parte = (total + partes - 1) // partes

        arquivos = []
        for idx in range(partes):
            inicio = idx * tamanho_parte
            fim = min((idx + 1) * tamanho_parte, total)
            chunk = resultado[inicio:fim]
            if not chunk:
                continue

            fname = f"{base_name}_parte{idx + 1}.json"
            fpath = os.path.join(RELATORIOS_DIR, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(chunk, f, ensure_ascii=False, indent=2)
            arquivos.append(fname)
            logger.info(f"Arquivo {fname} salvo ({len(chunk)} registros).")

        if arquivos:
            logger.info(f"Relatório {tabela} finalizado: {len(arquivos)} arquivos, {total} registros.")
            return f"Relatório JSON salvo em {len(arquivos)} arquivo(s) para {tabela}: " + ", ".join(arquivos) + f" | Total de registros: {total}"
        else:
            logger.info("Nenhum dado retornado para os filtros especificados.")
            return "Nenhum dado retornado para os filtros especificados."
    except Exception as e:
        logger.exception("Erro fatal inesperado na geração de relatório.")
        return f"Erro fatal inesperado: {e}"

# --- Extrai texto de todos JSONs gerados (com paginação) ---
@mcp.tool()
async def extrair_todos_jsons(offset: int = 0, limite: int = 100_000) -> str:
    """
    Extrai todo o conteúdo dos JSONs gerados no diretório, concatenando em um único texto.
    Permite controle via offset e limite para extrair até 100.000 caracteres por vez.
    """
    if not os.path.exists(RELATORIOS_DIR):
        return "Diretório de relatórios JSON não encontrado."
    files = sorted([f for f in os.listdir(RELATORIOS_DIR) if f.endswith(".json")])
    if not files:
        return "Nenhum arquivo JSON encontrado para extrair."
    all_text = ""
    for fname in files:
        fpath = os.path.join(RELATORIOS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
                all_text += f"\n\n===== {fname} =====\n\n" + content
        except Exception as e:
            all_text += f"\n\nErro ao ler {fname}: {e}\n"
    total_len = len(all_text)
    if offset > total_len:
        return "Offset maior que o tamanho total do conteúdo!"
    result = all_text[offset:offset + limite]
    fim = min(offset + limite, total_len)
    info = f"[Trecho extraído de {offset} até {fim} de {total_len} caracteres.]\n\n"
    return info + result

# --- Inicialização do MCP ---
if __name__ == "__main__":
    os.makedirs(RELATORIOS_DIR, exist_ok=True)
    mcp.run(transport='stdio')



