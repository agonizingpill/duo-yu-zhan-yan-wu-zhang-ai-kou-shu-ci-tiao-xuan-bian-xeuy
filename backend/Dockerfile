FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY migrations ./migrations
COPY scripts ./scripts
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
