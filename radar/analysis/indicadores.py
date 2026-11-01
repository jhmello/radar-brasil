"""Cálculos determinísticos sobre as séries. Os números do relatório saem daqui, não do LLM."""
from datetime import date, timedelta

from radar.storage import DATA, ler_json, ler_yaml


def _valor_em_ou_antes(pontos, alvo):
    anteriores = [p for p in pontos if p["data"] <= alvo]
    return anteriores[-1] if anteriores else None


def resumo_serie(pontos):
    if not pontos:
        return None
    ult = pontos[-1]
    d = date.fromisoformat(ult["data"])
    m1 = _valor_em_ou_antes(pontos[:-1], (d - timedelta(days=28)).isoformat())
    a1 = _valor_em_ou_antes(pontos, (d - timedelta(days=365)).isoformat())
    return {
        "data": ult["data"], "valor": ult["valor"],
        "anterior": pontos[-2] if len(pontos) > 1 else None,
        "ha_1_mes": m1, "ha_1_ano": a1,
    }


def todos():
    cfg = ler_yaml("indicadores.yml")
    out = []
    for s in cfg["series"]:
        pontos = ler_json(DATA / "indicadores" / f"{s['id']}.json", [])
        out.append({**s, "resumo": resumo_serie(pontos), "pontos": pontos})
    return out


def fmt(v, casas=2):
    if v is None:
        return "—"
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_data(iso):
    if not iso:
        return "—"
    a, m, d = iso[:10].split("-")
    return f"{d}/{m}/{a}"
