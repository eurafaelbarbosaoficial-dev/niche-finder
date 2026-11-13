# Revisão: Alle Geldwäsche-Skandale der Banken erklärt
Veredito: **APROVADO COM AJUSTES** (nenhum problema alto; os médios são pausas naturais da fala e diferenças de
transcrição, sem defeito no vídeo).

Arquivo: `publicar/Alle-Geldwaesche-Skandale-der-Banken-erklaert.mp4`. Duração 12:04, 1920x1080, 30 fps,
H.264 + AAC 320k.

## Corrigido depois que o dono assistiu (13/11, 12:25)
- **Aos 17 s havia corte seco + emenda de voz.** O capítulo 1 juntava duas gravações diferentes (a da amostra e
  uma nova) e trocava a cena noturna pelo documento num quadro só, cortando o som de transição no meio.
- **Agora:**
  - o capítulo 1 usa UMA tomada contínua de voz (`capitulo1.py`);
  - as cenas da amostra foram reajustadas palavra por palavra a essa tomada;
  - os cortes viraram um "dip" suave para a cor do papel, com o som de transição inteiro;
  - a visão geral do iceberg acende a faixa de cada nível quando a voz fala dele.
- **O revisor passou a pegar os dois casos:** corte seco (lista automática) e emenda de voz (regra 16 do agente).
- **Ainda existem cortes de noite para papel com whoosh** nos capítulos 3, 4, 7 e 8, no mesmo estilo dos 5 s e
  12 s que o dono aprovou na amostra. O revisor os lista como "corte seco com som de transição". Podem virar
  "dip" suave se o dono quiser.

## Problemas restantes
| # | tempo | área | gravidade | o que é | decisão |
|---|---|---|---|---|---|
| 1 | 15,9 s | retenção | média | Pausa de 1,5 s depois de "…der Deutschen Bank." | Coberta pelo carimbo "RAZZIA" e pelo impacto (cena aprovada pelo dono na amostra). Mantida. |
| 2 | 340,6 · 412,1 · 414,7 s | retenção | média | Pausas de ~1,0 s entre frases. | Respiração natural do narrador, cobertas por batidas de câmera. Mantidas. |
| 3 | vários | narração | média | 25 palavras "diferentes" na transcrição: palavra composta junta ou separada, número por extenso ("zwei" × "2"), grafia de nome ("Wimpelkomm", "Appstein", "Borgens"), "Merkt ihr" × "Merk dir". | Erro da transcrição, não da voz: no áudio, as frases estão completas. 1.512 de 1.520 palavras batem. |
| 4 | 45 s do cap. 4 | som | baixa | Uma moeda fica só +0,3 dB acima da voz num trecho de fala forte. | Mantida. |

## Retenção (números)
- **Nenhum trecho de 3 s ou mais sem novidade na tela** nos 12 min (2.827 momentos de mudança).
- A voz começa em 0,0 s. O gancho tem data, lugar, 170 policiais e a sirene alemã nos primeiros 5 s.
- Ritmo da fala: 126 palavras/min (faixa do alemão: 95–160). Nenhuma pausa maior que 1,5 s.
- Entre capítulos, a pausa é de ~1,5 s com o cartão "Ebene N" e o som de transição. Antes eram 3–5,7 s; foram
  cortadas na junção.
- Sem tela preta, sem imagem congelada.

## Som
- Volume geral -14,2 LUFS (padrão do YouTube), pico -1,6 dBTP, faixa dinâmica de 3,9 LU.
- Cada efeito foi medido por capítulo:
  - todos aparecem por cima da voz (exceto o item 4);
  - nenhum passa da fala;
  - nenhum tem voz gravada;
  - todos têm o arquivo certo (conferido na fonte).

## Imagem
- Cada uma das 128 cenas foi fotografada no momento mais completo antes do render. Defeitos corrigidos:
  - carimbo em cima do texto;
  - texto em cima de ícone;
  - palavras embaralhadas;
  - rótulos cortados;
  - título do iceberg cortado.
- Cada corte entre capítulos foi conferido no vídeo final.
- Todo número na tela está no roteiro (32 fontes listadas na descrição).

## Conferido por
`revisor.py` (medições), agente revisor (folhas de contato, cortes, aberturas) — 13/11/2026.
