#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "========================================"
echo "Wood Batch Template Generator"
echo "========================================"
echo ""

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 was not found."
  echo ""
  echo "Please install Python first:"
  echo "  macOS: install from https://www.python.org/downloads/macos/"
  echo "  or, if using Homebrew: brew install python"
  echo ""
  echo "After installing Python, re-open Terminal and run ./run.sh again."
  echo ""
  exit 1
fi

if [ ! -f "requirements.txt" ]; then
  echo "requirements.txt was not found in this folder."
  echo "Expected file: $(pwd)/requirements.txt"
  echo ""
  exit 1
fi

if [ ! -f "template.py" ]; then
  echo "template.py was not found in this folder."
  echo "Expected file: $(pwd)/template.py"
  echo ""
  exit 1
fi

mkdir -p output

if [ ! -d ".venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv
fi

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing/updating Python dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo ""
echo "Running template generator..."
python template.py

echo ""
echo "Done. Check the output/ folder."
echo ""