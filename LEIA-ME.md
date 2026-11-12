# Niche Finder

**Site:** https://eurafaelbarbosaoficial-dev.github.io/niche-finder/ · **Repositório:** https://github.com/eurafaelbarbosaoficial-dev/niche-finder

Acha **canais novos** no YouTube (o 1º vídeo saiu nas últimas 3 semanas) que já estão **performando**: têm pelo menos um vídeo
longo com 50 mil views ou mais. Não é a soma do canal. Procura em 17 nichos amplos e em PT, ES, EN, DE e FR, e mostra tudo num site em cards.
Não usa a API do YouTube.

## Arquivos

| Arquivo | Para quê |
|---|---|
| `finder.py` | A busca. Lê `categorias.json`, acha os canais, descarta os antigos e grava `docs/dados.json`. |
| `categorias.json` | Os nichos amplos e as buscas de cada idioma. Para pôr um nicho novo, copie um bloco e troque os termos. |
| `docs/index.html` | O site. Lê `docs/dados.json` e busca dados novos sozinho a cada 30 segundos. |
| `rodar.bat` | Roda uma busca completa e publica o site no GitHub. A tarefa do Windows chama este arquivo. |
| `cacador.py` | Funções de busca usadas pelo `finder.py` (vieram da skill /canal-dark). |
| `estado/` | Memória da busca: canais já checados e log. Fica só no PC, não vai para o GitHub. |

## Regras da busca

- **Canal novo:** o 1º vídeo do canal saiu nas últimas 3 semanas (21 dias). A idade do canal não importa.
- **Só vídeos longos:** 4 minutos ou mais. Shorts não entram.
- **Performando:** pelo menos UM vídeo longo com 50 mil views ou mais. Os outros vídeos podem ter menos.
- Canais com mais de 60 vídeos ficam de fora.
- Canal já descartado nunca é checado de novo. Canal novo é medido de novo a cada rodada, para mostrar o
  crescimento, até o 1º vídeo passar de 3 semanas.

Para mudar um número: `finder.py --dias-video 21 --bom-video 50000 --min-duracao 240`.

## Validador de dobras (aba "Validador" do site)

Pega um título que estourou e pesquisa o mesmo molde em PT, ES, EN, DE e FR, mais algumas dobras para outros nichos.
Para cada idioma diz se é **oportunidade** (ninguém faz e o tema tem procura), **validado** (já fazem e funciona:
entrar subnichando ou mudando o público) ou **feito sem sucesso** (alerta). Como pedir: no site, cole o título,
copie o pedido e mande para o Claude Code nesta pasta. Ele escreve as buscas (como um nativo buscaria) e roda
`validador.py`. O método está em `conhecimento/GUIA-DOBRA.md`.

## Como o site fica sempre atualizado

1. A tarefa do Windows "Niche Finder" roda `rodar.bat` a cada 3 horas. O notebook precisa estar ligado.
2. Durante a busca, o `finder.py --publicar 5` manda o `docs/` para o GitHub a cada 5 minutos.
3. O GitHub Pages publica o site num link fixo, que abre em qualquer navegador e em qualquer conta.
4. O site busca dados novos sozinho a cada 30 segundos.

Para ver no próprio PC, sem GitHub: `python -m http.server 8765 --directory docs` e abra http://localhost:8765.

## Trocar de máquina

**Só quer ver o site?** Não precisa de nada: abra o link do GitHub Pages em qualquer navegador.

**Quer que a máquina nova faça as buscas?** Tudo o que precisa está no repositório do GitHub, inclusive a memória
da busca (`estado/canais.json`). Não precisa copiar nenhuma pasta à mão.

1. Instale o Git, se ainda não tiver: `winget install Git.Git`.
2. Baixe o repositório para a pasta Documentos:
   `git clone https://github.com/eurafaelbarbosaoficial-dev/niche-finder "%USERPROFILE%\Documents\Niche Finder"`.
3. Dentro da pasta, rode `powershell -ExecutionPolicy Bypass -File instalar.ps1`. Ele instala Python, yt-dlp e Deno
   e cria a tarefa do Windows que roda a busca a cada 3 horas.
4. Na máquina antiga, apague a tarefa (Agendador de Tarefas → "Niche Finder" → Excluir). Duas máquinas buscando ao
   mesmo tempo brigam na hora de publicar.

Com o Claude Code: abra a pasta "Niche Finder" e diga "leia o CLAUDE.md". Ele entende o projeto sozinho.
