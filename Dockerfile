FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app
RUN groupadd --system oia && useradd --system --gid oia --home-dir /app oia
COPY src ./src
USER oia

EXPOSE 8080
CMD ["python", "-m", "src.http_server"]
