#!/bin/bash
# Startup script for Cloud Run deployment

echo "Starting Online Exam Application..."
echo "Environment: ${ENVIRONMENT:-development}"
echo "Port: ${PORT:-8080}"

# Create instance directory if it doesn't exist
mkdir -p instance

# Start the application
if [ "${ENVIRONMENT}" = "production" ] || [ "${GAE_ENV}" = "standard" ] || [ -n "${K_SERVICE}" ]; then
    echo "Starting with Gunicorn for production..."
    # Optimized for Cloud Run with faster startup
    exec gunicorn \
        --bind :${PORT:-8080} \
        --workers 1 \
        --threads 4 \
        --timeout 120 \
        --keep-alive 2 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --preload \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        main:app
else
    echo "Starting Flask development server..."
    exec python app.py
fi