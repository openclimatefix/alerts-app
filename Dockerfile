# --- Build image: install the app and its dependencies into a virtual env --- #
FROM python:3.14-slim AS build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# * Compile bytecode to reduce startup time
# * Disable cache to reduce image size
# * Use the image's Python, so the virtual env still works in the runtime image
ENV UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dependencies first, so this layer is reused when only the code changes
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN uv sync --locked --no-dev --no-editable

# --- Runtime image: only the virtual env --- #
FROM python:3.14-slim

COPY --from=build /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

CMD ["check-alerts"]
