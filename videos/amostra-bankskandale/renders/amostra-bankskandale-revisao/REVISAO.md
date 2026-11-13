# Revisão: amostra-bankskandale.mp4
Veredito: **APROVADO COM AJUSTES**

## Problemas
| # | tempo | área | gravidade | o que está errado | como corrigir |
|---|---|---|---|---|---|
| 1 | todo o vídeo | som | média | Volume geral em **-18,8 LUFS**; a faixa-alvo é de -16 a -12. O YouTube abaixa vídeo alto, mas não sobe vídeo baixo: fica mais baixo que os outros vídeos que a pessoa assiste. | Normalizar o mix final para -14 LUFS (pico ≤ -1 dBTP) na exportação. |
| 2 | 5,05 s · 12,50 s · 16,75 s | som | média | Os 3 *whoosh* passam a fala forte em **+5,9 / +4,9 / +3,8 LU** (limite +3, critério do revisor). | `data-volume` dos whoosh de 0,45/0,40/0,35 para ~0,32 ou menos. |
| 3 | 6,0–6,4 s | imagem | baixa | Os policiais nascem de baixo do chão e a linha do chão corta o corpo deles por um instante. | Entrada com fade + subida curta acima da linha, ou desenhar o chão por cima. |
| 4 | 6,7–10,5 s | imagem | baixa | O último policial da fileira de trás sobra meio corpo para fora, à direita da fileira da frente. | Fileira de trás com 9 policiais, ou deslocar para dentro. |
| 5 | 14,0–16,9 s | imagem | baixa | O título "Die Zentrale der Deutschen Bank" fica em cima do topo das torres. Dá para ler por causa da sombra, mas disputa com o desenho. | Subir o título uns 30 px ou começar as torres mais baixas. |

## Conferido e ok
- **Narração × roteiro:** 51 de 51 palavras iguais (0,0% de diferença), transcrição local com o whisper medium.
  Nenhuma palavra trocada ou pulada.
- **Pico** -1,4 dBTP: não estoura. Faixa dinâmica (LRA) de 4,3 LU, estável.
- **Pops, sirene e moedas:** de 3 a 8 LU abaixo da fala, audíveis sem cobrir a voz. Os dois impactos chegam a
  +1,7 e +2,8 LU, dentro do limite.
- **Música:** não tem (combinado).
- **Imagem:**
  - nenhum texto sobre o rosto do detetive;
  - personagem inteiro e igual em todas as cenas (17–29 s);
  - sem tela preta e sem imagem congelada fora das pausas de propósito;
  - textos da tela batem com a narração no tempo certo (data 0,9–2,6 s, "170" em 5,4 s, instituições em
    8,3–9,7 s, "6 Gebäude" em 10,6 s, balões em 18,6 / 19,5 / 20,6 s, título final em 26,7 s).
- **Técnico:** 1920x1080, 30 fps, H.264 + AAC, 29,2 s.
