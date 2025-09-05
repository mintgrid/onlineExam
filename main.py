"""
WSGI entry point for production deployment
This file is used by Google Cloud Run and other WSGI servers
"""

from app import app

# For Cloud Run and production WSGI servers
if __name__ == "__main__":
    # This will only run in development
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)