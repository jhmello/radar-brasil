"""Gera o site estático em _site/ a partir de data/ e relatorios/."""
import json
import shutil
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader

from radar.analysis import indicadores as ind
from radar.analysis.relatorio import focus_markdown
from radar.storage import DATA, RAIZ, RELATORIOS, ler_json

WEB = Path(__file__).resolve().parent
SAIDA = RAIZ / "_site"


def md_html(texto):
    return markdown.markdown(texto, extensions=["tables", "sane_lists", "md_in_html"])


def main():
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    (SAIDA / "relatorios").mkdir(parents=True)
    shutil.copytree(WEB / "static", SAIDA / "static")

    env = Environment(loader=FileSystemLoader(WEB / "templates"), autoescape=True)
    env.filters["num"] = ind.fmt
    env.filters["data_br"] = ind.fmt_data

    series = ind.todos()
    graficos = {s["id"]: s["pontos"][-400:] for s in series if s["pontos"]}
    status = ler_json(DATA / "status.json", {})

    relatorios = []
    for arq in sorted(RELATORIOS.glob("*.md"), reverse=True):
        corpo = arq.read_text(encoding="utf-8")
        titulo = corpo.splitlines()[0].lstrip("# ").strip() if corpo else arq.stem
        relatorios.append({"slug": arq.stem, "titulo": titulo, "html": md_html(corpo)})

    comum = {"status": status, "n_relatorios": len(relatorios)}
    (SAIDA / "index.html").write_text(env.get_template("index.html").render(
        raiz=".", series=series, graficos_json=json.dumps(graficos),
        focus_html=md_html(focus_markdown(ler_json(DATA / "focus.json", {}))),
        ultimo=relatorios[0] if relatorios else None, **comum), encoding="utf-8")

    for r in relatorios:
        (SAIDA / "relatorios" / f"{r['slug']}.html").write_text(
            env.get_template("relatorio.html").render(raiz="..", r=r, **comum), encoding="utf-8")

    (SAIDA / "arquivo.html").write_text(env.get_template("arquivo.html").render(
        raiz=".", relatorios=relatorios, **comum), encoding="utf-8")
    (SAIDA / "status.html").write_text(env.get_template("status.html").render(
        raiz=".", **comum), encoding="utf-8")
    (SAIDA / ".nojekyll").write_text("")
    print(f"Site gerado em {SAIDA} ({len(relatorios)} relatórios)")


if __name__ == "__main__":
    main()
