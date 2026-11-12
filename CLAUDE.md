# Niche Finder — memória para o Claude

O dono não é programador: explique em português simples. Leia o `LEIA-ME.md` antes de mexer.

- O que é: acha canais NOVOS no YouTube (o 1º vídeo saiu nas últimas 3 semanas; a idade do canal não importa) com pelo menos UM vídeo longo
  (4 min ou mais) com 50 mil views ou mais. Não é a soma do canal. Shorts não entram. 17 nichos amplos
  (`categorias.json`) em PT, ES, EN, DE e FR.
- Link do site: https://eurafaelbarbosaoficial-dev.github.io/niche-finder/
- Site: `docs/index.html` lê `docs/dados.json`. Fundo preto, cards, mapa dos nichos, filtros. Publicado pelo
  GitHub Pages (pasta `docs/`). Busca dados novos a cada 30 segundos.
- Busca: `finder.py` (usa funções de `cacador.py`). Memória em `estado/canais.json` (vai para o GitHub, para outra
  máquina continuar). `rodar.bat` roda e publica (`--publicar 5` = git push a cada 5 min).
- Máquina nova: clonar o repositório, rodar `instalar.ps1` (Python, yt-dlp, Deno, Git e a tarefa do Windows).
- Regras do dono: nada de número inventado; perguntar antes de mudar critérios; nunca usar a senha dele.

## Validador de dobras (quando o dono pede "valide o título X")
1. Escreva `validacoes/pedidos/<slug>.json` (formato no topo de `validador.py`): origem (título, canal, id do vídeo,
   views, idioma, canal_id), o **molde** do título com [buracos], e 2 buscas por idioma (pt, es, en, de, fr) escritas
   **como um nativo buscaria** (1ª = o molde, 2ª = o tema). **Não invente dobras aqui** (deixe "dobras" vazio): as
   dobras e os próximos vídeos saem do `pautas.py`, só de dados. Base do método: `conhecimento/GUIA-DOBRA.md`.
2. Rode `python -I validador.py validacoes/pedidos/<slug>.json --publicar` (uns 5–10 min; em segundo plano).
3. Resultado: `docs/validacoes/<slug>.json`, visto em `docs/validador.html#<slug>`.
4. Explique ao dono por idioma: oportunidade / validado (subnichar) / feito sem sucesso, com os números.
   Se "validado: subnichar", proponha subnichos/públicos e ofereça validar de novo. Nada de número inventado.

## Pautas e dobras com dados (depois do validador, para o idioma escolhido)
Regra do dono: **nada de hipótese**. Todo candidato vem de dado real; o Claude só traduz.
1. No pedido, preencha `"pautas": {"idioma", "tema" (no idioma alvo), "molde_mundo" (molde em en/es/pt/fr/de),
   "molde_alvo" ("alle {X} erklärt"), "subnicho" (assunto do vídeo que estourou)}` e rode `python -I pautas.py coletar validacoes/pedidos/<slug>.json`.
2. Leia `validacoes/candidatos/<slug>.json`: (A) assuntos onde o molde já funcionou no mundo, (B) autocompletar do
   idioma alvo, (C) vídeos do canal de referência. Escolha só dali; traduza para o idioma alvo e grave em
   `pautas.candidatos` com `fonte` (A/B/C), `evidencia` (título + views de onde veio) e `grupo` ("pauta" = mesmo
   tema, próximo vídeo; "dobra" = outro nicho).
3. `python -I pautas.py medir validacoes/pedidos/<slug>.json --publicar` (~12 min). Aparece no Validador.

## Roteiro (aba Roteiro) — engenharia reversa, 5 estruturas, adaptação cultural
- `roteiro.py baixar <vídeo> <slug>` baixa a transcrição e mede (duração, palavras/min, capítulos). O Claude lê e
  escreve `roteiros/<slug>/analise.json` (gancho, blocos com tempo e função, transições, gatilhos, CTA, regra).
- **Banco de 5 estruturas validadas** (vídeos reais com muitas views), para alternar e não cair em conteúdo
  repetitivo: catálogo sequencial (`lavagem-de-dinheiro-de`), iceberg, documentário investigativo, ascensão e
  queda, passo a passo em capítulos (`estrutura-*`). Para outro tema, achar 5 referências do tema no validador.
- **Adaptar, não traduzir**: antes de escrever, montar `roteiros/adaptacao-<idioma>-<tema>.json` só com dados
  locais (vídeos do idioma com views + minuto, autocompletar do idioma, casos locais). Ex.: `adaptacao-de-lavagem.json`.
- O roteiro novo (`roteiro.json`: titulo, idioma, blocos[{bloco, segue, texto, fontes}]) copia a ESTRUTURA, nunca o
  texto; fatos com fonte (WebSearch). Publicar: `roteiro.py publicar <slug>`.
- Cada pauta recebe a relação com o canal pela FONTE do dado: B (autocompletar do tema) = mesmo subnicho, mesmo canal;
  C (canal de referência) = subnicho vizinho, mesmo canal em bloco temático; A (molde em outros assuntos) = outro
  nicho → canal novo. Nunca misturar nichos no mesmo canal (Raj, vídeos 12 e 13). A ficha "Seu projeto"
  (nicho → subnicho → micronicho) e o "Mapa de dobras" (5 caminhos, recomendado pelos dados) saem de `pautas.py mapa`.
