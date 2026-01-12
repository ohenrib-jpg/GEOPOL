def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config.update({
        'REDIS_URL': 'redis://localhost:6379/0',
        'CACHE_TYPE': 'redis',
        'CACHE_DEFAULT_TIMEOUT': 300,
        'COMPRESS_MIMETYPES': ['application/json', 'text/html'],
        'COMPRESS_LEVEL': 6,
        'COMPRESS_MIN_SIZE': 500
    })
    
    # Extensions
    Compress(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialiser le cache
    from flask_caching import Cache
    cache = Cache(app)
    
    # Blueprints
    from geopol_data.modules.satellite import satellite_bp
    app.register_blueprint(satellite_bp)
    
    # Initialiser le gestionnaire satellite
    @app.before_first_request
    def init_satellite():
        from geopol_data.modules.satellite.satellite_manager import SatelliteManager
        manager = SatelliteManager()
        app.extensions['satellite_manager'] = manager
    
    return app