"""Entry point for the Multi-Agent Research Platform.

Usage:
    python run.py              - Start the FastAPI backend (default)
    python run.py --api        - Start the FastAPI backend
    python run.py --frontend   - Start the Streamlit frontend
    python run.py --both       - Start both backend and frontend
"""

import argparse
import subprocess
import sys
import time

import uvicorn

from configs.config import settings


def run_api():
    """Start the FastAPI backend server."""
    print(f"\n🚀 Starting FastAPI backend on http://{settings.api_host}:{settings.api_port}")
    print(f"   Docs: http://localhost:{settings.api_port}/docs\n")
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )


def run_frontend():
    """Start the Streamlit frontend."""
    print("\n🎨 Starting Streamlit frontend...\n")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "frontend/streamlit_app.py",
         "--server.port", "8501"],
        cwd=".",
    )


def run_both():
    """Start both the API backend and Streamlit frontend."""
    print("\n🚀 Starting both API backend and Streamlit frontend...\n")

    # Start API in a background subprocess to avoid threading signal issues
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", 
         "--host", settings.api_host, "--port", str(settings.api_port), "--reload"],
        cwd="."
    )

    # Give API a moment to start
    time.sleep(2)

    try:
        # Start Streamlit in the foreground
        run_frontend()
    finally:
        api_process.terminate()
        api_process.wait()


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Research Platform")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--api", action="store_true", help="Start the FastAPI backend (default)")
    group.add_argument("--frontend", action="store_true", help="Start the Streamlit frontend")
    group.add_argument("--both", action="store_true", help="Start both backend and frontend")

    args = parser.parse_args()

    if args.frontend:
        run_frontend()
    elif args.both:
        run_both()
    else:
        run_api()


if __name__ == "__main__":
    main()
