"""
Root entrypoint for Render, Docker, and Cloud PaaS deployments.
Exposes the FastAPI `app` instance with correct path resolution.
"""
import sys
import os

# Ensure the project root directory is at the front of sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.main import app

if __name__ == "__main__":
    import uvicorn
    from backend.config import settings
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
