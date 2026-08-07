FROM python:3.12-slim
WORKDIR /app

# Build with --build-arg TTS_GPU=true to install GPU-capable builds of both
# ML backends used here (onnxruntime for Piper, torch for Kokoro) instead of
# their CPU-only default builds. This only prepares the image to be able to
# use a GPU -- actually engaging it also needs the container run with GPU
# access (--gpus / the compose file's NVIDIA deploy block) and TTS_DEVICE=cuda
# set at runtime; see docker-compose.tts.yml. Both engines' dependencies are
# always installed regardless of TTS_ENGINE, so switching engines is a plain
# env var change with no rebuild required.
ARG TTS_GPU=false

# torch first, from the CPU-only wheel index -- kokoro's own "torch"
# dependency is unconstrained and would otherwise pull PyPI's default Linux
# build, which bundles CUDA runtime libs (large) even when never used.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$TTS_GPU" = "true" ]; then \
         pip install --no-cache-dir --force-reinstall onnxruntime-gpu; \
         pip install --no-cache-dir --force-reinstall torch; \
       fi

# Kokoro's English G2P (misaki.en.G2P) needs this spaCy model and otherwise
# tries to `pip install` it at runtime on first use -- which fails as the
# non-root "app" user below (no writable site-packages) even before
# considering that a request handler shouldn't be doing network installs.
# Pre-install it here, as root, at build time instead.
RUN python -m spacy download en_core_web_sm

COPY . .

RUN addgroup --system --gid 1000 app && \
    adduser --system --uid 1000 --ingroup app --no-create-home app && \
    mkdir -p /data/voices && \
    chown -R app:app /app /data/voices
USER app

# Kokoro downloads its base model + voice packs via huggingface_hub, which
# defaults to caching under $HOME (~/.cache/huggingface) -- the "app" user
# has no home directory (--no-create-home), so that fails with a permission
# error. Point it at the already-writable, volume-backed model dir instead,
# both so it works at all and so downloads persist across container restarts
# the same way Piper's models do.
ENV HF_HOME=/data/voices/hf-cache

EXPOSE 8100
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
