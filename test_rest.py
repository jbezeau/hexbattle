import requests
import restclient

URL = restclient.URL


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
get('/tokens/status')
get('/player/victory')

post('/token/actions', {"hex": 202})
post('/tokens/positions', {202: 402})
get('/tokens/acted')
post('/player/turn', {"side": "Red"})
