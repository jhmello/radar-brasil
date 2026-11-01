# Radar Brasil

Boletim pessoal sobre a situação do país, feito **dado primeiro, opinião depois**, rodando 100% no GitHub e de graça.

- **Todo dia (06:17, Brasília):** coleta indicadores oficiais (Banco Central/IBGE), o Boletim Focus e manchetes de veículos de linhas editoriais diferentes, e atualiza o painel.
- **Toda segunda (06:47):** gera o boletim semanal com análise de economia, decisões do governo e geopolítica.
- **Site:** publicado no GitHub Pages. O histórico de dados e de edições fica versionado no próprio repositório.

## Como o viés é controlado

1. Os **números do painel são calculados em código** a partir das APIs oficiais. O modelo de linguagem não gera números, só interpreta os que recebe.
2. O **método** está escrito em `prompts/metodo.md`: fato separado de interpretação, manchete tratada como alegação, sempre uma leitura otimista e uma crítica, projeções em faixas e linguagem neutra.
3. A **lista de veículos** (`config/fontes.yml`) é sua: mantenha perfis diferentes lado a lado.
4. Cada edição lista as **manchetes usadas**, com link, para você conferir.

## Instalação (uma vez, uns 5 minutos)

1. Crie um repositório **público** no GitHub, por exemplo `radar-brasil`. Em repositório público o Actions e o Pages são gratuitos sem limite prático.
2. Envie este projeto:
   ```bash
   cd radar-brasil
   git init -b main && git add . && git commit -m "Radar Brasil"
   git remote add origin https://github.com/SEU_USUARIO/radar-brasil.git
   git push -u origin main
   ```
3. No repositório: **Settings → Pages → Source: GitHub Actions**.
4. **Actions → Radar Brasil → Run workflow**, marcando *"Gerar o boletim semanal agora"*, para ter a primeira edição sem esperar a segunda-feira.
5. Ao terminar, o link do site aparece no resumo do workflow (`https://SEU_USUARIO.github.io/radar-brasil/`).

Depois da primeira execução, abra a página **Status** do site: ela mostra quais fontes responderam. Feeds RSS mudam de endereço com o tempo; se algum estiver com erro, corrija a URL em `config/fontes.yml`.

## Modelo de linguagem

O padrão é o **GitHub Models** (`openai/gpt-4.1`), autenticado pelo token do próprio Actions, sem chave nem cadastro extra. O plano gratuito tem limite de requisições e de tamanho por chamada, por isso o boletim é dividido em três chamadas pequenas.

- **Trocar o modelo:** Settings → Secrets and variables → Actions → *Variables* → `LLM_MODEL` (ex.: `openai/gpt-4.1-mini`).
- **Outro provedor compatível com OpenAI** (ex.: Gemini): defina `LLM_PROVIDER=openai-compatible`, `LLM_BASE_URL` e o secret `LLM_API_KEY`, e passe-os no passo "Gerar boletim semanal" do workflow.

Se o modelo falhar, o boletim sai assim mesmo, com o painel de números e um aviso na seção de análise.

## Rodar localmente

```bash
pip install -r requirements.txt
python -m radar.collect                         # coleta
LLM_DRY_RUN=1 python -m radar.analysis.relatorio  # boletim sem chamar o modelo
python -m web.build                             # site em _site/
python -m pytest tests
```

Para testar com o modelo de verdade, exporte um `GITHUB_TOKEN` pessoal (fine-grained, permissão *Models: read*).

## Estrutura

```
config/        indicadores.yml (séries do Banco Central/IBGE) e fontes.yml (feeds RSS)
prompts/       método anti-viés e instruções de cada seção
radar/         coleta (collectors/), cálculos e boletim (analysis/)
web/           gerador do site estático
data/          dados coletados, versionados (o "banco de dados")
relatorios/    edições semanais em Markdown
```

## Próximas fases

- **Fiscalização:** cartões corporativos (Portal da Transparência, chave gratuita), cota parlamentar (APIs da Câmara e do Senado) e acórdãos do TCU.
- **Institucional:** votações nominais no Congresso e decisões do STF com análise jurídica.
- **Mais indicadores:** resultado primário, CAGED e outras séries do SGS (basta adicionar o código em `config/indicadores.yml`).
