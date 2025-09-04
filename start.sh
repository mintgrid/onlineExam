#!/bin/bash
# Startup script for Cloud Run deployment

echo "Starting Online Exam Application..."
echo "Environment: ${ENVIRONMENT:-development}"
echo "Port: ${PORT:-8080}"

# Create instance directory if it doesn't exist
mkdir -p instance

# Start the application
if [ "${ENVIRONMENT}" = "production" ]; then
    echo "Starting with Gunicorn for production..."
    exec gunicorn --bind :${PORT:-8080} --workers 2 --threads 8 --timeout 0 app:app
else
    echo "Starting Flask development server..."
    exec python app.py
fi