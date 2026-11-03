FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml requirements.lock /app/
COPY src /app/src
RUN python -m pip install --no-cache-dir -r requirements.lock . && useradd --uid 10001 --create-home pug
USER pug
EXPOSE 8080
CMD ["uvicorn", "pug_www.app:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
