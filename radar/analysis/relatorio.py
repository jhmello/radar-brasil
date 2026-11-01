"""Gera o relatório semanal em Markdown.

O painel de números é montado em código (determinístico). O LLM só escreve a interpretação,
em chamadas separadas por seção para caber nos limites do plano gratuito do GitHub Models.
"""
from collections import Counter
from datetime import date

from radar.analysis import indicadores as ind
from radar.analysis.llm import LLMIndisponivel, completar
from radar.storage import DATA, PROMPTS, RELATORIOS, ler_json, noticias_recentes

AVISO = ("> Boletim gerado automaticamente a partir de dados oficiais e de manchetes de veículos "
         "de linhas editoriais diferentes. A interpretação é feita por IA e pode conter erros: "
         "confira sempre os números no painel e os links das fontes.")


def painel_markdown(series):
    linhas = ["| Indicador | Último | Data | 1 mês antes | 1 ano antes | Fonte |",
              "|---|---|---|---|---|---|"]
    for s in series:
        r = s["resumo"]
        if not r:
            linhas.append(f"| {s['nome']} | sem dados | — | — | — | {s['fonte']} |")
            continue
        casas = 4 if s["id"] == "dolar_ptax" else 2
        v = lambda p: ind.fmt(p["valor"], casas) if p else "—"
        linhas.append(f"| {s['nome']} ({s['unidade']}) | **{ind.fmt(r['valor'], casas)}** | "
                      f"{ind.fmt_data(r['data'])} | {v(r['ha_1_mes'])} | {v(r['ha_1_ano'])} | {s['fonte']} |")
    return "\n".join(linhas)


def focus_markdown(focus):
    if not focus:
        return "_Boletim Focus indisponível nesta edição._"
    linhas = ["| Indicador | Ano | Mediana atual | Faixa (mín–máx) | Há 4 semanas |",
              "|---|---|---|---|---|"]
    for nome, anos in focus.items():
        for ano, d in anos.items():
            a, b = d["atual"], d.get("quatro_semanas_antes")
            linhas.append(f"| {nome} | {ano} | **{ind.fmt(a['mediana'])}** | "
                          f"{ind.fmt(a['minimo'])} – {ind.fmt(a['maximo'])} | "
                          f"{ind.fmt(b['mediana']) if b else '—'} |")
    data_ref = next((d["atual"]["data"] for anos in focus.values() for d in anos.values()), None)
    return "\n".join(linhas) + f"\n\n_Focus de {ind.fmt_data(data_ref)}._"


def _manchetes(itens, limite):
    # Distribui o limite entre veículos para nenhum dominar a amostra.
    por_fonte, sel = Counter(), []
    teto = max(4, limite // max(1, len({n["fonte"] for n in itens})) + 2)
    for n in itens:
        if por_fonte[n["fonte"]] < teto:
            por_fonte[n["fonte"]] += 1
            sel.append(n)
        if len(sel) >= limite:
            break
    texto = "\n".join(
        f"- [{n['fonte']} | {n['perfil']}] {n['titulo']}"
        + (f" — {n['resumo'][:140]}" if n["resumo"] else "")
        for n in sel)
    return texto, sel


def _secao(prompt, dados, sistema):
    try:
        return completar(sistema, (PROMPTS / prompt).read_text(encoding="utf-8").format(dados=dados))
    except LLMIndisponivel as e:
        print(f"Seção {prompt} sem análise: {e}")
        return "_Análise indisponível nesta edição (falha no modelo de linguagem). Os dados acima seguem válidos._"


def gerar(hoje=None):
    hoje = hoje or date.today()
    sistema = (PROMPTS / "metodo.md").read_text(encoding="utf-8")
    series = ind.todos()
    focus = ler_json(DATA / "focus.json", {})
    painel, tab_focus = painel_markdown(series), focus_markdown(focus)

    noticias = noticias_recentes(7)
    nacionais = [n for n in noticias if n["tema"] in ("brasil", "economia")]
    mundo = [n for n in noticias if n["tema"] == "mundo"]
    txt_nac, sel_nac = _manchetes(nacionais, 55)
    txt_mundo, sel_mundo = _manchetes(mundo, 35)

    economia = _secao("economia.md", painel + "\n\nBOLETIM FOCUS:\n" + tab_focus, sistema)
    governo = _secao("governo.md", txt_nac or "(sem manchetes coletadas)", sistema)
    geo = _secao("geopolitica.md", txt_mundo or "(sem manchetes coletadas)", sistema)

    fontes = "\n".join(f"- [{n['titulo']}]({n['link']}) — {n['fonte']}" for n in sel_nac + sel_mundo)
    md = f"""# Radar Brasil — semana de {hoje.strftime('%d/%m/%Y')}

{AVISO}

## Painel de indicadores

{painel}

### Expectativas do mercado (Boletim Focus)

{tab_focus}

## Economia

{economia}

## Governo e decisões

{governo}

## Geopolítica

{geo}

## Fontes desta edição

<details><summary>{len(sel_nac) + len(sel_mundo)} manchetes analisadas</summary>

{fontes}

</details>
"""
    RELATORIOS.mkdir(exist_ok=True)
    caminho = RELATORIOS / f"{hoje.isoformat()}.md"
    caminho.write_text(md, encoding="utf-8")
    print(f"Relatório salvo em {caminho}")
    return caminho


if __name__ == "__main__":
    gerar()
