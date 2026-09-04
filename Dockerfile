FROM ghcr.io/astral-sh/uv:0.12.9-python3.13-alpine3.23

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/.venv/lib/python3.13/site-packages" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 1. Copy only dependency descriptors first for layer caching
COPY pyproject.toml uv.lock main.py ./

# 2. Sync dependencies, compile bytecode, and remove cache in a single layer
RUN uv sync --frozen --no-dev --compile-bytecode && \
    rm -rf /root/.cache/uv

# 3. Copy the rest of the application
COPY . .

EXPOSE 8080

CMD ["granian", "--interface", "asgi", "main:app", "--host", "0.0.0.0", "--port", "8080"]