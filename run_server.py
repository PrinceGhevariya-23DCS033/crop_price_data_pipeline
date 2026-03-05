"""
Simple server launcher for Gujarat Crop Price Forecasting System
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("Gujarat Crop Price Forecasting API Server")
    print("=" * 70)
    print("\nStarting server...")
    print("API will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("\nOpen frontend/index.html in your browser to use the interface")
    print("\nPress CTRL+C to stop the server")
    print("=" * 70)
    print()
    
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
