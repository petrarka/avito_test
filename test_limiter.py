import random as rnd
import time

import pytest

from main import app

@pytest.fixture
def client():

    with app.test_client() as client:
        yield client


def test_ban(client):
    for x in range(100):
        rv = client.get('/', headers = {'X-Forwarded-For': f'31.31.31.{rnd.randint(1, 255)}'})
        assert b"I love dogs" in rv.data
    for x in range(100):
        rv = client.get('/', headers = {'X-Forwarded-For': '31.31.31.31'})
        assert b'Too many requests' in rv.data
    for x in range(100): 
        rv = client.get('/', headers = {'X-Forwarded-For': f'32.32.32.{rnd.randint(1, 255)}'})
        assert b"I love dogs" in rv.data


def test_rs(client):
    rv = client.get('/rs', headers = {'X-Forwarded-For': '31.31.31.31'})
    rv = client.get('/rs', headers = {'X-Forwarded-For': '32.32.32.32'})
    assert b"reseted" in rv.data
    test_ban(client)


def test_unban(client):
    rv = client.get('/rs', headers = {'X-Forwarded-For': '31.31.31.31'})
    rv = client.get('/rs', headers = {'X-Forwarded-For': '32.32.32.32'})
    test_ban(client)
    time.sleep(5)
    test_ban(client)


def test_time(client): #проверка сброса лимита
    rv = client.get('/rs', headers = {'X-Forwarded-For': '31.31.31.31'})
    for x in range(100):
        rv = client.get('/', headers = {'X-Forwarded-For': f'31.31.31.{rnd.randint(1, 255)}'})
        assert b"I love dogs" in rv.data
    time.sleep(1)
    for x in range(100):
        rv = client.get('/', headers = {'X-Forwarded-For': '31.31.31.31'})
        assert b"I love dogs" in rv.data


def test_header(client):
    rv = client.get('/', headers = {'X-Forwarded-For': 'SOBAKA'})
    assert b"header error" in rv.data
    rv = client.get('/')
    assert b"header error" in rv.data