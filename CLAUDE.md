# Niche Finder — memória para o Claude

O dono não é programador: explique em português simples. Leia o `LEIA-ME.md` antes de mexer.

- O que é: acha canais NOVOS no YouTube (criados há até 30 dias, data da aba "Sobre") com pelo menos UM vídeo longo
  (4 min ou mais) com 50 mil views ou mais. Não é a soma do canal. Shorts não entram. 17 nichos amplos
  (`categorias.json`) em PT, ES, EN, DE e FR.
- Site: `docs/index.html` lê `docs/dados.json`. Fundo preto, cards, mapa dos nichos, filtros. Publicado pelo
  GitHub Pages (pasta `docs/`). Busca dados novos a cada 30 segundos.
- Busca: `finder.py` (usa funções de `cacador.py`). Memória em `estado/canais.json` (vai para o GitHub, para outra
  máquina continuar). `rodar.bat` roda e publica (`--publicar 5` = git push a cada 5 min).
- Máquina nova: clonar o repositório, rodar `instalar.ps1` (Python, yt-dlp, Deno, Git e a tarefa do Windows).
- Regras do dono: nada de número inventado; perguntar antes de mudar critérios; nunca usar a senha dele.
