# 构建后导入 k3s：docker build -t ml-api:dev -f apps/ml-api/Dockerfile .
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask prometheus-client psutil

COPY scripts/ ./scripts/
COPY src/ ./src/

ENV PYTHONUNBUFFERED=1
EXPOSE 5000

CMD ["python", "scripts/mock_ml_service.py"]
