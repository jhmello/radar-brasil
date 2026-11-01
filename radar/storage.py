"""Leitura e escrita dos dados versionados no próprio repositório."""
import json
from datetime import date, timedelta
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
RELATORIOS = RAIZ / "relatorios"
CONFIG = RAIZ / "config"
PROMPTS = RAIZ / "prompts"


def ler_yaml(nome):
    return yaml.safe_load((CONFIG / nome).read_text(encoding="utf-8"))


def ler_json(caminho, padrao=None):
    p = Path(caminho)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else padrao


def gravar_json(caminho, obj):
    p = Path(caminho)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def mesclar_serie(caminho, novos):
    """Une histórico salvo com a coleta nova (a coleta nova prevalece em datas repetidas)."""
    atual = {p["data"]: p for p in ler_json(caminho, [])}
    atual.update({p["data"]: p for p in novos})
    gravar_json(caminho, sorted(atual.values(), key=lambda p: p["data"]))


def noticias_recentes(dias=7):
    vistos, itens = set(), []
    for i in range(dias):
        d = date.today() - timedelta(days=i)
        for n in ler_json(DATA / "noticias" / f"{d.isoformat()}.json", []):
            if n["link"] not in vistos:
                vistos.add(n["link"])
                itens.append(n)
    return sorted(itens, key=lambda n: n["publicado"], reverse=True)
