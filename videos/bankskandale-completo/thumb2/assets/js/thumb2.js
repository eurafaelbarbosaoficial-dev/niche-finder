// Thumbnail no estilo do canal modelado (Econ in a Nutshell): fundo de raios laranja/amarelo,
// letra branca gigante com contorno preto, personagens de olhos grandes e expressão exagerada.
// Desenhado à mão em Canvas 2D com o Pincel (sem imagem de IA).
(function () {
  const P = window.Pincel, C = P.COR, INK = P.INK;
  const W = 1920, H = 1080;
  const FONTE = '"League Gothic", "Oswald", sans-serif';

  function raios(ctx, cx, cy) {
    const W = ctx.canvas.width, H = ctx.canvas.height;
    const g = ctx.createRadialGradient(cx, cy, 80, cx, cy, 1500);
    g.addColorStop(0, "#ffe04a"); g.addColorStop(0.45, "#ffae1a"); g.addColorStop(1, "#f0561c");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    const n = 28;
    ctx.save(); ctx.globalAlpha = 0.22; ctx.fillStyle = "#fff6c8";
    for (let i = 0; i < n; i += 2) {
      const a0 = (i / n) * Math.PI * 2, a1 = ((i + 1) / n) * Math.PI * 2;
      ctx.beginPath(); ctx.moveTo(cx, cy);
      ctx.lineTo(cx + Math.cos(a0) * 3000, cy + Math.sin(a0) * 3000);
      ctx.lineTo(cx + Math.cos(a1) * 3000, cy + Math.sin(a1) * 3000);
      ctx.closePath(); ctx.fill();
    }
    ctx.restore();
    // bordas mais quentes (vinheta vermelha)
    const v = ctx.createRadialGradient(cx, cy, 500, cx, cy, 1400);
    v.addColorStop(0, "rgba(200,40,20,0)"); v.addColorStop(1, "rgba(170,30,15,0.55)");
    ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  }

  function nota(ctx, x, y, w, rot, seed, tinta) {
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
    const h = w * 0.48;
    P.forma(ctx, P.ret(-w / 2, -h / 2, w, h), { fill: tinta || "#7fc06a", sombra: "#4f8f45", seed, w: 4.5, sdx: -8, sdy: -6 });
    P.traco(ctx, P.ret(-w / 2 + 12, -h / 2 + 10, w - 24, h - 20), { w: 2.5, fechado: true, cor: "#3e7236", seed: seed + 1 });
    P.forma(ctx, P.elipse(0, 0, h * 0.32, h * 0.32, 12), { fill: "#b9e0a4", seed: seed + 2, w: 3 });
    ctx.font = `400 ${Math.round(h * 0.42)}px ${FONTE}`; ctx.fillStyle = "#2f5e2a"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText("€", 0, 2);
    ctx.restore();
  }

  function pilha(ctx, x, y, n, seed) { // maço de notas empilhadas (de lado)
    for (let i = 0; i < n; i++) {
      P.forma(ctx, P.ret(x - 90, y - i * 22, 180, 26), { fill: i % 2 ? "#7fc06a" : "#8fcf78", sombra: "#4f8f45", seed: seed + i, w: 4, sdx: -6, sdy: -4 });
    }
    P.forma(ctx, P.ret(x - 22, y - n * 22 + 6, 44, n * 22 + 16), { fill: "#f3ead8", seed: seed + 50, w: 3.5 });
  }

  function brilho(ctx, x, y, r) { // estrelinha de brilho
    ctx.save(); ctx.fillStyle = "#fffbe0"; ctx.beginPath();
    for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4, rr = i % 2 ? r * 0.28 : r; ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); }
    ctx.closePath(); ctx.fill(); ctx.restore();
  }

  // olhos grandes (estilo do canal modelado), em coordenadas locais do personagem
  function olhoGrande(ctx, x, y, rx, ry, px, py, seed) {
    P.forma(ctx, P.elipse(x, y, rx, ry, 16), { fill: "#ffffff", sombra: "#e4e0da", seed, w: 5.5, sdx: 6, sdy: 6 });
    ctx.fillStyle = INK; ctx.beginPath(); ctx.ellipse(x + px, y + py, rx * 0.42, ry * 0.42, 0, 0, 7); ctx.fill();
    ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(x + px - rx * 0.14, y + py - ry * 0.16, rx * 0.13, 0, 7); ctx.fill();
  }

  function gota(ctx, x, y, s, seed) { // gota de suor
    const pts = [[0, -26], [12, -4], [14, 10], [0, 20], [-14, 10], [-12, -4]].map(([a, b]) => [x + a * s, y + b * s]);
    P.forma(ctx, pts, { fill: "#8fd3f4", sombra: "#5fb2dc", brilho: "rgba(255,255,255,.6)", seed, w: 3.5 });
  }

  // banqueiro suando, abraçado a um saco de dinheiro. Origem = pés; ~800 px de altura em escala 1.
  function banqueiro(ctx, x, y, s) {
    const terno = "#2d3352", ternoS = "#1f2440", pele = "#f4d2b0", peleS = "#dcae86";
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    // pernas
    P.forma(ctx, P.ret(-110, -230, 90, 240), { fill: terno, sombra: ternoS, seed: 201 });
    P.forma(ctx, P.ret(20, -230, 90, 240), { fill: terno, sombra: ternoS, seed: 202 });
    // corpo (paletó risca de giz)
    const corpo = [[-185, -170], [-175, -420], [-120, -500], [-50, -520], [50, -520], [120, -500], [175, -420], [185, -170], [0, -150]];
    P.forma(ctx, corpo, { fill: terno, sombra: ternoS, brilho: "rgba(255,255,255,.08)", seed: 203, sdx: -40, sdy: -6 });
    ctx.save(); ctx.beginPath(); P.caminho(ctx, corpo, true); ctx.clip();
    for (let k = -170; k <= 170; k += 30) P.traco(ctx, [[k, -520], [k + 6, -150]], { w: 1.8, cor: "rgba(220,225,240,.45)", seed: 210 + k });
    ctx.restore();
    // camisa, gravata, colar de ouro
    P.forma(ctx, [[-52, -518], [52, -518], [0, -380]], { fill: "#f3ead8", seed: 220, w: 4.5 });
    P.forma(ctx, [[-14, -505], [14, -505], [22, -420], [0, -392], [-22, -420]], { fill: "#c9302c", sombra: "#8f1f1c", seed: 221, w: 4 });
    const colar = []; for (let i = 0; i <= 16; i++) { const a = Math.PI * (0.12 + i * 0.0475); colar.push([Math.cos(a) * 72, -515 + Math.sin(a) * 110]); }
    colar.forEach((p, i) => P.forma(ctx, P.elipse(p[0], p[1], 9, 7, 8), { fill: "#f2c230", sombra: "#c4921a", seed: 230 + i, w: 2.5 }));
    // cabeça
    P.forma(ctx, P.ret(-34, -560, 68, 50), { fill: peleS, seed: 240, w: 4.5 });
    P.forma(ctx, P.elipse(-112, -660, 22, 30, 9), { fill: pele, sombra: peleS, seed: 241 });
    P.forma(ctx, P.elipse(112, -660, 22, 30, 9), { fill: peleS, seed: 242 });
    const cab = P.elipse(0, -680, 118, 128, 20);
    P.forma(ctx, cab, { fill: pele, sombra: peleS, brilho: "rgba(255,250,240,.35)", seed: 243, sdx: -24, sdy: -14 });
    // cabelo penteado para trás (preto, brilhante)
    P.forma(ctx, [[-120, -690], [-126, -760], [-90, -810], [-20, -830], [60, -822], [112, -786], [124, -720], [112, -700], [90, -760], [30, -786], [-40, -780], [-96, -742]], { fill: "#1b1a22", brilho: "rgba(255,255,255,.18)", seed: 244 });
    P.traco(ctx, [[-60, -800], [10, -812], [80, -795]], { w: 3, cor: "rgba(255,255,255,.45)", seed: 245 });
    // olhos enormes de pânico
    olhoGrande(ctx, -44, -688, 40, 48, -10, 6, 250);
    olhoGrande(ctx, 46, -688, 40, 48, -12, 6, 251);
    P.traco(ctx, [[-92, -744], [-54, -758], [-16, -784]], { w: 9, seed: 252 });
    P.traco(ctx, [[16, -784], [54, -758], [94, -744]], { w: 9, seed: 253 });
    // boca de medo (aberta, tremida)
    P.forma(ctx, [[-44, -598], [-22, -612], [0, -604], [22, -614], [44, -598], [30, -578], [0, -572], [-30, -578]], { fill: "#5a2a22", seed: 254, w: 5 });
    P.forma(ctx, [[-30, -600], [30, -602], [26, -592], [-26, -590]], { fill: "#fffaf0", seed: 255, w: 2.5 });
    P.brilhoSuave(ctx, -76, -632, 28, "rgba(214,110,80,0.30)");
    P.brilhoSuave(ctx, 80, -632, 28, "rgba(214,110,80,0.30)");
    // suor
    gota(ctx, -150, -760, 1.4, 260); gota(ctx, 150, -730, 1.2, 261); gota(ctx, 172, -640, 0.9, 262); gota(ctx, -168, -650, 1.0, 263);
    // saco de dinheiro abraçado
    const saco = [[-150, -170], [-170, -280], [-120, -380], [-50, -410], [-70, -450], [-20, -470], [20, -470], [70, -450], [50, -410], [120, -380], [170, -280], [150, -170], [0, -150]];
    P.forma(ctx, saco, { fill: "#c9a46a", sombra: "#9c7a40", brilho: "rgba(255,240,200,.25)", seed: 270, sdx: -30 });
    P.traco(ctx, [[-56, -412], [0, -400], [56, -412]], { w: 8, cor: "#6d5232", seed: 271 });
    ctx.font = `400 170px ${FONTE}`; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.lineWidth = 14; ctx.lineJoin = "round"; ctx.strokeStyle = INK; ctx.strokeText("€", 0, -270);
    ctx.fillStyle = "#f2c230"; ctx.fillText("€", 0, -270);
    // braços abraçando o saco
    P.membro(ctx, [[-170, -460], [-200, -330], [-110, -300]], 60, terno, 280, ternoS);
    P.membro(ctx, [[170, -460], [200, -330], [110, -300]], 60, terno, 281, ternoS);
    P.forma(ctx, P.elipse(-96, -300, 30, 28, 10), { fill: pele, sombra: peleS, seed: 282 });
    P.forma(ctx, P.elipse(96, -300, 30, 28, 10), { fill: pele, sombra: peleS, seed: 283 });
    ctx.restore();
  }

  function lupa(ctx, hx, hy, cx, cy, r) {
    // cabo
    P.membro(ctx, [[hx, hy], [cx - (cx - hx) * 0.45, cy - (cy - hy) * 0.45]], 34, "#6b3f22", 301, "#4c2c17");
    // vidro com o "achado": dinheiro vermelho (sujo) ampliado
    ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, r, 0, 7); ctx.clip();
    const g = ctx.createRadialGradient(cx, cy, 10, cx, cy, r);
    g.addColorStop(0, "#ff7a5a"); g.addColorStop(1, "#c9201a");
    ctx.fillStyle = g; ctx.fillRect(cx - r, cy - r, 2 * r, 2 * r);
    for (let i = 0; i < 5; i++) nota(ctx, cx - 60 + (i % 2) * 70, cy + 90 - i * 52, 230, -0.15 + i * 0.07, 310 + i * 5, "#e2544a");
    P.brilhoSuave(ctx, cx, cy, r * 0.9, "rgba(255,90,40,.45)");
    ctx.fillStyle = "rgba(255,255,255,.28)"; ctx.beginPath(); ctx.ellipse(cx - r * 0.38, cy - r * 0.42, r * 0.34, r * 0.16, -0.7, 0, 7); ctx.fill();
    ctx.restore();
    // aro
    P.traco(ctx, P.elipse(cx, cy, r + 8, r + 8, 40), { w: 22, fechado: true, cor: "#3a3540", seed: 340 });
    P.traco(ctx, P.elipse(cx, cy, r + 8, r + 8, 40), { w: 6, fechado: true, cor: "#8c8698", seed: 341 });
    P.traco(ctx, P.elipse(cx, cy, r + 22, r + 22, 40), { w: 6, fechado: true, seed: 342 });
  }

  function titulo(ctx, txt, y, maxW, maxTam) {
    let tam = maxTam;
    ctx.font = `400 ${tam}px ${FONTE}`;
    while (ctx.measureText(txt).width > maxW && tam > 60) { tam -= 4; ctx.font = `400 ${tam}px ${FONTE}`; }
    ctx.save(); ctx.textAlign = "center"; ctx.textBaseline = "alphabetic"; ctx.lineJoin = "round";
    ctx.fillStyle = "rgba(0,0,0,.45)"; ctx.fillText(txt, W / 2 + 10, y + 12);
    ctx.lineWidth = tam * 0.16; ctx.strokeStyle = "#111"; ctx.strokeText(txt, W / 2, y);
    ctx.fillStyle = "#ffffff"; ctx.fillText(txt, W / 2, y);
    ctx.restore();
    return tam;
  }

  window.Arte = { raios, olhoGrande, lupa, brilho, nota, FONTE };
  window.Motor.T.thumb2 = (ctx, c, lt, t) => {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    raios(ctx, 980, 600);
    // prédio do banco ao fundo (sem logotipo)
    ctx.save(); ctx.translate(1490, 690); ctx.scale(3.0, 3.0);
    P.forma(ctx, P.poli([[-120, -60], [0, -130], [120, -60]], 30), { fill: "#efe6d2", sombra: "#cfc3a8", seed: 401 });
    P.forma(ctx, P.ret(-128, -66, 256, 16), { fill: "#d8cdb5", seed: 402, w: 4 });
    [-90, -45, 0, 45, 90].forEach((cx, i) => P.forma(ctx, P.ret(cx - 13, -50, 26, 118), { fill: "#fbf7ee", sombra: "#d8cdb5", seed: 403 + i, w: 3.5 }));
    P.forma(ctx, P.ret(-140, 68, 280, 26), { fill: "#d8cdb5", sombra: "#b9ab8e", seed: 410 });
    ctx.restore();
    // monte de dinheiro no chão
    for (let i = 0; i < 26; i++) {
      const r = P.rng(500 + i), x = 1080 + r() * 860, y = 900 + r() * 200;
      nota(ctx, x, y, 170 + r() * 50, (r() - 0.5) * 1.2, 520 + i * 3);
    }
    pilha(ctx, 1150, 1000, 7, 600); pilha(ctx, 1860, 980, 8, 620);
    for (let i = 0; i < 9; i++) { const r = P.rng(700 + i); P.moeda(ctx, 1100 + r() * 800, 950 + r() * 110, 36, r() * 3, 710 + i); }
    // banqueiro
    banqueiro(ctx, 1540, 1260, 1.08);
    // detetive zangado com a lupa
    const dx = 330, dy = 1300, ds = 1.25;
    ctx.save(); ctx.translate(dx, dy); ctx.scale(ds, ds);
    P.detetive(ctx, { respira: 0, incl: 0.04, olhar: [1, 0.2], pisca: 0, sobrancelha: 0, boca: -0.8, bocaO: 0, mao: 0, aponta: 1, zangado: 1, cocar: 0 }, 0);
    // olhos grandes por cima dos olhos pequenos (estilo do canal modelado)
    ctx.translate(0, -372); ctx.rotate(0.04); ctx.translate(0, 372);
    olhoGrande(ctx, -38, -476, 32, 38, 12, 4, 801);
    olhoGrande(ctx, 40, -476, 32, 38, 12, 4, 802);
    P.traco(ctx, [[-82, -534], [-46, -526], [-10, -508]], { w: 13, seed: 803 });
    P.traco(ctx, [[10, -508], [46, -526], [82, -534]], { w: 13, seed: 804 });
    ctx.restore();
    // mão do detetive (aponta=1) fica em (330,-370) local
    const hx = dx + 330 * ds, hy = dy - 370 * ds;
    lupa(ctx, hx + 20, hy - 10, 905, 560, 190);
    brilho(ctx, 1180, 420, 34); brilho(ctx, 700, 380, 26); brilho(ctx, 1830, 860, 30); brilho(ctx, 1060, 880, 22);
    // texto
    titulo(ctx, "DIE BANK WAR DER TÄTER", 250, 1840, 250);
  };
})();
