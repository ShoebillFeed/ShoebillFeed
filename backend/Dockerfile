FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc ffmpeg && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
COPY . .
RUN addgroup --system --gid 1000 app && \
    adduser --system --uid 1000 --ingroup app --no-create-home app && \
    chown -R app:app /app && \
    mkdir -p /var/lib/celerybeat /data/piper-voices /data/podcast-audio && \
    chown app:app /var/lib/celerybeat /data/piper-voices /data/podcast-audio
USER app
