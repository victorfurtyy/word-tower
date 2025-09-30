# Dockerfile for Word Tower backend (ASGI Socket.IO)
# Use official Python slim image
FROM python:3.11-slim

# Create app directory
WORKDIR /app

# Install OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app
COPY app /app/app

# Expose port
EXPOSE 8000

# Default environment variables (can be overridden)
ENV HOST=0.0.0.0
ENV PORT=8000
ENV UVICORN_RELOAD=False
ENV SOCKET_CORS_ORIGINS="*"

# Run the app with uvicorn
CMD ["python", "-m", "app.main"]
