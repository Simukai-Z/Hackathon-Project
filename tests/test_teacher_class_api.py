import pytest
import json
from app import app

def login_teacher(client, email="teacher1@example.com"):
    with client.session_transaction() as sess:
        sess['user_type'] = 'teacher'
        sess['email'] = email

def test_create_and_join_class():
    client = app.test_client()
    login_teacher(client)

    # Create a new class
    response = client.post('/api/create_class', json={
        'class_name': 'Biology 101',
        'school': 'Test High School'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    class_code = data['classroom']['code']

    # Join the class as another teacher
    login_teacher(client, email="teacher2@example.com")
    response = client.post('/api/join_class_as_teacher', json={
        'class_code': class_code
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']

    # List classes for teacher2
    response = client.get('/api/my_classes')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert any(c['code'] == class_code for c in data['classrooms'])

    # List classes for teacher1
    login_teacher(client, email="teacher1@example.com")
    response = client.get('/api/my_classes')
    data = response.get_json()
    assert any(c['code'] == class_code for c in data['classrooms'])
