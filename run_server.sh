#!/bin/bash

# Start the FastAPI development server
cd "$(dirname "$0")"

echo "Starting Erie Otters API on http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "ReDoc: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop"
echo ""

/usr/local/bin/python3 -m uvicorn main:app --reload --host localhost --port 8000 --log-level info
