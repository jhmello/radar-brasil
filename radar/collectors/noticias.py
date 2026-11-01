"""Coleta de manchetes via RSS. Guarda título, fonte, perfil e link, nunca o texto completo."""
import html
import re
from datetime import datetime, timezone

import feedparser

from radar.http import get

_TAG = re.compile(r"<[^>]+>")


def limpar(texto, limite=280):
    t = html.unescape(_TAG.sub(" ", texto or ""))
    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) <= limite else t[:limite].rsplit(" ", 1)[0] + "…"


def _data(entry):
    for campo in ("published_parsed", "updated_parsed"):
        st = entry.get(campo)
        if st:
            return datetime(*st[:6], tzinfo=timezone.utc).isoformat()
    return datetime.now(timezone.utc).isoformat()


def parse_feed(conteudo, feed_cfg):
    parsed = feedparser.parse(conteudo)
    itens = []
    for e in parsed.entries[:40]:
        link = e.get("link")
        titulo = limpar(e.get("title"), 200)
        if not link or not titulo:
            continue
        itens.append({
            "titulo": titulo,
            "resumo": limpar(e.get("summary")),
            "link": link,
            "fonte": feed_cfg["nome"],
            "perfil": feed_cfg.get("perfil", ""),
            "tema": feed_cfg.get("tema", "brasil"),
            "publicado": _data(e),
        })
    return itens


def coletar_feed(feed_cfg):
    r = get(feed_cfg["url"], timeout=25, headers={"Accept": "application/rss+xml, application/xml, */*"})
    itens = parse_feed(r.content, feed_cfg)
    if not itens:
        raise ValueError("feed sem itens (URL pode ter mudado)")
    return itens
