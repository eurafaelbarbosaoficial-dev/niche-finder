# Plano: vídeo completo "Alle Geldwäsche-Skandale der Banken erklärt"

Roteiro: `roteiros/bankskandale-de/roteiro.json` (8 blocos, 9.998 caracteres, 32 fontes).
Estilo aprovado: o da amostra (`videos/amostra-bankskandale/`), Canvas 2D + `assets/js/pincel.js`, detetive fixo.

## Números (medidos na amostra, não estimados)
- Voz "Alexander - Deep TV Narrator", ElevenLabs v4: **109 palavras/min** em alemão. Os ~1.500 palavras do roteiro
  dão uns **14 min** de vídeo (o roteiro estimava 9 min a 165 palavras/min).
- Custo de voz: a amostra gastou 419 créditos para ~330 caracteres (≈1,27/caractere). O roteiro inteiro sai por uns
  **12.700 créditos**. Conferir o saldo antes.
- Render: 29 s levaram ~6 min neste PC, então 14 min levam umas **3 horas** (roda sozinho em segundo plano).

## Fio condutor visual (retenção)
É um vídeo iceberg. A cada nível, o detetive desce mais fundo num iceberg desenhado, com um medidor
"Ebene 1 … 6" e a profundidade. Esse mesmo plano volta entre os capítulos:
- dá à pessoa a sensação de progresso ("faltam 3 níveis") e segura até o fim;
- serve de respiro visual entre casos pesados.

## Capítulos (1 capítulo = 1 projeto HyperFrames, revisado pelo agente antes do próximo)
| # | bloco | assunto (do roteiro) | palavras | ~min |
|---|---|---|---|---|
| 1 | gancho | Razzia na Deutsche Bank, 29.11.2018 (os 28 s da amostra + o resto do bloco) | 148 | 1,4 |
| 2 | Ebene 1 | Conta aberta por app: o jeito "pequeno" de lavar | 171 | 1,6 |
| 3 | Ebene 2 | ING, 775 mi (2018) e outras multas: a bancona seriosa | 204 | 1,9 |
| 4 | Ebene 3 | A "máquina": Moscou–Londres–Nova York, 2011–2015 | 302 | 2,8 |
| 5 | Ebene 4 | Cartel mexicano e as caixas de dinheiro: 881 mi | 204 | 1,9 |
| 6 | Ebene 5 | Danske Bank, transferências da ex-União Soviética | 191 | 1,8 |
| 7 | Ebene 6 | BCCI, 1991: quando o banco É o crime | 147 | 1,3 |
| 8 | fecho | O padrão: os bancos pagam, quase ninguém é preso | 135 | 1,2 |

## Regras de produção
- **Todo número na tela vem do roteiro e da fonte dele.** Nada inventado (lição da amostra: tirei um "€ 1.000.000"
  que não existia).
- **Nada de logo ou marca real desenhada:** prédio estilizado, sem logotipo de banco.
- **Algo novo na tela a cada 3 s, no máximo;** o revisor mede isso.
- **Efeito sonoro:** só arquivo com licença CC0 ou CC BY. Sem voz gravada; o revisor checa. O som é do país do vídeo
  (Martinshorn alemão).
- **Narração:** gerada por bloco (8 chamadas), com a chave que o dono mandar na hora, **nunca salva**.
- **Fluxo de cada capítulo:**
  1. render;
  2. `masterizar.py`;
  3. agente `revisor-video` → `REVISAO.md`;
  4. o dono aprova;
  5. próximo capítulo.
- **No fim:** juntar os 8 capítulos, masterizar o vídeo inteiro e fazer a revisão final completa.
