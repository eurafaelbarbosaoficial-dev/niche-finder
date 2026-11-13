// Arte do canal: foto de perfil (logo) e banner. Fundo próprio do canal (azul-noite com holofote),
// diferente do fundo laranja das thumbs.
(function () {
  const P = window.Pincel, A = window.Arte;

  function fundoCanal(ctx, cx, cy, W, H) {
    const g = ctx.createRadialGradient(cx, cy, 40, cx, cy, Math.max(W, H) * 0.75);
    g.addColorStop(0, "#3d5a9e"); g.addColorStop(0.45, "#22325f"); g.addColorStop(1, "#0d1226");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    // holofote suave + poeira de luz
    P.brilhoSuave(ctx, cx, cy, Math.min(W, H) * 0.45, "rgba(255,214,120,0.22)");
    const r = P.rng(77);
    ctx.fillStyle = "rgba(255,240,200,0.35)";
    for (let i = 0; i < 60; i++) { ctx.beginPath(); ctx.arc(r() * W, r() * H, 1.5 + r() * 3, 0, 7); ctx.fill(); }
  }

  const ROSTO = { respira: 0, incl: 0, olhar: [0, 0.1], pisca: 0, sobrancelha: 0.2, boca: 0.5, bocaO: 0, mao: 0, aponta: 0, zangado: 0, cocar: 0 };

  // versão "olhando para frente": olhos grandes, sorriso confiante
  function perfilFrente(ctx) {
    fundoCanal(ctx, 540, 470, 1080, 1080);
    const s = 1.85, dx = 540, dy = 1560;
    ctx.save(); ctx.translate(dx, dy); ctx.scale(s, s);
    P.detetive(ctx, ROSTO, 0);
    A.olhoGrande(ctx, -38, -476, 32, 38, 0, 4, 801);
    A.olhoGrande(ctx, 40, -476, 32, 38, 0, 4, 802);
    P.traco(ctx, [[-80, -528], [-46, -538], [-12, -530]], { w: 12, seed: 803 });
    P.traco(ctx, [[12, -530], [46, -538], [80, -528]], { w: 12, seed: 804 });
    ctx.restore();
  }

  // versão "lupa no olho": lupa na frente do olho direito, olho enorme ampliado
  function perfilLupa(ctx) {
    fundoCanal(ctx, 540, 470, 1080, 1080);
    const s = 1.85, dx = 540, dy = 1560;
    ctx.save(); ctx.translate(dx, dy); ctx.scale(s, s);
    P.detetive(ctx, Object.assign({}, ROSTO, { boca: 0.3 }), 0);
    A.olhoGrande(ctx, -38, -476, 30, 36, 0, 4, 801);
    P.traco(ctx, [[-80, -524], [-46, -534], [-12, -526]], { w: 12, seed: 803 });
    // braço da frente subindo até a lupa
    const C = P.COR;
    P.membro(ctx, [[128, -318], [235, -250], [175, -372]], 62, C.casaco, 820, C.casacoS);
    // cabo
    P.membro(ctx, [[168, -380], [100, -430]], 16, "#6b3f22", 821, "#4c2c17");
    P.forma(ctx, P.elipse(172, -382, 30, 28, 10), { fill: C.pele, sombra: C.peleS, seed: 822 });
    // lente com o olho ampliado
    const lx = 46, ly = -478, lr = 74;
    ctx.save(); ctx.beginPath(); ctx.arc(lx, ly, lr, 0, 7); ctx.clip();
    ctx.fillStyle = C.pele; ctx.fillRect(lx - lr, ly - lr, 2 * lr, 2 * lr);
    P.traco(ctx, [[lx - 52, ly - 60], [lx, ly - 76], [lx + 52, ly - 62]], { w: 16, seed: 823 });
    A.olhoGrande(ctx, lx, ly + 6, 50, 56, 0, 6, 824);
    ctx.fillStyle = "rgba(170,215,255,.18)"; ctx.fillRect(lx - lr, ly - lr, 2 * lr, 2 * lr);
    ctx.fillStyle = "rgba(255,255,255,.35)"; ctx.beginPath(); ctx.ellipse(lx - 30, ly - 36, 26, 11, -0.7, 0, 7); ctx.fill();
    ctx.restore();
    P.traco(ctx, P.elipse(lx, ly, lr + 4, lr + 4, 36), { w: 14, fechado: true, cor: "#3a3540", seed: 830 });
    P.traco(ctx, P.elipse(lx, ly, lr + 4, lr + 4, 36), { w: 4, fechado: true, cor: "#9a94a8", seed: 831 });
    ctx.restore();
  }

  window.Motor.T.perfil = (ctx) => { ctx.setTransform(1, 0, 0, 1, 0, 0); perfilFrente(ctx); };
  window.Motor.T.perfil2 = (ctx) => { ctx.setTransform(1, 0, 0, 1, 0, 0); perfilLupa(ctx); };

  // banner 2560x1440: mesmo fundo da logo, só "ABONNIEREN" no centro (área segura 1546x423)
  window.Motor.T.banner = (ctx) => {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    fundoCanal(ctx, 1280, 720, 2560, 1440);
    const bw = 880, bh = 240, bx = 1280 - bw / 2, by = 720 - bh / 2;
    ctx.save();
    ctx.fillStyle = "rgba(0,0,0,.45)"; ctx.beginPath(); ctx.roundRect(bx + 12, by + 14, bw, bh, 60); ctx.fill();
    ctx.fillStyle = "#e3261c"; ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, 60); ctx.fill();
    ctx.lineWidth = 14; ctx.strokeStyle = "#111"; ctx.stroke();
    ctx.font = `400 200px ${A.FONTE}`; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.lineJoin = "round";
    ctx.lineWidth = 22; ctx.strokeStyle = "#111"; ctx.strokeText("ABONNIEREN", 1280, 728);
    ctx.fillStyle = "#fff"; ctx.fillText("ABONNIEREN", 1280, 728);
    ctx.restore();
  };
})();
