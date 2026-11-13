# Progresso do vídeo completo (para continuar de onde parou)

Pedido do dono (13/11, madrugada): fazer o vídeo inteiro sozinho, tudo passado pelo agente revisor, pronto para
postar de manhã. Ele autorizou tudo (gastar créditos de voz, decidir, editar). Ajustes: ele pede depois.

## Feito
- **Voz:** os 8 blocos (`voz/bloco-N.mp3`) + 2 trechos do bloco 1 (`voz-extra/`). ElevenLabs v4, voz Alexander;
  12.252 créditos no total. A chave NÃO está salva em lugar nenhum.
- **Motor de cenas:** `comum/js/motor.js`, com os modelos titulo, numero, comparar, local, banco, rota, fluxo,
  iceberg, documento, lista, celular, guiche, carta, teia, balanca, detetive, tempo e cta.
  - "Batidas" de câmera automáticas onde a cena passaria mais de 2,8 s sem novidade.
- **Roteiro visual:** `cenas.py`. Cada cena começa numa frase da narração.
- **Montador:** `montar.py <cap>`. Acha o segundo de cada frase na transcrição (`*.palavras.json`), escreve
  `<cap>/index.html` e põe os efeitos sonoros. Também mostra os trechos de mais de 3 s sem novidade.
- **Render em lote:** `renderizar.sh k1b k1d k2 …`.
- **Junção:** `juntar.py`. O capítulo 1 é a amostra aprovada (0–16,95 s) + k1b + amostra (16,95–28,3 s) + k1d;
  depois vêm k2…k8.

## Cuidado
- A transcrição longa do whisper às vezes PULA uma frase inteira. No bloco 4, "Juli 2020 … 150 Millionen Dollar
  Strafe" não apareceu. `palavras.py` agora usa `vad_filter` e `condition_on_previous_text=False`. Depois de
  transcrever, conferir se o número de palavras bate com o roteiro e procurar buracos de mais de 2 s.

- As batidas de câmera (punch-in) precisam ser calculadas ANTES de escrever o index.html. Até 02:45 de 13/11 elas
  não entravam no vídeo. Com zoom de 8% e pan de 46 px, o detector de "novidade" do revisor enxerga a batida.
- O texto em canvas precisa de `textAlign = "left"` dentro de `texto()`. Um "center" vindo de outro desenho
  embaralhava as palavras.
- Fotografar cada cena a 85% da duração (`python -I fotos.py kN`) pegou 8 defeitos de layout antes do render.
- Render: ~20 s de processamento por segundo de vídeo neste PC, quando roda junto com outras tarefas.

## Próximos passos
1. Renderizar k4…k8: `./renderizar.sh k4 k5 k6 k7 k8`, depois de `python -I montar.py kN` para cada um.
2. `python -I juntar.py`, depois `python -I ../../masterizar.py renders/bankskandale-completo.mp4`.
3. Revisor:
   - `python -I ../../revisor.py --video renders/bankskandale-completo-final.mp4 --idioma de`, mais o roteiro
     em txt;
   - fazer a revisão visual das folhas de contato;
   - escrever o `REVISAO.md`.
4. Thumbnail, título, descrição (fontes + créditos CC BY dos sons) e tags: pasta `publicar/`.
