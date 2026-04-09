#!/usr/bin/env python3
"""
Start the FastAPI server for Erie Otters API
"""

import sys
import uvicorn

if __name__ == "__main__":
    print("Starting Erie Otters API Server...")
    print("=" * 60)
    print("API Documentation: http://localhost:8000/docs")
    print("ReDoc: http://localhost:8000/redoc")
    print("=" * 60)
    print()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
