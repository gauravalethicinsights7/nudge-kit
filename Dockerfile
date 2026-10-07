# API image — FastAPI (api/main.py) over the real M1-M8 engine.
# Build from the repo root: docker build -t nudge-api .
FROM python:3.12-slim

# g++ and the BLAS headers are runtime requirements, not just build ones:
# PyTensor (under PyMC, models/response.py) compiles its computation graph to
# C on first use and shells out to a compiler to do it. Without these the M6
# adstock fit fails at request time, not at image-build time.
RUN apt-get update && apt-get install -y --no-install-recommends \
      g++ \
      libopenblas-dev \
      curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

# Dependency layer first so code-only changes don't bust the cache.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Migrations run on container start, not at build time — the database isn't
# reachable while the image is being built, and a redeploy must pick up any
# new revision before the app serves a request against the old schema.
CMD ["sh", "-c", "alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port 8000"]
