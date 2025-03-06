import os
import pytest
from app import create_app
import io

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_scan_no_file(client):
    response = client.post('/api/scan')
    assert response.status_code == 400
    assert b'No image provided' in response.data

def test_scan_history(client):
    response = client.get('/api/scans')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'scans' in json_data
    assert 'total' in json_data 