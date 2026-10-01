FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends gosu tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
COPY entrypoint.sh /usr/local/bin/collector-entrypoint
RUN chmod 755 /usr/local/bin/collector-entrypoint
RUN mkdir -p /logs

ENTRYPOINT ["/usr/local/bin/collector-entrypoint"]
CMD ["main.py"]
