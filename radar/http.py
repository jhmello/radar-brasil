"""Cliente HTTP com tentativas e espera progressiva (APIs públicas oscilam)."""
import time

import requests

UA = "radar-brasil/1.0 (projeto pessoal de acompanhamento de dados publicos)"


def get(url, params=None, tentativas=3, timeout=40, headers=None):
    h = {"User-Agent": UA, "Accept": "application/json, application/xml, */*"}
    h.update(headers or {})
    erro = None
    for i in range(tentativas):
        try:
            r = requests.get(url, params=params, headers=h, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            erro = e
            if i < tentativas - 1:
                time.sleep(2 * (i + 1) ** 2)
    raise erro
