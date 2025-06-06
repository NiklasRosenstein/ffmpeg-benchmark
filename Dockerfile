FROM linuxserver/ffmpeg:latest

RUN apt-get update && apt-get install git -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.7.2 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    unset VIRTUAL_ENV && uv sync --frozen --no-install-project --no-dev

ADD pyproject.toml uv.lock README.md /app
ADD ffmpeg_benchmark /app/ffmpeg_benchmark

RUN --mount=type=cache,target=/root/.cache/uv \
    unset VIRTUAL_ENV && uv sync --frozen --no-dev

RUN ln -s /app/.venv/bin/ffmpeg-benchmark /bin/ffmpeg-benchmark

VOLUME /assets

ENTRYPOINT ["/bin/ffmpeg-benchmark"]
