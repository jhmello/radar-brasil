"""Coleta diária: indicadores, Focus e notícias. Falhas parciais não derrubam a coleta."""
import sys
from datetime import date, datetime, timezone

from radar.collectors import bcb, noticias
from radar.storage import DATA, gravar_json, ler_json, ler_yaml, mesclar_serie


def main():
    status = {"executado_em": datetime.now(timezone.utc).isoformat(), "fontes": {}}

    def registrar(chave, ok, detalhe=""):
        status["fontes"][chave] = {"ok": ok, "detalhe": str(detalhe)[:300]}
        print(("OK   " if ok else "ERRO ") + chave + (f" — {detalhe}" if detalhe else ""))

    cfg = ler_yaml("indicadores.yml")
    for s in cfg["series"]:
        try:
            pontos = bcb.serie_sgs(s["codigo"], s.get("historico_dias", 400))
            mesclar_serie(DATA / "indicadores" / f"{s['id']}.json", pontos)
            registrar(f"sgs:{s['id']}", True, f"{len(pontos)} pontos")
        except Exception as e:
            registrar(f"sgs:{s['id']}", False, e)

    try:
        f = bcb.focus(cfg["focus"]["indicadores"], cfg["focus"].get("anos_a_frente", 2))
        gravar_json(DATA / "focus.json", f)
        registrar("focus", True)
    except Exception as e:
        registrar("focus", False, e)

    arq = DATA / "noticias" / f"{date.today().isoformat()}.json"
    do_dia = {n["link"]: n for n in ler_json(arq, [])}
    for feed in ler_yaml("fontes.yml")["feeds"]:
        try:
            itens = noticias.coletar_feed(feed)
            for n in itens:
                do_dia.setdefault(n["link"], n)
            registrar(f"rss:{feed['nome']}", True, f"{len(itens)} itens")
        except Exception as e:
            registrar(f"rss:{feed['nome']}", False, e)
    gravar_json(arq, sorted(do_dia.values(), key=lambda n: n["publicado"], reverse=True))

    gravar_json(DATA / "status.json", status)
    if not any(v["ok"] for v in status["fontes"].values()):
        sys.exit("Nenhuma fonte respondeu.")


if __name__ == "__main__":
    main()
