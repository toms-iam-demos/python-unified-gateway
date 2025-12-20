FROM python:3.12-slim

# Work directory inside container
WORKDIR /app

# System dependencies
# - sqlite3: lets us run operator-grade DB inspection via `docker exec ... sqlite3 ...`
# - ca-certificates: avoids TLS surprises for outbound HTTPS (DocuSign, etc.)
# - curl: handy for in-container smoke tests (optional but useful)
# - build-essential/libssl-dev: required for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    sqlite3 \
    ca-certificates \
    curl \
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
