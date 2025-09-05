# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create instance directory (legacy - now using Firebase)
RUN mkdir -p instance

# Set Firebase environment for production
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/firebase-service-account.json

# Make start script executable
RUN chmod +x start.sh

# Create non-root user
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check (use startup endpoint first, then health)
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/startup || curl -f http://localhost:8080/health || exit 1

# Run the application with startup script
CMD ["./start.sh"]