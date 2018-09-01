import requests


class CloudianRequestor(object):
    def __init__(self, url, port, user, key, warn=False):
        self.url = url
        self.port = port
        self.user = user
        self.key = key
        self.warn = warn

    def request(self, url, data=None, json=None, method='GET'):
        print(url)
        request = dict()
        request['method'] = method

        if data is not None:
            request['data'] = data.pop('data', None)
            for index, (key, value) in enumerate(data.items()):
                url += '{symbol}{key}={value}'.format(
                    symbol='&' if index else '?', key=key, value=value
                )
        elif json is not None:
            request['json'] = json

        api_call = '{url}:{port}/{call}'.format(
            url=self.url, port=self.port, call=url
        )
        print(url)

        try:
            response = requests.request(
                verify=False,
                method=method,
                url=api_call,
                data=request['data'] if data is not None else None,
                json=request['json'] if json is not None else None,
                auth=(
                    self.user, self.key
                ),
            )

            if response.status_code == 200:
                try:
                    return {
                        'status_code': response.status_code,
                        'status_message': 'ok',
                        'data': response.json()
                    }
                except ValueError:
                    return {
                        'status_code': response.status_code,
                        'status_message': response.text,
                        'data': {}
                    }
            else:
                return {
                    'status_code': response.status_code,
                    'status_message': response.reason,
                }

        except requests.exceptions.ConnectionError as err:
            return {
                'status_code': err.errno,
                'status_message': err.message,
            }
