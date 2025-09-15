FROM python:3.11-slim
ENV APP_USER=workeruser
RUN addgroup --system $APP_USER && adduser --system --ingroup $APP_USER $APP_USER --home /home/$APP_USER
RUN mkdir -p /home/$APP_USER && chown -R $APP_USER:$APP_USER /home/$APP_USER
WORKDIR /app
COPY workers/requirements.txt /app/requirements.txt
RUN apt-get update && apt-get install -y wget gnupg ca-certificates \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libxss1 libgtk-3-0 libasound2 libgbm1 \
    fonts-liberation libpangocairo-1.0-0 libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 \
    libxrandr2 libxfixes3 libxrender1 libffi-dev curl build-essential \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && playwright install-deps chromium

COPY workers /app/workers
ENV PYTHONPATH=/app/workers:/app
WORKDIR /app/workers

# create worker-data directory for artifacts
RUN mkdir -p /tmp/worker-data && chmod 0777 /tmp/worker-data
ENV PROXY_LIST=
ENV PROXY_FILE=/app/proxies.txt

# Switch to user and install playwright browsers as that user
USER $APP_USER
ENV HOME=/home/$APP_USER
RUN playwright install chromium

CMD ["celery", "-A", "workers.celery_app.celery_app", "worker", "--loglevel=info", "-Q", "workers"]
