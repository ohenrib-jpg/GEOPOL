# diagnostic_routes.py
from flask import Flask
import requests
import time

def test_routes(base_url="http://localhost:5000"):
    """Teste toutes les routes principales et retourne leur statut"""
    
    routes_to_test = [
        "/",
        "/dashboard", 
        "/api/themes",
        "/api/articles",
        "/api/stats",
        "/api/social/statistics",
        "/api/weak-indicators/stocks/data",
        "/api/batch/analyze-coherent"
    ]
    
    results = {}
    
    for route in routes_to_test:
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}{route}", timeout=10)
            response_time = round((time.time() - start_time) * 1000, 2)
            
            results[route] = {
                "status_code": response.status_code,
                "response_time_ms": response_time,
                "success": response.status_code == 200,
                "content_type": response.headers.get('content-type', ''),
                "error": None
            }
            
        except Exception as e:
            results[route] = {
                "status_code": "ERROR",
                "response_time_ms": 0,
                "success": False, 
                "content_type": "",
                "error": str(e)
            }
    
    return results