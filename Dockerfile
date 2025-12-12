FROM python:3.12-slim

# Work directory inside container
WORKDIR /app

# Install system dependencies (cryptography, openssl, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only required files first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire application
COPY . .

# Default environment — override in docker-compose
ENV PYTHONPATH=/app

# Expose FastAPI port
EXPOSE 8001

# Run uvicorn server
CMD ["uvicorn", "gateway.app:app", "--host", "0.0.0.0", "--port", "8001"]
