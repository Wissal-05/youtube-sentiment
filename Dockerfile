FROM python:3.11-slim

WORKDIR /app
ENV PORT=7860 PYTHONUNBUFFERED=1

# Dépendances d'abord (cache des layers)
COPY requirements-prod.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Uniquement le nécessaire
COPY app_api.py .
COPY src/ ./src/
COPY models/ ./models/

EXPOSE 7860
CMD uvicorn app_api:app --host 0.0.0.0 --port ${PORT}