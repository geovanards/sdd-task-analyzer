# Imagem do TaskAnalyzer: ambiente isolado e reproduzível para o Test Harness.
# Versão do Python conforme CONTEXT_RULES.md (3.12+); imagem "slim" = leve.
FROM python:3.12-slim

# Sem arquivos .pyc e com saída imediata no terminal
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Usuário sem privilégios de administrador (boa prática de segurança)
RUN useradd --create-home --uid 1000 analyzer \
    && mkdir /app && chown analyzer:analyzer /app
WORKDIR /app

# Dependências primeiro: aproveita o cache de camadas do Docker
COPY --chown=analyzer:analyzer requirements.txt .
RUN pip install -r requirements.txt

# Código da aplicação, testes e configuração do pytest
COPY --chown=analyzer:analyzer pytest.ini .
COPY --chown=analyzer:analyzer src/ src/
COPY --chown=analyzer:analyzer tests/ tests/

USER analyzer

# Comando principal: executa o Test Harness
CMD ["pytest", "tests/test_harness.py", "-v"]
