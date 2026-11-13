// Arte do canal: foto de perfil (logo) e banner. Mesmo estilo da thumb (raios laranja, detetive de olhos grandes).
(function () {
  const P = window.Pincel, A = window.Arte, INK = P.INK;

  // logo: detetive de busto, desconfiado, com a lupa. Desenha num quadrado de lado L com o canto em (x, y).
  function logo(ctx, x, y, L) {
    ctx.save(); ctx.translate(x, y); ctx.scale(L / 1080, L / 1080);
    ctx.beginPath(); ctx.rect(0, 0, 1080, 1080); ctx.clip();
    // fundo de raios só dentro do quadrado
    ctx.save();
    const cv = document.createElement("canvas"); cv.width = 1080; cv.height = 1080;
    A.raios(cv.getContext("2d"), 540, 520);
    ctx.drawImage(cv, 0, 0);
    ctx.restore();
    const s = 1.75, dx = 520, dy = 1500;
    ctx.save(); ctx.translate(dx, dy); ctx.scale(s, s);
    P.detetive(ctx, { respira: 0, incl: -0.05, olhar: [1, 0.1], pisca: 0, sobrancelha: 0, boca: -0.3, bocaO: 0, mao: 0, aponta: 1, zangado: 0.7, cocar: 0 }, 0);
    ctx.translate(0, -372); ctx.rotate(-0.05); ctx.translate(0, 372);
    A.olhoGrande(ctx, -38, -476, 32, 38, 12, 4, 801);
    A.olhoGrande(ctx, 40, -476, 32, 38, 12, 4, 802);
    P.traco(ctx, [[-82, -530], [-46, -526], [-10, -512]], { w: 13, seed: 803 });
    P.traco(ctx, [[10, -514], [46, -534], [82, -546]], { w: 13, seed: 804 });
    ctx.restore();
    const hx = dx + 330 * s, hy = dy - 370 * s;
    A.lupa(ctx, hx + 10, hy - 10, 870, 560, 150);
    A.brilho(ctx, 180, 250, 34); A.brilho(ctx, 960, 300, 28);
    ctx.restore();
  }

  window.Motor.T.perfil = (ctx) => {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    logo(ctx, 0, 0, 1080);
  };

  // banner 2560x1440: só a logo + "ABONNIEREN", dentro da área segura (1546x423 no centro)
  window.Motor.T.banner = (ctx) => {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    A.raios(ctx, 1280, 720);
    const L = 400, lx = 1280 - 640, ly = 720 - L / 2;
    // logo em círculo com borda
    ctx.save(); ctx.beginPath(); ctx.arc(lx + L / 2, ly + L / 2, L / 2, 0, 7); ctx.clip();
    logo(ctx, lx, ly, L);
    ctx.restore();
    ctx.lineWidth = 16; ctx.strokeStyle = "#111"; ctx.beginPath(); ctx.arc(lx + L / 2, ly + L / 2, L / 2, 0, 7); ctx.stroke();
    // botão "ABONNIEREN"
    const bx = 1110, by = 720 - 115, bw = 800, bh = 230;
    ctx.save();
    ctx.fillStyle = "rgba(0,0,0,.45)"; ctx.beginPath(); ctx.roundRect(bx + 12, by + 14, bw, bh, 60); ctx.fill();
    ctx.fillStyle = "#e3261c"; ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, 60); ctx.fill();
    ctx.lineWidth = 14; ctx.strokeStyle = "#111"; ctx.stroke();
    ctx.font = `400 190px ${A.FONTE}`; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.lineJoin = "round";
    ctx.lineWidth = 22; ctx.strokeStyle = "#111"; ctx.strokeText("ABONNIEREN", bx + bw / 2, by + bh / 2 + 8);
    ctx.fillStyle = "#fff"; ctx.fillText("ABONNIEREN", bx + bw / 2, by + bh / 2 + 8);
    ctx.restore();
  };
})();
