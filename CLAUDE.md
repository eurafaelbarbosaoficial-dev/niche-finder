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
   views, idioma), o **molde** do título com [buracos], e 2 buscas por idioma (pt, es, en, de, fr) escritas **como um
   nativo buscaria** (não tradução literal), e de 2 a 4 **dobras** (mesmo molde em outros nichos/públicos), com uma
   nota curta do porquê (driver, público). Base do método: `conhecimento/GUIA-DOBRA.md`.
2. Rode `python -I validador.py validacoes/pedidos/<slug>.json --publicar` (uns 5–10 min; em segundo plano).
3. Resultado: `docs/validacoes/<slug>.json`, visto em `docs/validador.html#<slug>`.
4. Explique ao dono por idioma: oportunidade / validado (subnichar) / feito sem sucesso, com os números.
   Se "validado: subnichar", proponha subnichos/públicos e ofereça validar de novo. Nada de número inventado.
