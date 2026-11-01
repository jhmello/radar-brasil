"""Chamada ao LLM por API compatível com OpenAI.

Padrão: GitHub Models, autenticado pelo GITHUB_TOKEN do próprio Actions (sem chave extra).
Para trocar de provedor, defina LLM_PROVIDER=openai-compatible, LLM_BASE_URL e LLM_API_KEY
(ex.: Gemini em https://generativelanguage.googleapis.com/v1beta/openai).
"""
import os
import time

import requests

GITHUB_MODELS = "https://models.github.ai/inference/chat/completions"


class LLMIndisponivel(Exception):
    pass


def completar(sistema, usuario, max_tokens=1800, tentativas=4):
    if os.getenv("LLM_DRY_RUN"):
        return "_(modo de teste: análise não gerada)_"

    if os.getenv("LLM_PROVIDER", "github") == "github":
        url, chave = GITHUB_MODELS, os.getenv("GITHUB_TOKEN")
        extra = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    else:
        url = os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions"
        chave, extra = os.getenv("LLM_API_KEY"), {}
    if not chave:
        raise LLMIndisponivel("token/chave do LLM não definido")

    corpo = {
        "model": os.getenv("LLM_MODEL", "openai/gpt-4.1"),
        "messages": [{"role": "system", "content": sistema},
                     {"role": "user", "content": usuario}],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }
    headers = {"Authorization": f"Bearer {chave}", "Content-Type": "application/json", **extra}

    for i in range(tentativas):
        r = requests.post(url, json=corpo, headers=headers, timeout=180)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        if r.status_code in (429, 500, 502, 503) and i < tentativas - 1:
            espera = int(r.headers.get("Retry-After", 20 * (i + 1)))
            print(f"LLM HTTP {r.status_code}; aguardando {espera}s")
            time.sleep(min(espera, 120))
            continue
        raise LLMIndisponivel(f"HTTP {r.status_code}: {r.text[:300]}")
