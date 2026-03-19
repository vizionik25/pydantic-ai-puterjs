"""
This is the main entry point for the Pydantic AI Litellm PuterJS Proof-of-Work Package.
"""
from .main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9999)