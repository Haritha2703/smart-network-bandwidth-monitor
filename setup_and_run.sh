#!/bin/bash
# One-step setup + run for macOS/Linux. Usage: ./setup_and_run.sh [options]
# Example: ./setup_and_run.sh --warning 2 --critical 8
cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 was not found."
    echo "Install it from https://www.python.org/downloads/ (or run: xcode-select --install)"
    exit 1
fi
echo "Using $(python3 --version)"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment (.venv)..."
    python3 -m venv .venv || { echo "Could not create the virtual environment."; exit 1; }
fi

source .venv/bin/activate
echo "Installing dependencies..."
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt || { echo "Dependency installation failed (check internet)."; exit 1; }

echo "Starting monitor... (press CTRL+C to stop)"
python main.py "$@"
