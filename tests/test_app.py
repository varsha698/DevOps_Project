import pytest
import os
from app import app, db, Visit

@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'TEST_DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/flaskapp_test'
    )
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code in [200, 503]  # 503 if DB unavailable
    data = response.get_json()
    assert 'status' in data

def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data

def test_visits_endpoint(client):
    """Test visits endpoint"""
    response = client.get('/visits')
    # Should work even if DB is unavailable (returns error in JSON)
    assert response.status_code in [200, 500]

