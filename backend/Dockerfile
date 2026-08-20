FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc ffmpeg && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# download_dir is explicit and points at one of NLTK's own default *global*
# search paths (not a per-user one) -- this step runs as root, before the
# `app` user below even exists, but the app user's $HOME resolves to the
# unwritable /nonexistent (--no-create-home), so NLTK's default
# ~/nltk_data-relative download location would be invisible to it at
# runtime regardless of which user ran the download. Same class of bug as
# tts_service/'s $HOME fixes, different resolution since this data only
# needs to be *findable*, not written to at runtime.
# nltk.download() alone leaves e.g. corpora/wordnet.zip sitting unextracted;
# nltk.data.find('corpora/wordnet') can see the zip exists but can't resolve
# a path inside it, so it still raises. Extracting explicitly to a real
# corpora/wordnet/ directory sidesteps NLTK's zip-transparency entirely.
RUN python -c "\
import nltk, zipfile, os; \
target = '/usr/local/share/nltk_data'; \
nltk.download('wordnet', download_dir=target); \
nltk.download('omw-1.4', download_dir=target); \
corpora = os.path.join(target, 'corpora'); \
[zipfile.ZipFile(os.path.join(corpora, f'{name}.zip')).extractall(corpora) for name in ('wordnet', 'omw-1.4')]"
COPY . .
RUN addgroup --system --gid 1000 app && \
    adduser --system --uid 1000 --ingroup app --no-create-home app && \
    chown -R app:app /app && \
    mkdir -p /var/lib/celerybeat /data/piper-voices /data/podcast-audio && \
    chown app:app /var/lib/celerybeat /data/piper-voices /data/podcast-audio
USER app
