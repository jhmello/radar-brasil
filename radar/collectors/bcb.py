"""Banco Central: séries do SGS e expectativas do Boletim Focus (API Olinda)."""
from datetime import date, datetime, timedelta
from urllib.parse import quote

from radar.http import get

SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
FOCUS = ("https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/"
         "odata/ExpectativasMercadoAnuais")


def parse_sgs(payload):
    pontos = []
    for p in payload:
        try:
            d, m, a = p["data"].split("/")
            pontos.append({"data": f"{a}-{m}-{d}", "valor": float(p["valor"])})
        except (KeyError, ValueError):
            continue
    return sorted(pontos, key=lambda p: p["data"])


def serie_sgs(codigo, dias):
    # O SGS exige janela de datas para séries diárias (máx. 10 anos por consulta).
    fim = date.today()
    ini = fim - timedelta(days=min(dias, 3650))
    r = get(SGS.format(codigo=codigo), params={
        "formato": "json",
        "dataInicial": ini.strftime("%d/%m/%Y"),
        "dataFinal": fim.strftime("%d/%m/%Y"),
    })
    return parse_sgs(r.json())


def _odata_url(indicador):
    filtro = f"Indicador eq '{indicador}' and baseCalculo eq 0"
    campos = "Indicador,Data,DataReferencia,Mediana,Minimo,Maximo,numeroRespondentes"
    return (f"{FOCUS}?$filter={quote(filtro, safe='')}&$orderby=Data%20desc"
            f"&$top=400&$select={campos}&$format=json")


def resumir_focus(linhas, anos):
    """Para cada ano: projeção mais recente e a de ~4 semanas antes (para ver a tendência)."""
    out = {}
    for ano in anos:
        do_ano = sorted((l for l in linhas if str(l.get("DataReferencia")) == str(ano)),
                        key=lambda l: l["Data"], reverse=True)
        if not do_ano:
            continue
        atual = do_ano[0]
        limite = datetime.fromisoformat(atual["Data"]) - timedelta(days=28)
        antes = next((l for l in do_ano if datetime.fromisoformat(l["Data"]) <= limite), None)

        def pick(l):
            return None if l is None else {
                "data": l["Data"], "mediana": l.get("Mediana"),
                "minimo": l.get("Minimo"), "maximo": l.get("Maximo"),
                "respondentes": l.get("numeroRespondentes"),
            }
        out[str(ano)] = {"atual": pick(atual), "quatro_semanas_antes": pick(antes)}
    return out


def focus(indicadores, anos_a_frente=2):
    hoje = date.today().year
    anos = [hoje + i for i in range(anos_a_frente)]
    resultado = {}
    for ind in indicadores:
        linhas = get(_odata_url(ind)).json().get("value", [])
        resultado[ind] = resumir_focus(linhas, anos)
    return resultado
