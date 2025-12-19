# tests/test_basic.py
import pytest
from Flask.app_factory import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_endpoint(client):
    """Test du endpoint de santé"""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'ok'

def test_indicateurs_endpoint(client):
    """Test des indicateurs économiques"""
    response = client.get('/indicateurs/api/indicators')
    assert response.status_code == 200
    assert 'indicators' in response.json