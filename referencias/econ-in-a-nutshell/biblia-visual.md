# Bíblia visual: Econ in a Nutshell (canal de referência do projeto every-money-laundering)

Medido em 13/11/2026 com `producao/biblia.py`. Os dados estão em `medidas.json`, as thumbs em `thumbs.jpg` e os
quadros (1 a cada 3 s, primeiros 3 min) em `video-1.jpg` (Money Laundering, 1,1 mi) e `video-2.jpg`
(Retirement, 307 mil). **Dado** = medido. **Leitura** = minha interpretação, a conferir.

## 1. Ritmo de edição (dado)
| vídeo | duração | trocas de cena/min | plano médio |
|---|---|---|---|
| Every Money Laundering Technique Explained (1,1 mi) | 11:11 | **14,9** | **4,0 s** |
| Why You'll Never Actually Spend Your Retirement Savings (307 mil) | 10:07 | **17,4** | **3,4 s** |
| **Nosso** Alle Geldwäsche-Skandale (mesma medida) | 12:05 | **3,1** | **18,6 s** |

- Medida: troca de cena = mudança grande do quadro inteiro (ffmpeg `scene > 0,3`). Nossas animações dentro da cena
  (texto entrando, batida de câmera) **não contam** aqui. Mesmo assim, a distância é grande: eles mudam o
  **cenário inteiro** a cada ~4 s; nós ficamos ~18 s no mesmo cenário.
- **Leitura:** a regra "algo novo a cada 3 s" que usamos está certa, mas o "novo" deles é uma **imagem nova
  inteira**, não um elemento a mais na mesma tela.

## 2. Como é cada cena (quadros de video-1.jpg)
- **Ilustração cheia, de borda a borda**: cenário completo (banco por dentro, cidade à noite, porão, mapa,
  escritório). Nunca fundo liso.
- **Personagens "palito de cabeça redonda":** cabeça grande e lisa, olhos de ponto, corpo de traço. Os mesmos tipos
  voltam: o **detetive de sobretudo com lupa** (0:42, 0:48, 1:24, 2:30, 2:48), o mafioso de terno risca de giz,
  o contador de bigode e os "dois amigos" (camisa vermelha e verde) que reagem.
- **Paleta escura e apagada** (dado: cinza-marrom #383534, #514c49, #1d1e1f, #706960 = ~80% do quadro), com
  **uma** cor de destaque por cena: o verde do dinheiro, o vermelho do carro ou da bandeira, o neon do lava-jato.
- **Texto na tela:** quase só **números e títulos de capítulo**, em caixa alta branca com sombra, embaixo e no
  centro: "$880,000,000", "$1.9 BILLION", "MONEY LAUNDERING", "1. PLACEMENT", "#1 THE CASH BUSINESS",
  "#2 SMURFING". Nada de parágrafo na tela.
- **Movimento:** a mesma imagem fica 2 quadros seguidos (~6 s) com leve aproximação; depois troca.
- **Capítulos numerados** ("#1", "#2"…) com o título grande na primeira imagem do capítulo.
- **Metáfora visual literal:** máquina de lavar para "lavagem", rio com pedras para "layering", mapa com setas
  para rotas de dinheiro.

## 3. Thumbs (thumbs.jpg; paleta das thumbs: laranja #e79913, verde-oliva, creme, azul-ciano #1dc0db)
- Fundo **laranja/amarelo com raios** (ou cor saturada lisa), oposto do vídeo escuro: a thumb grita, o vídeo é
  sóbrio.
- **Texto enorme**, branco com contorno preto, letra condensada, de 2 a 4 palavras; às vezes ocupa metade da imagem
  ("BROKE AT 85", "DAD WAS WRONG?").
- 1 ou 2 personagens com **expressão exagerada** (choro, susto, raiva), olhos grandes.
- Um objeto-símbolo grande: pilha de dinheiro, lupa, gangorra, lápide.
- A thumb **não repete o título**: completa ("Every Money Laundering Technique Explained" + "MONEY LAUNDERING 101").

## 4. O que aplicar no nosso canal (leitura; decidir com o dono)
1. **Mais trocas de cenário:** de 3,1 para perto de 15 por minuto. No motor: cenas mais curtas (~4 s), cada frase
   importante com um cenário próprio, em vez de um cenário que recebe elementos aos poucos.
2. **Cenário cheio:** cada cena com fundo desenhado (sala, rua, mapa), não papel liso.
3. **Texto na tela só para número e capítulo**, em caixa alta, embaixo, com sombra.
4. **Capítulos numerados** com título grande ("#1 …"). Já temos "Ebene 1…6": manter, no estilo deles.
5. **Thumb:** já refeita nesse estilo (13/11).
6. **Manter o que é nosso:** o traço desenhado à mão, o detetive (eles também usam um detetive de lupa, o que
   confirma o personagem) e a narração.

Atenção: o canal deles usa imagens geradas por IA. Nós desenhamos por código (é a nossa barreira de entrada).
Copiar o **ritmo e a gramática visual**, nunca as imagens.
