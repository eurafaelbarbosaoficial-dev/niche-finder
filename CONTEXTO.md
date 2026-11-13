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
