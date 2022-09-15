import os
from urllib.parse import urljoin

import requests

from . import consts

TOKEN = os.environ.get(consts.TOKEN_ENV)


class ApiSession(requests.Session):
    def request(self, method, url, headers=None, timeout=5, **kwargs):
        headers = {**(headers or {}), "Authorization": f"Token {TOKEN}"}

        resp = super().request(
            method, url, headers=headers, timeout=timeout, **kwargs
        )

        resp.raise_for_status()
        return resp.json()

    def get_spec(self):
        return self.get("/openapi/?format=openapi-json")


api = ApiSession()
