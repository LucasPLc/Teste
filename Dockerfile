# Dockerfile na raiz do repositório Teste
FROM python:3.11-slim
WORKDIR /app

# Instala release estável (ZIP)
RUN pip install "https://github.com/LucasPLc/Teste/archive/refs/tags/v0.1.0.zip"

# Variável que o seu código usa
ENV API_BASE_URL=https://also-excluded-myrtle-morocco.trycloudflare.com/api

EXPOSE 8080
CMD ["python", "-m", "saam_rotina178.server", "--transport", "sse", "--port", "8080"]
