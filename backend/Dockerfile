FROM python:3.11-slim
ENV APP_USER=backenduser
RUN addgroup --system $APP_USER && adduser --system --ingroup $APP_USER $APP_USER || true
RUN mkdir -p /home/$APP_USER && chown -R $APP_USER:$APP_USER /home/$APP_USER || true
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN apt-get update && apt-get install -y gcc libpq-dev     && pip install --no-cache-dir -r /app/requirements.txt
COPY backend /app/backend
ENV PYTHONPATH=/app/backend:/app
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
USER $APP_USER
