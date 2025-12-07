"""
WSGI entry point for production deployment
"""
import os
from app import app

if __name__ == "__main__":
    # This is only for local testing
    # In production, Gunicorn will import the app directly
    port = int(os.getenv('PORT', 5004))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_ENV') == 'development'
    )
