"""Testes offline: parsing das APIs, cálculos e geração do relatório/site em modo de teste."""
from radar.analysis.indicadores import fmt, resumo_serie
from radar.collectors.bcb import parse_sgs, resumir_focus
from radar.collectors.noticias import parse_feed

RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Copom mant&#233;m juros</title><link>https://ex.com/a</link>
<description>&lt;p&gt;Decis&#227;o un&#226;nime.&lt;/p&gt;</description>
<pubDate>Mon, 26 Oct 2026 10:00:00 GMT</pubDate></item></channel></rss>"""


def test_parse_sgs():
    pts = parse_sgs([{"data": "02/01/2026", "valor": "15.00"}, {"data": "01/01/2026", "valor": "x"}])
    assert pts == [{"data": "2026-01-02", "valor": 15.0}]


def test_resumo_serie():
    pts = [{"data": f"2025-{m:02d}-01", "valor": float(m)} for m in range(1, 13)]
    pts += [{"data": "2026-01-01", "valor": 20.0}]
    r = resumo_serie(pts)
    assert r["valor"] == 20.0 and r["ha_1_mes"]["valor"] == 12.0 and r["ha_1_ano"]["valor"] == 1.0


def test_focus():
    linhas = [
        {"Data": "2026-10-23", "DataReferencia": "2026", "Mediana": 4.5, "Minimo": 4.0, "Maximo": 5.1},
        {"Data": "2026-09-20", "DataReferencia": "2026", "Mediana": 4.8, "Minimo": 4.1, "Maximo": 5.3},
    ]
    r = resumir_focus(linhas, [2026, 2027])
    assert r["2026"]["atual"]["mediana"] == 4.5
    assert r["2026"]["quatro_semanas_antes"]["mediana"] == 4.8
    assert "2027" not in r


def test_rss():
    itens = parse_feed(RSS, {"nome": "Teste", "perfil": "p", "tema": "economia"})
    assert itens[0]["titulo"] == "Copom mantém juros"
    assert itens[0]["resumo"] == "Decisão unânime."


def test_fmt():
    assert fmt(1234.5) == "1.234,50" and fmt(None) == "—"
