import requests

URL = 'http://localhost:5000'


def get(path):
    print(path)
    response = requests.get(URL + path)
    if len(response.text) > len('\n'):
        print(f'Status {response.status_code}, {response.json()}')
    else:
        print(f'Status {response.status_code}')


def post(path, data):
    print(f'{path}, {data}')
    response = requests.post(URL + path, json=data)
    print(f'Status {response.status_code}, {response.json()}')


# testing rest interface exposed by application.py
get('/board/reset')
get('/board/dimensions')
get('/board/terrain')
get('/status')
get('/victory')

post('/actions', {"hex": 202})
post('/positions', {"hexes": [{"Start": 202, "End": 402}]})
get('/turn/acted')
post('/turn', {"side": "Red"})
