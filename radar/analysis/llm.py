"""Chamada ao LLM por API compatível com OpenAI.

Padrão: GitHub Models, autenticado pelo GITHUB_TOKEN do próprio Actions (sem chave extra).
Para trocar de provedor, defina LLM_PROVIDER=openai-compatible, LLM_BASE_URL e LLM_API_KEY.
"""
import os
import time

import requests

GITHUB_MODELS = "https://models.github.ai/inference/chat/completions"
RESERVA = "openai/gpt-4.1-mini"


class LLMIndisponivel(Exception):
    pass


def _chamar(url, headers, corpo, tentativas=4):
    ultimo = ""
    for i in range(tentativas):
        r = requests.post(url, json=corpo, headers=headers, timeout=180)
        tipo = r.headers.get("Content-Type", "")
        ultimo = f"HTTP {r.status_code} ({tipo}): {r.text[:300]!r}"
        if r.status_code == 200:
            try:
                return r.json()["choices"][0]["message"]["content"].strip()
            except (ValueError, KeyError, IndexError, TypeError):
                print(f"Resposta inesperada do modelo, tentativa {i + 1}: {ultimo}")
        elif r.status_code not in (429, 500, 502, 503, 504):
            raise LLMIndisponivel(ultimo)
        else:
            print(f"Modelo ocupado, tentativa {i + 1}: {ultimo}")
        if i < tentativas - 1:
            time.sleep(min(int(r.headers.get("Retry-After", 15 * (i + 1))), 120))
    raise LLMIndisponivel(ultimo)


def completar(sistema, usuario, max_tokens=1800):
    if os.getenv("LLM_DRY_RUN"):
        return "_(modo de teste: análise não gerada)_"

    if os.getenv("LLM_PROVIDER", "github") == "github":
        url, chave = GITHUB_MODELS, os.getenv("GITHUB_TOKEN")
        extra = {"X-GitHub-Api-Version": "2022-11-28"}
    else:
        url = os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions"
        chave, extra = os.getenv("LLM_API_KEY"), {}
    if not chave:
        raise LLMIndisponivel("token/chave do LLM não definido")

    headers = {"Authorization": f"Bearer {chave}", "Content-Type": "application/json",
               "Accept": "application/json", **extra}
    modelos = [os.getenv("LLM_MODEL", "openai/gpt-4.1")]
    if RESERVA not in modelos:
        modelos.append(RESERVA)

    erros = []
    for modelo in modelos:
        corpo = {
            "model": modelo,
            "messages": [{"role": "system", "content": sistema},
                         {"role": "user", "content": usuario}],
            "temperature": 0.3,
            "max_tokens": max_tokens,
        }
        try:
            texto = _chamar(url, headers, corpo)
            print(f"Análise gerada com {modelo}")
            return texto
        except LLMIndisponivel as e:
            print(f"Falha com {modelo}: {e}")
            erros.append(f"{modelo}: {e}")
    raise LLMIndisponivel(" | ".join(erros))
