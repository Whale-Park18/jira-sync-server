FROM python:3.11-slim

WORKDIR /server

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && pip install --no-cache-dir git+https://github.com/Whale-Park18/jira-sync.git@344c0c076aae6faa085bcdb787eab8de00d79c94 \
    && apt-get purge -y git && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

COPY app/ ./app/

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT:-8000}"]
