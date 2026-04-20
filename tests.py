import pytest
from unittest.mock import patch
from app import create_app
from models import db


@pytest.fixture
def client():
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def make_item(client, name='Test Item', price=5.00, quantity=10):
    return client.post('/items', json={'name': name, 'price': price, 'quantity': quantity})


# basic CRUD
def test_empty_inventory(client):
    res = client.get('/items')
    assert res.status_code == 200
    assert res.json['total'] == 0


def test_create_item(client):
    res = make_item(client, name='Milk', price=2.99)
    assert res.status_code == 201
    assert res.json['name'] == 'Milk'


def test_create_requires_name(client):
    res = client.post('/items', json={'price': 1.99})
    assert res.status_code == 400


def test_create_requires_price(client):
    res = client.post('/items', json={'name': 'Bread'})
    assert res.status_code == 400


def test_get_item(client):
    make_item(client)
    res = client.get('/items/1')
    assert res.status_code == 200


def test_get_item_missing(client):
    assert client.get('/items/999').status_code == 404


def test_update_item(client):
    make_item(client)
    res = client.patch('/items/1', json={'quantity': 99})
    assert res.status_code == 200
    assert res.json['quantity'] == 99


def test_update_missing_item(client):
    assert client.patch('/items/999', json={'quantity': 1}).status_code == 404


def test_delete_item(client):
    make_item(client)
    res = client.delete('/items/1')
    assert res.status_code == 200
    assert 'deleted' in res.json['message']


def test_delete_missing_item(client):
    assert client.delete('/items/999').status_code == 404


# search and pagination
def test_search(client):
    make_item(client, name='Apple Juice')
    make_item(client, name='Orange Juice')
    make_item(client, name='Milk')
    res = client.get('/items?search=Juice')
    assert res.json['total'] == 2


def test_pagination(client):
    for i in range(12):
        make_item(client, name=f'Item {i}')
    res = client.get('/items?page=1&per_page=10')
    assert len(res.json['items']) == 10
    assert res.json['pages'] == 2


# external API (mocked so tests don't hit the real API)
mock_product = {
    'name': 'Mock Chips',
    'description': 'Crunchy chips',
    'category': 'Snacks',
    'image_url': None
}

def test_fetch_by_barcode(client):
    with patch('routes.get_product_by_barcode', return_value=mock_product):
        res = client.get('/fetch/barcode/123')
        assert res.status_code == 200
        assert res.json['name'] == 'Mock Chips'


def test_fetch_barcode_not_found(client):
    with patch('routes.get_product_by_barcode', return_value=None):
        assert client.get('/fetch/barcode/000').status_code == 404


def test_fetch_and_add(client):
    with patch('routes.get_product_by_barcode', return_value=mock_product):
        res = client.post('/fetch/add/123', json={'price': 2.99, 'quantity': 5})
        assert res.status_code == 201
        assert res.json['name'] == 'Mock Chips'


def test_fetch_and_add_duplicate(client):
    with patch('routes.get_product_by_barcode', return_value=mock_product):
        client.post('/fetch/add/123', json={'price': 2.99, 'quantity': 5})
        res = client.post('/fetch/add/123', json={'price': 2.99, 'quantity': 5})
        assert res.status_code == 409