from conftest import QL_URL, ORION_URL, clean_mongo, clean_crate
import requests
from reporter.timex import TIME_INDEX_HEADER_NAME
subscribe_url = "{}/subscribe".format(QL_URL)


def test_invalid_wrong_orion_url(clean_mongo, clean_crate):
    params = {
        'orionUrl': "blabla",
        'quantumleapUrl': "quantumleap",
    }
    r = requests.post(subscribe_url, params=params)
    assert r.status_code == 400
    assert r.json() == {
        "error": "Bad Request",
        "description": "Orion is not reachable at blabla"
    }


def test_valid_defaults(clean_mongo, clean_crate):
    params = {
        'orionUrl': ORION_URL,
        'quantumleapUrl': QL_URL,
    }
    r = requests.post(subscribe_url, params=params)
    assert r.status_code == 201

    # Check created subscription
    r = requests.get("{}/subscriptions".format(ORION_URL))
    assert r.ok
    res = r.json()
    assert len(res) == 1
    subscription = res[0]

    assert subscription['description'] == 'Created by QuantumLeap {}.' \
                                          ''.format(QL_URL)
    assert subscription['subject'] == {
        'entities': [{'idPattern': '.*'}],
        'condition': {'attrs': []}
    }
    assert subscription['notification'] == {
        'attrs': [],
        'attrsFormat': 'normalized',
        'http': {'url': "{}/notify".format(QL_URL)},
        'metadata': ['dateCreated', 'dateModified', 'TimeInstant', 'timestamp']
    }
    assert subscription['throttling'] == 1


def test_valid_customs(clean_mongo, clean_crate):
    headers = {
        'Fiware-Service': 'custom',
        'Fiware-ServicePath': '/custom',
    }
    params = {
        'orionUrl': ORION_URL,
        'quantumleapUrl': QL_URL,
        'entityType': "Room",
        'idPattern': "Room1",
        'observedAttributes': "temperature,pressure",
        'notifiedAttributes': "pressure",
        'throttling': 30
    }
    r = requests.post(subscribe_url, params=params, headers=headers)
    assert r.status_code == 201

    # Check created subscription
    r = requests.get("{}/subscriptions".format(ORION_URL), headers=headers)
    assert r.ok
    res = r.json()
    assert len(res) == 1
    subscription = res[0]

    description = 'Created by QuantumLeap {}.'.format(QL_URL)
    assert subscription['description'] == description
    assert subscription['subject'] == {
        'entities': [{'idPattern': 'Room1', 'type': 'Room'}],
        'condition': {'attrs': ["temperature", "pressure"]}
    }
    assert subscription['notification'] == {
        'attrs': ["pressure"],
        'attrsFormat': 'normalized',
        'http': {'url': "{}/notify".format(QL_URL)},
        'metadata': ['dateCreated', 'dateModified', 'TimeInstant', 'timestamp']
    }
    assert subscription['throttling'] == 30


def test_use_multitenancy_headers(clean_mongo, clean_crate):
    headers = {
        'Fiware-Service': 'used',
        'Fiware-ServicePath': '/custom/from/headers',
    }
    params = {
        'orionUrl': ORION_URL,
        'quantumleapUrl': QL_URL,
        'entityType': "Room",
        'idPattern': "Room1",
        'observedAttributes': "temperature,pressure",
    }
    # Post with FIWARE headers
    r = requests.post(subscribe_url, params=params, headers=headers)
    assert r.status_code == 201

    # Check created subscription using headers via http headers
    headers = {
        'fiware-service': "used",
        'fiware-servicepath': "/custom/from/headers",
    }
    r = requests.get("{}/subscriptions".format(ORION_URL), headers=headers)
    assert r.ok
    res = r.json()
    assert len(res) == 1

    # No headers no results
    r = requests.get("{}/subscriptions".format(ORION_URL), headers={})
    assert r.ok
    res = r.json()
    assert len(res) == 0


def test_custom_time_index(clean_mongo, clean_crate):
    params = {
        'orionUrl': ORION_URL,
        'quantumleapUrl': QL_URL,
        'entityType': 'Room',
        'idPattern': 'Room1',
        'observedAttributes': 'temperature,pressure',
        'notifiedAttributes': 'pressure',
        'timeIndexAttribute': 'my-time-index'
    }
    r = requests.post(subscribe_url, params=params)
    assert r.status_code == 201

    # Check created subscription
    r = requests.get("{}/subscriptions".format(ORION_URL))
    assert r.ok
    res = r.json()
    assert len(res) == 1
    subscription = res[0]

    description = 'Created by QuantumLeap {}.'.format(QL_URL)
    assert subscription['description'] == description
    assert subscription['subject'] == {
        'entities': [{'idPattern': 'Room1', 'type': 'Room'}],
        'condition': {'attrs': ['temperature', 'pressure']}
    }
    assert subscription['notification'] == {
        'attrs': ['pressure'],
        'attrsFormat': 'normalized',
        'httpCustom': {
            'url': "{}/notify".format(QL_URL),
            'headers': {
                TIME_INDEX_HEADER_NAME: 'my-time-index'
            }
        },
        'metadata': ['dateCreated', 'dateModified', 'TimeInstant', 'timestamp', 'my-time-index']
    }
