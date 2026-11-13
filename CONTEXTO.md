# CONTEXTO COMPLETO DO PROJETO (ler primeiro numa conversa nova)

Atualizado em 12/11/2026. Este arquivo existe para que qualquer conversa nova, outra máquina ou outra conta do
Claude continue o trabalho sem perder nada. Junto com `CLAUDE.md`, `LEIA-ME.md` e `conhecimento/`.

## Quem é o dono e o que ele quer
- Não é programador: falar **sempre em português simples**, sem jargão.
- Situação: perdeu a renda (R$ 4.000/mês), paga R$ 1.200 de aluguel, quer monetizar canais dark no YouTube. Não
  prometer prazo nem valor; ser sincero (monetizar em 1 mês é improvável; execução e constância decidem).
- Objetivo do sistema: uma "máquina" para achar canais que estouraram, validar onde mais o formato funciona
  (dobra de nicho do Raj), planejar os próximos vídeos e escrever roteiros — tudo **com dados reais, nada de
  achismo/hipótese/invenção**. Quer o sistema robusto também para, no futuro, ajudar outras pessoas ou vender.
- Referências: Raj Teixeira (canal "Rhaj", 28 vídeos estudados em `conhecimento/raj/notas.md`) e o "Grimório do
  Mago" (sistema fechado e pago; NÃO tentar acessar, só construir a nossa versão).
- Regras fixas: nada de número inventado; perguntar antes de mudar critérios; nunca usar a senha dele; não
  colocar o e-mail dele em serviço externo; separar dado de hipótese; dizer de onde veio cada número.

## O método (resumo do Raj — detalhes em `conhecimento/GUIA-DOBRA.md`)
- **Domine o micro (formato), troque o macro (nicho).** Formato = como o vídeo é feito + molde do título.
- 5 caminhos de dobra: outro idioma · outro nicho no mesmo idioma · outro nicho em outro idioma (canal novo) ·
  outro formato no mesmo nicho · outro público.
- **Nunca misturar nichos no mesmo canal.** Outro nicho = canal novo. Canal = nicho → subnicho → micronicho.
- Adaptar, não traduzir: o roteiro de outro idioma usa casos, comparações e palavras daquele público (com dado).
- Variar entre 5 estruturas de roteiro validadas para não cair em "conteúdo repetitivo" do YouTube.
- Validar antes de criar: estágio do formato (E1 emergente … E8 saturado), demanda do nicho, moat.

## O sistema (pasta `Documents/Niche Finder`, repositório GitHub eurafaelbarbosaoficial-dev/niche-finder)
Site: https://eurafaelbarbosaoficial-dev.github.io/niche-finder/ (GitHub Pages, pasta `docs/`).
Visual: preto, vidro, acento verde-limão #D4FF3A, fontes Geist (sem fonte de código), cards com capa, animações
(`docs/estilo.css` + `docs/ui.js`). O dono pediu: moderno, "2026", nada de cara de terminal ou de site feito por IA.

| Parte | Arquivos | O que faz |
|---|---|---|
| Busca de canais (aba Canais) | `finder.py`, `cacador.py`, `categorias.json`, `rodar.bat` | Tarefa do Windows a cada 3 h. Busca por 17 nichos + grupo "Formatos" (What if, catálogo, POV, iceberg, níveis, como era antigamente…) em PT/ES/EN/DE/FR. Outlier = 1º vídeo há ≤ 21 dias E 1 vídeo longo (4 min+) com ≥ 50 mil views. Publica no GitHub a cada 5 min. |
| Clusters de título | `clusters.py` → `docs/clusters.json` | Agrupa os títulos de cada outlier pelo molde ([X]) e mostra quais rendem mais que a média; "moldes em alta" entre canais. Roda no fim de cada busca. |
| Validador (aba Validador) | `validador.py` → `docs/validacoes/` | Pesquisa o molde de um título nos 5 idiomas: oportunidade / validado / feito sem sucesso. |
| Pautas e dobras | `pautas.py coletar|medir|mapa` → `docs/pautas/` | Candidatos SÓ de dados (A molde no mundo, B autocompletar do idioma, C canal de referência); o Claude só traduz; mede demanda e concorrência no idioma; ficha do projeto (nicho/subnicho/micronicho), etiqueta mesmo canal × canal novo, mapa de dobras com caminho recomendado. |
| Roteiro (aba Roteiro) | `roteiro.py`, `roteiros/` → `docs/roteiros/` | Baixa a transcrição da referência, o Claude faz o mapa da estrutura; banco de 5 estruturas; estudo de adaptação cultural; roteiro novo copia a estrutura, nunca o texto, com fontes. |

Passo a passo de cada parte: `CLAUDE.md`. Instalar em máquina nova: `LEIA-ME.md` (clonar + `instalar.ps1`).

## Estado atual (12/11/2026, 20h)
- Busca: 3.063 canais checados, 56 outliers (21 deles "E se / What if"). Inscritos corrigidos (página traduzida).
- Projeto 1 escolhido pelos dados: **canal alemão de lavagem de dinheiro**, formato catálogo ("Alle … erklärt"),
  a partir do outlier "Every Money Laundering Technique Explained" (Econ in a Nutshell, 1,1 mi, 4,9 mil inscritos).
  Validador: alemão = oportunidade (ninguém faz; tema com 1 mi de demanda). Próximos vídeos fortes: escândalos de
  lavagem nos bancos (202 mil), golpes contra idosos (49 mil). Canais novos possíveis no mesmo formato em alemão:
  criaturas míticas (1,85 mi), técnicas de manipulação (507 mil), tipos de alienígena (120 mil), livros proibidos.
- 5 estruturas de roteiro analisadas (catálogo, iceberg, documentário, ascensão e queda, passo a passo) +
  `roteiros/adaptacao-de-lavagem.json`.
- PRÓXIMO PASSO: escrever o 1º roteiro em alemão (tema a escolher pelo dono) e produzir o 1º vídeo.
- FEITO em 12/11 à noite: 14 formatos de título nas buscas (grupo "Formatos" em categorias.json), cada termo buscado
  2 vezes (relevância no mês + MAIS VISTOS da semana = ~620 buscas por rodada) e arquivo histórico
  (`docs/arquivo.json`, botão Agora | Arquivo no site: todo outlier que já apareceu, a base só cresce).
- Em aberto: faixa "Subindo" (abaixo de 50 mil mas ≥ 50× views/inscrito), se o dono quiser.

## Lições técnicas (para não repetir erros)
- `python -I` não põe a pasta do script no caminho: os scripts fazem `sys.path.insert`.
- No Windows, bash heredoc com texto grande às vezes falha: escrever o script num arquivo e rodar.
- YouTube limita (erro 429): pausas, 4 processos em paralelo no máximo.
- Idioma real: o título da busca vem traduzido; conferir na página do vídeo; se o YouTube não informa, detectar
  pelas palavras/letras do título (ä ö ü ß = alemão).
- Comparar tema por radical quase inteiro (não 6 letras): "Finanzisch" ≠ "Finanzagent".
- Busca do tema precisa ser só o assunto (sem "erklärt"), senão exige palavras demais.

## Quando o dono pedir para TROCAR DE MÁQUINA
O dono pede ("quero usar o Niche Finder nesta máquina nova") e o Claude faz, guiando em português:
1. `winget install Git.Git` (se faltar) e `winget install GitHub.cli`; o DONO faz o login (`gh auth login`) — nunca usar a senha dele.
2. `git clone https://github.com/eurafaelbarbosaoficial-dev/niche-finder "%USERPROFILE%\Documents\Niche Finder"`.
3. Na pasta: `powershell -ExecutionPolicy Bypass -File instalar.ps1` (Python, yt-dlp, Deno, tarefa a cada 3 h).
4. Configurar o git (user.name eurafaelbarbosaoficial-dev e o e-mail noreply do GitHub, nunca o e-mail pessoal).
5. Ler este arquivo; rodar `python -I finder.py --publicar 5` de teste e conferir se o site atualiza.
5b. Clonar também `eurafaelbarbosaoficial-dev/estudos-de-mercado` (PRIVADO) em `Documents\estudos-de-mercado`: lá ficam as
   skills do dono (`setup/skills/`: canal-dark, estudar, novela-americana, claude-youtube, watch-skill) e a memória do
   Claude (`setup/memoria-claude/`). Copiar as skills para `%USERPROFILE%\.claude\skills\` e rodar `setup\instalar.ps1`.
5c. **Backup privado** (fora do GitHub de propósito): `Documents\Backup Niche Finder\backup-privado-<data>.zip` — chave da
   API do YouTube, prints do Studio, histórico dos canais e o vídeo final. O dono guarda no Drive/pendrive; na máquina nova,
   descompactar DENTRO de `Documents\Niche Finder`. Sem o zip: criar outra chave no Google Cloud (projeto "Niche Finder").
5d. Tarefas do Windows: o `instalar.ps1` cria "Niche Finder" (busca), "Niche Finder - Roteiros" (vigia) e
   "Niche Finder - Pautas semanais". O Claude Code de linha de comando precisa de login uma vez (`claude`, /login).
6. Na máquina antiga: apagar a tarefa "Niche Finder" (`Unregister-ScheduledTask -TaskName "Niche Finder" -Confirm:$false`),
   pelo Claude de lá ou pelo Agendador de Tarefas. Só uma máquina busca por vez.

## Botão "Fazer roteiro" (feito em 12/11, à noite)
- No Validador → Próximos vídeos, cada tema tem "Fazer roteiro" (abre uma issue no GitHub com rótulo `roteiro` e o
  pedido completo; o dono confirma com "Create") e "Copiar pedido" (para colar numa conversa).
- `vigia.py` (tarefa do Windows "Niche Finder - Roteiros", a cada 10 min, via `vigia.bat`) pega o pedido mais antigo,
  roda o Claude Code sozinho (`claude -p`, sem perguntas) na pasta, publica o roteiro e fecha a issue com o resumo.
- PRECISA: o Claude Code de linha de comando logado UMA vez pelo dono (`claude` no terminal → /login). Em 12/11 ainda
  não estava logado ("Not logged in"). Log em `estado/vigia.txt`.
- Bug corrigido em 12/11: em português o YouTube escreve "3,6 mil" e o yt-dlp lia 36 → nenhum canal brasileiro
  chegava a 50 mil. Agora as views vêm sempre da página em inglês (finder.lista_videos).
- 12/11 22:05: 1º ROTEIRO PRONTO pelo botão (issue #1, ~8 min): "Alle Geldwäsche-Skandale der Banken erklärt"
  (`roteiros/bankskandale-de/`), estrutura iceberg, 6 níveis (N26 → ING/Commerzbank → Deutsche Bank → HSBC/TD → Danske →
  BCCI), ~1.500 palavras (~9 min), 32 links de fonte, adaptação `roteiros/adaptacao-de-bankskandale.json`.
- Estilo de produção escolhido pelos dados: animação 2D com personagem mascote (como o vídeo de referência de 1,1 mi),
  feita por código (HyperFrames).

## Produção de vídeo (amostra aprovada em 12/11, à noite)
- Amostra: `videos/amostra-bankskandale/` (HyperFrames 0.9.40), 29 s, abertura do roteiro Bankskandale.
  Render final em `renders/amostra-bankskandale.mp4`.
- **Voz:** ElevenLabs **v4** via a API que o dono manda na hora (ai84.pro em 12/11). **A CHAVE NUNCA É SALVA**: o
  dono troca de app e manda uma chave nova por sessão. Voz usada: "Alexander - Deep TV Narrator"
  (`kkJxCnlRCckmfFvzDW5Q`). O dono achou a narração "excelente": manter essa voz. A API exige o cabeçalho
  `User-Agent: curl/8.5.0` (o do Python leva 403).
- **Estilo aprovado pelo dono** (a 1ª versão em SVG "tinha cara de HyperFrames"; ele quer canal de alta barreira,
  confortável de assistir):
  - tudo desenhado em **Canvas 2D** com `assets/js/pincel.js`, a biblioteca do canal;
  - traço de pincel com pressão (`assets/js/perfect-freehand.js`, MIT), linha que "ferve" a 12 fps;
  - papel com textura, luz única vinda de cima/esquerda e paleta quente apagada (ocre, terracota, ardósia, sálvia,
    tinta #2b2420);
  - títulos em Playfair Display; rótulos em Inter.
- **Personagem fixo:** o detetive (`Pincel.detetive`), de sobretudo, chapéu e gravata terracota. O rig tem
  respiração, piscada, olhar, sobrancelha, cara zangada, boca e mão no queixo. Também: policial figurante
  (`Pincel.policial`), prédios (`Pincel.casa`), moedas (`Pincel.moeda`) e balões de pensamento (`Pincel.nuvem`).
  Cenas novas reaproveitam a biblioteca: copie `assets/js/` para o projeto novo.
- **Sem música** por enquanto (não há gerador de música aqui). Efeitos em `assets/sfx/`, com créditos em
  `.media/audio/sfx/CREDITS.md`; os CC BY precisam de crédito na descrição do vídeo.
- Amostra final aprovada pelo revisor: `renders/amostra-bankskandale-final.mp4`.
- Próximo passo: o vídeo completo, ver `videos/PLANO-bankskandale-completo.md` (~14 min, ~12.700 créditos de voz,
  8 capítulos).

## Agente revisor de vídeo (pedido do dono em 12/11)
- `.claude/agents/revisor-video.md` + `revisor.py`. O agente roda depois de cada render e revisa três coisas:
  - imagem quadro a quadro (texto sobre o personagem, personagem quebrado, cortes);
  - narração × roteiro (transcrição com faster-whisper `medium`, local, palavra por palavra com o tempo);
  - volume: mix entre -16 e -12 LUFS, pico < -1 dBTP; efeito no máximo +3 LU acima da fala forte; música de 12 a
    30 LU abaixo da narração. Esses limites são critério nosso.
- Antes de revisar: `python -I masterizar.py <mp4>` → `<nome>-final.mp4` em -14 LUFS (é ele que vai para o YouTube).
- Retenção (pedido do dono: "não deve passar nada que diminua a retenção"):
  - trechos sem elemento novo na tela (3 s = médio, 5 s = alto; o tremor do traço não conta como novidade);
  - voz começando em até 1 s;
  - silêncios na fala;
  - palavras/min por idioma;
  - efeito que some debaixo da voz (janelas de 50 ms);
  - efeito com VOZ gravada;
  - o que cada arquivo de efeito É de verdade na fonte.
- Lições de 12/11:
  - o "sirene.mp3" era um whoosh e o "whoosh.mp3" era um impacto (os arquivos estavam com o nome trocado);
  - um "rubber stamp" baixado era uma pessoa FALANDO "rubber stamp";
  - o revisor agora pega os dois casos.
- Ele gera `<mp4>-revisao/RELATORIO.md` e as folhas de contato. O agente escreve o `REVISAO.md` com o veredito.
  Não corrige sozinho.

## 1º vídeo completo (feito sozinho na madrugada de 13/11, a pedido do dono)
- Pasta `videos/bankskandale-completo/`. Leia o `PROGRESSO.md` dela: tem o passo a passo e as lições.
- **Linha de produção** (serve para os próximos vídeos):
  1. voz por bloco do roteiro (ElevenLabs v4, chave do dono só na sessão);
  2. `palavras.py` (tempo de cada palavra, whisper local) → conferir se o número de palavras bate com o roteiro;
  3. `cenas.py` (roteiro visual, cenas presas às frases);
  4. `montar.py kN`;
  5. `fotos.py kN` (foto de cada cena a 85%: pega defeito de layout antes do render);
  6. `renderizar.sh`;
  7. `remixar.py` (refaz só o áudio, sem renderizar de novo);
  8. `juntar.py` (corta o silêncio entre capítulos e põe o som de transição);
  9. `masterizar.py`;
  10. `revisor.py` + revisão visual;
  11. `publicar/` (thumbnail, título, descrição com capítulos, fontes e créditos, tags).
- **Motor de cenas** `comum/js/motor.js`: 18 modelos desenhados com o Pincel. Para outro tema, troque o `cenas.py`
  e, se precisar, crie modelos novos.
- **Custos e tempos medidos:**
  - voz: 12.252 créditos para ~10.000 caracteres (≈1,2 por caractere);
  - render: ~5 s de processamento por segundo de vídeo (quando roda sozinho);
  - vídeo de ~12 min.
- **Som:** o arquivo `moedas` original era baixo demais (o "clink" é curto). Foi comprimido e amplificado: o crédito
  CC BY diz "bearbeitet".

## Linha de produção com "feedback loop" (pedido do dono em 13/11, a partir do Raj vídeo 29)
Pasta `producao/`. Aba **Produção** no site (`docs/producao.html`).
- **Lições do revisor** (`producao/licoes.json`, `licoes.py`): cada erro que o revisor (ou o dono) acha vira
  regra + "como conferir". O `montar.py` mostra as lições antes de montar; o `revisor.py` põe a lista com caixinhas
  no RELATORIO; os agentes `revisor-video` e `revisor-roteiro` gravam lições novas. Lição que falha de novo = alto.
- **Revisor de roteiro** (`producao/revisor_roteiro.py` + agente `.claude/agents/revisor-roteiro.md`): ANTES da voz.
  Mede a duração (voz alemã medida: 126 palavras/min; acertou 11,9 min × 12:04 reais), links, números × fontes do
  bloco, frases longas, gancho, risco jurídico. Gera `roteiros/<slug>/REVISAO-ROTEIRO.md`.
- **Bíblia visual** (`producao/biblia.py <canal> <slug>`): baixa thumbs + os vídeos mais vistos da referência e
  mede (trocas de cena/min, plano médio, paleta). Resultado em `referencias/<slug>/` + `biblia-visual.md`.
  Econ in a Nutshell: 14,9–17,4 trocas/min (plano 3,4–4 s); o NOSSO vídeo: 3,1/min (18,6 s) → lição L013.
- **Calendário** (`producao/calendario.py <projeto> --ref <ref> --feitos "..."`): pautas fortes/boas + vídeos do
  canal de referência acima da mediana ("a medir"), nos dias/hora escolhidos (padrão sáb e qua, 17:00 Alemanha).
- **Esteira** (`producao/esteira.py`, `producao/projetos.json`): ideia → roteiro → revisão → voz → montagem →
  revisão do vídeo → pronto → publicado, lida dos arquivos. Botão "Nova ideia" abre issue com rótulo `ideia`; o
  `vigia.py` mede a ideia com dados e refaz a esteira a cada 10 min. Quando postar, preencher `publicado_em` e `url`
  no `projetos.json`.
- Shorts: o dono decidiu não fazer por enquanto. Canal como vitrine de produto: para depois.
- Canal: nome sugerido "Geld im Dunkeln" (aguardando o dono); arte em `videos/bankskandale-completo/publicar/`.

## Rodada de melhorias de 13/11 (tarde/noite) — rapidez e acerto
- **Linha de produção para qualquer vídeo** (`producao/produzir.py`): `novo <roteiro> <pasta> --ref <referência>` copia
  `producao/modelo-video/` (motor, efeitos, montar, fotos, render, remix, juntar) e cria `projeto.json` com o RITMO ALVO
  medido na referência; `status <pasta>` diz a etapa e o próximo comando; `rodar <pasta> <etapa>`.
  Voz: `K=<chave> python -I producao/voz.py …` (chave nunca salva). Cenas: agente `diretor-de-cenas` (usa
  `producao/modelo-video/CATALOGO.md`, gerado por `producao/catalogo.py`). O formato/ritmo vem da referência de cada
  canal; o motor desenha o nosso estilo 2D (outro estilo visual = motor novo).
- **Ritmo quadro a quadro** (`producao/ritmo.py`): cada cena (início, fim, duração), cada transição com tipo
  matemático (corte seco, fusão por mistura, fade para preto/branco/cor lisa, movimento) e duração em quadros.
  Validado no nosso vídeo (acertou os dips em 15,97/36,8/48,05 s). Econ in a Nutshell: 173 cenas, 15,4 trocas/min, cena
  média 3,88 s (metade entre 2,7 e 4,9 s), 97% corte seco. `producao/estilo.py estudar|comparar` = ritmo + lupa da
  /estudar (sons, câmera) em 3 trechos; agente `estudo-estilo`.
- **Legenda SRT** com o texto exato do roteiro (`producao/legenda.py`; 99% das palavras casadas com a voz).
- **3 thumbs por vídeo** (`producao/thumbs.py`, `producao/modelo-thumb/`): mesmo desenho, textos = fatos do roteiro;
  "Testar e comparar" do YouTube com o MESMO título (testar uma coisa por vez).
- **Desempenho dos nossos vídeos** (`producao/desempenho.py`): views/curtidas/comentários a cada 3 h (vigia), 24 h/48 h/7 d;
  print do Studio entra com `desempenho.py studio <pasta> --ctr … --retencao …`. Ao postar: pôr `url` e
  `publicado_em` em `producao/projetos.json`. API do YouTube opcional: `estado/youtube-api.txt` (fora do git).
- **Subindo** (aba Canais → Subindo, `docs/subindo.json`): canais novos abaixo de 50 mil que crescem rápido
  (≥ 5 mil no melhor vídeo e +2 mil/dia ou 20× views/inscrito; critério nosso). **Bola de neve**: a cada rodada, os
  vídeos relacionados de cada outlier entram na fila (~19 canais por vídeo; a API não oferece isso).
- **Validador com sinais**: estágio do formato (vazio/começando/crescendo/maduro/saturando), vídeos novos no mês e no
  ano, canais pequenos com sucesso. Ex.: o formato "every … explained" está SATURANDO em inglês e VAZIO em alemão.
- **Títulos** (`producao/titulos.py <projeto> "<tema>"`): autocompletar, mais vistos e moldes que rendem no idioma.
- **Pautas semanais** (`producao/semanal.py`, `semanal.bat`): coleta + medida + matriz de validação (Raj 25, nota do
  Claude marcada como opinião) + árvore editorial + calendário. A tarefa do Windows precisa ser criada pelo dono:
  `powershell -ExecutionPolicy Bypass -File producao\agendar-semanal.ps1` (o instalar.ps1 já cria em máquina nova).

## Aba "Meus canais" (pedido do dono em 13/11)
- `docs/meus-canais.html` + `producao/meus_canais.py`: cada canal de `producao/canais.json` com o campo `youtube` é medido
  a cada 3 h pela API (inscritos, views, vídeos; por vídeo: views, +24 h, curtidas, comentários e os últimos comentários,
  sem o nome do autor). Histórico em `estado/meus-canais.json`.
- Ligar o link do canal: botão "Adicionar link do canal" → issue com rótulo `meu-canal` → o vigia grava o link.
- **Prints do YouTube Studio** (retenção, cliques na thumb, origem do público): o repositório é PÚBLICO, então os prints
  vão para a pasta PRIVADA `prints-studio/<id-do-canal>/` (fora do git). O vigia acha prints novos, o Claude lê cada
  imagem e grava só os números que aparecem (`producao/studio.py adicionar`) em `producao/studio.json`; problemas claros
  viram lição. O site avisa quando o último print tem 2 dias ou mais. O dono também pode mandar os prints na conversa.
