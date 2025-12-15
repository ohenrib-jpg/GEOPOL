# Flask/sdr_rate_limit.py
from flask import request, jsonify
from functools import wraps
import time

class RateLimiter:
    def __init__(self, max_requests=60, window_seconds=60):
        self.requests = {}
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def is_rate_limited(self, client_ip):
        now = time.time()
        
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Nettoyer les anciennes requêtes
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window_seconds
        ]
        
        # Vérifier la limite
        if len(self.requests[client_ip]) >= self.max_requests:
            return True
        
        # Ajouter la nouvelle requête
        self.requests[client_ip].append(now)
        return False

def rate_limit_sdr(max_requests=10, window_seconds=60):
    """Decorator pour limiter les appels SDR"""
    limiter = RateLimiter(max_requests, window_seconds)
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            
            if limiter.is_rate_limited(client_ip):
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'retry_after': window_seconds
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator