FROM python:3.12-slim
WORKDIR /app

# Build with --build-arg TTS_GPU=true to install GPU-capable builds of the
# ML backends used here (onnxruntime for Piper, torch/torchaudio for
# Kokoro and Chatterbox) instead of their CPU-only default builds. This only
# prepares the image to be able to use a GPU -- actually engaging it also
# needs the container run with GPU access (--gpus / the compose file's
# NVIDIA deploy block) and TTS_DEVICE=cuda set at runtime; see
# docker-compose.tts.yml. All three engines' dependencies are always
# installed regardless of TTS_ENGINE, so switching engines is a plain env
# var change with no rebuild required.
ARG TTS_GPU=false

# torch/torchaudio first, from the CPU-only wheel index, pinned to exactly
# what chatterbox-tts requires (kokoro's own torch dependency is
# unconstrained, so it's happy with whatever's already installed) --
# otherwise pip would pull PyPI's default Linux build to satisfy that pin,
# which bundles CUDA runtime libs (large) even when never used.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.6.0 torchaudio==2.6.0

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$TTS_GPU" = "true" ]; then \
         pip install --no-cache-dir --force-reinstall onnxruntime-gpu; \
         pip install --no-cache-dir --force-reinstall torch==2.6.0 torchaudio==2.6.0; \
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
    mkdir -p /data/voices /data/voices/home && \
    chown -R app:app /app /data/voices
USER app

# The "app" user has no home directory (--no-create-home), which resolves
# to the nonexistent, unwritable "/nonexistent" -- and it turns out more of
# this dependency stack than expected reaches for $HOME by default: Kokoro
# and Chatterbox's model downloads via huggingface_hub cache under
# ~/.cache/huggingface, and Chatterbox's Chinese tokenizer support
# (spacy_pkuseg) downloads a segmentation model under ~/.pkuseg. Fixing
# $HOME itself covers those and whatever else in this stack makes the same
# assumption, rather than chasing each tool's own env var one at a time.
ENV HOME=/data/voices/home
# Still set explicitly for clarity and because it also means downloads
# persist in the volume across container restarts, same as Piper's models.
ENV HF_HOME=/data/voices/hf-cache

# Chatterbox also pulls in librosa/numba, and numba's JIT cache (from
# librosa's @jit(cache=True) functions) defaults to writing next to the
# installed package's .py source files -- site-packages, not $HOME, so the
# HOME fix above doesn't cover this one. Redirect it to the same writable
# volume rather than losing the cache (repaying JIT compile time on every
# container start) or disabling JIT entirely.
ENV NUMBA_CACHE_DIR=/data/voices/numba-cache

EXPOSE 8100
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
