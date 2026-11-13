/* Pincel: biblioteca de desenho "feito à mão" em Canvas 2D para os vídeos do canal.
   Tudo é função do tempo t (determinístico): o mesmo t sempre desenha o mesmo quadro. */
(function () {
  const P = {};
  P.INK = "#2b2420";
  P.COR = {
    papel: "#efe6d2", ocre: "#d9a441", terracota: "#b8503a", ardosia: "#4a6a8a", ardosiaS: "#36506b",
    salvia: "#8aa66a", pele: "#efc8a0", peleS: "#d9a479", casaco: "#c99a5c", casacoS: "#a87a40",
    chapeu: "#3b3a45", chapeuS: "#2a2932", camisa: "#f3ead8", nuvem: "#fbf7ee",
  };

  P.rng = function (seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };
  P.quadro = (t, fps = 12) => Math.floor(t * fps + 1e-6);
  P.clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  P.seg = (t, a, b) => P.clamp((t - a) / (b - a), 0, 1);
  P.lerp = (a, b, u) => a + (b - a) * u;
  P.ease = {
    out: (u) => 1 - Math.pow(1 - u, 3),
    inOut: (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2),
    back: (u) => { const c1 = 2.2, c3 = c1 + 1; return 1 + c3 * Math.pow(u - 1, 3) + c1 * Math.pow(u - 1, 2); },
  };
  // valores-chave com transição suave: [[t, valor], ...]
  P.keyed = function (t, keys, dur = 0.3) {
    let v = keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      const [kt, kv] = keys[i];
      if (t < kt) break;
      const u = P.ease.inOut(P.clamp((t - kt) / dur, 0, 1));
      const prev = v;
      v = Array.isArray(kv) ? kv.map((x, j) => P.lerp(prev[j], x, u)) : P.lerp(prev, kv, u);
    }
    return v;
  };
  P.piscar = (t, tempos) => tempos.reduce((m, b) => Math.max(m, 1 - Math.abs(t - b) / 0.09), 0);

  P.jitter = (pts, amt, r) => pts.map((p) => [p[0] + (r() - 0.5) * 2 * amt, p[1] + (r() - 0.5) * 2 * amt]);
  P.elipse = (cx, cy, rx, ry, n = 14, rot = 0) => {
    const a = [];
    for (let i = 0; i < n; i++) { const th = rot + (i / n) * Math.PI * 2; a.push([cx + Math.cos(th) * rx, cy + Math.sin(th) * ry]); }
    return a;
  };

  // amostra uma curva suave (Catmull-Rom) passando pelos pontos
  P.amostrar = function (pts, fechado, per = 8) {
    const n = pts.length, out = [], N = fechado ? n : n - 1;
    for (let i = 0; i < N; i++) {
      const p0 = pts[(i - 1 + n) % n], p1 = pts[i], p2 = pts[(i + 1) % n], p3 = pts[(i + 2) % n];
      const q0 = !fechado && i === 0 ? p1 : p0, q3 = !fechado && i + 2 >= n ? p2 : p3;
      for (let k = 0; k < per; k++) {
        const t = k / per, t2 = t * t, t3 = t2 * t;
        out.push([0, 1].map((j) => 0.5 * (2 * p1[j] + (-q0[j] + p2[j]) * t + (2 * q0[j] - 5 * p1[j] + 4 * p2[j] - q3[j]) * t2 + (-q0[j] + 3 * p1[j] - 3 * p2[j] + q3[j]) * t3)));
      }
    }
    out.push(fechado ? out[0] : pts[n - 1]);
    return out;
  };
  P.caminho = function (ctx, pts, fechado) {
    const s = P.amostrar(pts, fechado, 6);
    ctx.moveTo(s[0][0], s[0][1]);
    for (let i = 1; i < s.length; i++) ctx.lineTo(s[i][0], s[i][1]);
    if (fechado) ctx.closePath();
  };

  // traço de pincel: espessura variável, pontas afinadas quando aberto
  P.traco = function (ctx, pts, o = {}) {
    const fechado = !!o.fechado;
    const s = P.amostrar(pts, fechado, o.per || 8);
    const r = P.rng(o.seed || 3), w = o.w || 6, L = s.length, ph = r() * 6.28;
    const PF = window.PerfectFreehand;
    if (PF && L > 2) {
      // traço com pressão (perfect-freehand): contorno preenchido, mais liso que segmentos
      const inp = s.map((p, i) => {
        const u = i / (L - 1);
        return [p[0], p[1], P.clamp(0.5 + 0.22 * Math.sin(ph + u * 9) + (r() - 0.5) * 0.08, 0.15, 1)];
      });
      const out = PF.getStroke(inp, {
        size: w * 1.35, thinning: 0.5, smoothing: 0.6, streamline: 0.2, simulatePressure: false, last: true,
        start: { taper: fechado ? 0 : w * 5, cap: true }, end: { taper: fechado ? 0 : w * 5, cap: true },
      });
      if (out.length > 2) {
        ctx.save();
        if (o.alpha != null) ctx.globalAlpha = o.alpha;
        ctx.fillStyle = o.cor || P.INK;
        ctx.beginPath(); ctx.moveTo(out[0][0], out[0][1]);
        for (let i = 1; i < out.length; i++) ctx.lineTo(out[i][0], out[i][1]);
        ctx.closePath(); ctx.fill();
        ctx.restore();
      }
      return;
    }
    ctx.save();
    ctx.strokeStyle = o.cor || P.INK; ctx.lineCap = "round"; ctx.lineJoin = "round";
    if (o.alpha != null) ctx.globalAlpha = o.alpha;
    for (let i = 0; i < L - 1; i++) {
      const u = i / (L - 1);
      let k = 0.8 + 0.3 * Math.sin(ph + u * 9) + (r() - 0.5) * 0.12;
      if (!fechado) k *= Math.min(1, 0.3 + Math.sin(Math.PI * u) * 1.4);
      ctx.lineWidth = Math.max(0.8, w * k);
      ctx.beginPath(); ctx.moveTo(s[i][0], s[i][1]); ctx.lineTo(s[i + 1][0], s[i + 1][1]); ctx.stroke();
    }
    ctx.restore();
  };

  // forma: preenchimento + sombra de luz única (vinda de cima/esquerda) + contorno vivo
  P.forma = function (ctx, pts, o = {}) {
    const r = P.rng(o.seed || 1);
    const jp = P.jitter(pts, o.boil ?? 1.4, r);
    ctx.save();
    if (o.fill) {
      ctx.beginPath(); P.caminho(ctx, jp, true); ctx.fillStyle = o.fill; ctx.fill();
      if (o.sombra) {
        ctx.save(); ctx.clip();
        ctx.beginPath(); P.caminho(ctx, jp.map((p) => [p[0] + (o.sdx ?? -16), p[1] + (o.sdy ?? -12)]), true);
        ctx.rect(-1e4, -1e4, 2e4, 2e4); ctx.fillStyle = o.sombra; ctx.fill("evenodd");
        ctx.restore();
      }
      if (o.brilho) {
        ctx.save(); ctx.beginPath(); P.caminho(ctx, jp, true); ctx.clip();
        ctx.beginPath(); P.caminho(ctx, jp.map((p) => [p[0] + 10, p[1] + 9]), true);
        ctx.rect(-1e4, -1e4, 2e4, 2e4); ctx.fillStyle = o.brilho; ctx.fill("evenodd");
        ctx.restore();
      }
    }
    if (o.ink !== false) P.traco(ctx, jp, { w: o.w ?? 5.5, cor: o.inkCor, fechado: true, seed: (o.seed || 1) + 7 });
    ctx.restore();
  };

  // membro grosso (manga) com contorno
  P.membro = function (ctx, pts, w, cor, seed, sombra) {
    const jp = P.jitter(pts, 1.2, P.rng(seed));
    ctx.save(); ctx.lineCap = "round"; ctx.lineJoin = "round";
    ctx.beginPath(); P.caminho(ctx, jp, false); ctx.strokeStyle = P.INK; ctx.lineWidth = w + 11; ctx.stroke();
    ctx.beginPath(); P.caminho(ctx, jp, false); ctx.strokeStyle = cor; ctx.lineWidth = w; ctx.stroke();
    if (sombra) {
      ctx.beginPath(); P.caminho(ctx, jp.map((p) => [p[0] + w * 0.22, p[1] + w * 0.1]), false);
      ctx.strokeStyle = sombra; ctx.lineWidth = w * 0.4; ctx.stroke();
    }
    ctx.restore();
  };

  // papel: grão + manchas, gerado uma vez (semente fixa)
  P.papel = function (w, h, base) {
    const c = document.createElement("canvas"); c.width = w; c.height = h;
    const x = c.getContext("2d");
    x.fillStyle = base || P.COR.papel; x.fillRect(0, 0, w, h);
    const r = P.rng(99);
    for (let i = 0; i < 26; i++) {
      const cx = r() * w, cy = r() * h, rad = 80 + r() * 320;
      const g = x.createRadialGradient(cx, cy, 0, cx, cy, rad);
      const a = 0.012 + r() * 0.018;
      g.addColorStop(0, r() > 0.5 ? `rgba(150,110,60,${a})` : `rgba(255,250,235,${a * 1.5})`); g.addColorStop(1, "rgba(0,0,0,0)");
      x.fillStyle = g; x.fillRect(cx - rad, cy - rad, rad * 2, rad * 2);
    }
    const img = x.getImageData(0, 0, w, h), d = img.data;
    for (let i = 0; i < d.length; i += 4) { const n = (r() - 0.5) * 11; d[i] += n; d[i + 1] += n; d[i + 2] += n * 0.9; }
    x.putImageData(img, 0, 0);
    x.strokeStyle = "rgba(120,90,50,0.06)"; x.lineWidth = 1;
    for (let i = 0; i < 260; i++) { const fx = r() * w, fy = r() * h, a = r() * 6.28, l = 6 + r() * 22; x.beginPath(); x.moveTo(fx, fy); x.lineTo(fx + Math.cos(a) * l, fy + Math.sin(a) * l); x.stroke(); }
    return c;
  };
  P.vinheta = function (ctx, w, h, forca = 0.22) {
    const g = ctx.createRadialGradient(w / 2, h / 2, h * 0.35, w / 2, h / 2, h * 1.05);
    g.addColorStop(0, "rgba(60,40,20,0)"); g.addColorStop(1, `rgba(60,40,20,${forca})`);
    ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
  };
  P.brilhoSuave = function (ctx, x, y, r, cor) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, cor); g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2);
  };

  // nuvem de pensamento
  P.nuvem = function (ctx, cx, cy, rx, ry, seed) {
    const r = P.rng(seed), n = 9, puffs = [];
    for (let i = 0; i < n; i++) {
      const th = (i / n) * Math.PI * 2 + r() * 0.2;
      const pr = ry * (0.42 + r() * 0.12);
      puffs.push([cx + Math.cos(th) * (rx - pr * 0.55), cy + Math.sin(th) * (ry - pr * 0.55), pr]);
    }
    ctx.save();
    ctx.fillStyle = "rgba(70,45,20,0.13)";
    puffs.forEach(([x, y, pr]) => { ctx.beginPath(); ctx.arc(x + 9, y + 12, pr, 0, 7); ctx.fill(); });
    ctx.beginPath(); ctx.ellipse(cx + 9, cy + 12, rx * 0.8, ry * 0.8, 0, 0, 7); ctx.fill();
    puffs.forEach(([x, y, pr], i) => P.traco(ctx, P.elipse(x, y, pr, pr, 12), { w: 6, fechado: true, seed: seed * 7 + i }));
    ctx.fillStyle = P.COR.nuvem;
    puffs.forEach(([x, y, pr]) => { ctx.beginPath(); ctx.arc(x, y, pr - 0.5, 0, 7); ctx.fill(); });
    ctx.beginPath(); ctx.ellipse(cx, cy, rx * 0.8, ry * 0.8, 0, 0, 7); ctx.fill();
    ctx.restore();
  };

  /* Detetive (personagem fixo do canal). Origem = centro dos pés; altura ~ 700 px em escala 1.
     st: { respira, incl, olhar:[x,y], pisca 0..1, sobrancelha 0..1, boca -1..1, mao 0..1, cocar 0..1 } */
  P.detetive = function (ctx, st, t) {
    const C = P.COR, f = P.quadro(t), sd = (k) => f * 131 + k * 17;
    const resp = (st.respira || 0) * 4;
    // braço de trás
    P.membro(ctx, [[-128, -318 + resp], [-158, -200], [-166, -80]], 62, C.casaco, sd(1), C.casacoS);
    P.forma(ctx, P.elipse(-166, -66, 27, 25, 10), { fill: C.pele, sombra: C.peleS, seed: sd(2) });
    // corpo
    ctx.save();
    ctx.translate(0, -150); ctx.rotate((st.inclCorpo || 0)); ctx.translate(0, 150);
    const corpo = [[-178, 60], [-165, -190], [-148, -322 + resp], [-62, -368 + resp], [62, -368 + resp], [148, -322 + resp], [165, -190], [178, 60]];
    P.forma(ctx, corpo, { fill: C.casaco, sombra: C.casacoS, brilho: "rgba(255,240,210,0.25)", seed: sd(3), sdx: -46, sdy: -6 });
    P.forma(ctx, [[-56, -364 + resp], [56, -364 + resp], [0, -238]], { fill: C.camisa, sombra: "#ddd0b6", seed: sd(4), w: 4.5 });
    P.forma(ctx, [[-13, -350], [13, -350], [21, -268], [0, -240], [-21, -268]], { fill: C.terracota, sombra: "#963d2b", seed: sd(5), w: 4 });
    P.forma(ctx, [[-62, -368 + resp], [-118, -340], [-74, -290], [-14, -318]], { fill: C.casaco, sombra: C.casacoS, seed: sd(6), w: 5 });
    P.forma(ctx, [[62, -368 + resp], [118, -340], [74, -290], [14, -318]], { fill: C.casaco, sombra: C.casacoS, seed: sd(7), w: 5 });
    P.traco(ctx, [[-70, -292], [-34, -236], [-8, -200]], { w: 4.5, seed: sd(8) });
    P.traco(ctx, [[70, -292], [34, -236], [8, -200]], { w: 4.5, seed: sd(9) });
    P.forma(ctx, [[-168, -150], [168, -150], [170, -116], [-170, -116]], { fill: C.casacoS, seed: sd(10), w: 5 });
    P.forma(ctx, [[-22, -156], [22, -156], [22, -110], [-22, -110]], { fill: C.ocre, sombra: "#b98a2f", seed: sd(11), w: 4.5 });
    [[-60, -190], [60, -190], [-60, -60], [60, -60]].forEach(([x, y], i) => P.forma(ctx, P.elipse(x, y, 9, 9, 8), { fill: "#6d5232", seed: sd(12 + i), w: 3.5 }));
    ctx.restore();

    // cabeça (gira a partir do pescoço; vem antes do corpo)
    ctx.save();
    ctx.translate(0, -372 + resp); ctx.rotate(st.incl || 0); ctx.translate(0, 372 - resp);
    ctx.translate(0, resp * 0.8);
    P.forma(ctx, [[-30, -410], [30, -410], [32, -360], [-32, -360]], { fill: C.peleS, seed: sd(20), w: 4.5 });
    P.forma(ctx, P.elipse(-99, -468, 19, 26, 9), { fill: C.pele, sombra: C.peleS, seed: sd(21) });
    P.forma(ctx, P.elipse(99, -468, 19, 26, 9), { fill: C.peleS, seed: sd(22) });
    const cabeca = P.elipse(0, -478, 101, 110, 18);
    P.forma(ctx, cabeca, { fill: C.pele, sombra: C.peleS, brilho: "rgba(255,245,230,0.35)", seed: sd(23), sdx: -26, sdy: -14 });
    // sombra da aba no rosto
    ctx.save(); ctx.beginPath(); P.caminho(ctx, cabeca, true); ctx.clip();
    ctx.fillStyle = "rgba(90,50,30,0.16)"; ctx.beginPath(); ctx.ellipse(6, -548, 120, 34, 0, 0, 7); ctx.fill(); ctx.restore();
    // bochechas
    P.brilhoSuave(ctx, -58, -440, 30, "rgba(214,110,80,0.28)");
    P.brilhoSuave(ctx, 58, -440, 30, "rgba(214,110,80,0.28)");
    // olhos
    const [lx, ly] = st.olhar || [0, 0];
    const pis = P.clamp(st.pisca || 0, 0, 1);
    [-38, 38].forEach((ex, i) => {
      const x = ex + lx * 10, y = -478 + ly * 7;
      if (pis > 0.75) { P.traco(ctx, [[x - 13, y + 2], [x, y + 6], [x + 13, y + 2]], { w: 5, seed: sd(30 + i) }); return; }
      ctx.fillStyle = P.INK; ctx.beginPath(); ctx.ellipse(x, y, 10.5, 15 * (1 - pis * 0.85), 0, 0, 7); ctx.fill();
      ctx.fillStyle = "#fffaf0"; ctx.beginPath(); ctx.arc(x - 3.5, y - 5 * (1 - pis), 3.4, 0, 7); ctx.fill();
    });
    // sobrancelhas
    const sb = st.sobrancelha || 0, zang = st.zangado || 0;
    P.traco(ctx, [[-64, -516 - sb * 14 + zang * 6], [-40, -526 - sb * 18], [-16, -521 - sb * 12 + zang * 12]], { w: 8.5, seed: sd(33) });
    P.traco(ctx, [[16, -521 - sb * 10 + zang * 12], [40, -526 - sb * 14], [64, -516 - sb * 10 + zang * 6]], { w: 8.5, seed: sd(34) });
    // nariz e boca
    P.traco(ctx, [[4, -468], [17, -446], [3, -437]], { w: 5, seed: sd(35) });
    const b = st.boca || 0, bo = P.clamp(st.bocaO || 0, 0, 1);
    if (bo > 0.3) P.forma(ctx, P.elipse(0, -412, 13 + bo * 4, 9 + bo * 12, 10), { fill: "#5a2a22", seed: sd(36), w: 5 });
    else P.traco(ctx, [[-30, -412 - b * 4], [-2, -409 + b * 12], [30, -414 - b * 6]], { w: 6, seed: sd(36) });
    // chapéu
    P.forma(ctx, [[-90, -556], [-95, -612], [-66, -652], [-8, -636], [0, -628], [8, -636], [66, -652], [95, -612], [90, -556]], { fill: C.chapeu, sombra: C.chapeuS, brilho: "rgba(255,255,255,0.10)", seed: sd(40), sdx: -24 });
    P.forma(ctx, [[-91, -553], [91, -553], [93, -584], [-93, -584]], { fill: C.terracota, sombra: "#963d2b", seed: sd(41), w: 4.5 });
    P.forma(ctx, [[-168, -544], [-92, -560], [0, -563], [92, -560], [168, -544], [96, -526], [0, -521], [-96, -526]], { fill: C.chapeu, sombra: C.chapeuS, seed: sd(42), sdx: 0, sdy: -9 });
    ctx.restore();

    // braço da frente (mão no queixo)
    const m = P.clamp(st.mao || 0, 0, 1), me = P.ease.inOut(m);
    const ap = P.ease.inOut(P.clamp(st.aponta || 0, 0, 1));
    const coc = (st.cocar || 0) * Math.sin(t * 22) * 5;
    let cot = [P.lerp(166, 182, me), P.lerp(-190, -255, me)];
    let mao = [P.lerp(172, 58, me) + coc, P.lerp(-74, -402, me) + coc * 0.4];
    if (ap > 0) { // braço esticado apontando para a direita (para o que a narração mostra)
      cot = [P.lerp(cot[0], 250, ap), P.lerp(cot[1], -300, ap)];
      mao = [P.lerp(mao[0], 330, ap), P.lerp(mao[1], -370, ap)];
    }
    P.membro(ctx, [[128, -318 + resp], cot, [P.lerp(mao[0], mao[0] + 22, 0.5), mao[1] + 30 * (1 - me) + 18 * me]], 62, C.casaco, sd(50), C.casacoS);
    P.forma(ctx, P.elipse(mao[0], mao[1], 29, 27, 10), { fill: C.pele, sombra: C.peleS, seed: sd(51) });
    if (me > 0.5 && ap < 0.5) P.traco(ctx, [[mao[0] - 18, mao[1] - 10], [mao[0] - 26, mao[1] - 28], [mao[0] - 18, mao[1] - 40]], { w: 5, seed: sd(52) });
    if (ap > 0.5) { P.membro(ctx, [[mao[0] + 10, mao[1] - 4], [mao[0] + 44, mao[1] - 14]], 12, C.pele, sd(53)); }
  };

  // retângulo com cantos levemente arredondados (lados retos)
  // polígono com lados retos: insere pontos ao longo de cada lado (a curva suave não "estufa")
  P.poli = (cantos, passo = 34) => {
    const out = [];
    for (let i = 0; i < cantos.length; i++) {
      const a = cantos[i], b = cantos[(i + 1) % cantos.length];
      const n = Math.max(1, Math.round(Math.hypot(b[0] - a[0], b[1] - a[1]) / passo));
      for (let k = 0; k < n; k++) out.push([P.lerp(a[0], b[0], k / n), P.lerp(a[1], b[1], k / n)]);
    }
    return out;
  };
  P.linha = (pts, passo = 10) => { const c = P.poli(pts, passo), fim = pts[pts.length - 1]; const k = c.findIndex((p, i) => i > 0 && p[0] === fim[0] && p[1] === fim[1]); return (k > 0 ? c.slice(0, k + 1) : c); };
  P.ret = (x, y, w, h) => P.poli([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], Math.min(34, Math.max(6, Math.min(w, h) / 2)));
  // parte inicial de um traço (efeito "desenhando")
  P.parcial = (pts, u) => {
    if (u >= 1) return pts;
    const n = (pts.length - 1) * u, i = Math.floor(n), k = n - i;
    const out = pts.slice(0, i + 1);
    if (i + 1 < pts.length) out.push([P.lerp(pts[i][0], pts[i + 1][0], k), P.lerp(pts[i][1], pts[i + 1][1], k)]);
    return out;
  };
  P.tremor = (t, t0, dur, amp, seed = 1) => {
    const u = P.seg(t, t0, t0 + dur);
    if (u <= 0 || u >= 1) return [0, 0];
    const d = Math.pow(1 - u, 2) * amp;
    return [Math.sin(t * 91 + seed) * d, Math.cos(t * 73 + seed * 2) * d];
  };

  // moeda de euro girando
  P.moeda = function (ctx, x, y, r, giro, seed) {
    const sx = Math.max(0.12, Math.abs(Math.cos(giro)));
    ctx.save(); ctx.translate(x, y); ctx.scale(sx, 1);
    P.forma(ctx, P.elipse(0, 0, r, r, 14), { fill: "#e3b44c", sombra: "#b98a2f", brilho: "rgba(255,245,200,.45)", seed, w: 4.5, sdx: -r * 0.25, sdy: -r * 0.18 });
    P.traco(ctx, P.elipse(0, 0, r * 0.74, r * 0.74, 14), { w: 2.5, fechado: true, cor: "#9a7020", seed: seed + 1 });
    if (sx > 0.45) {
      const arco = []; for (let i = 0; i <= 10; i++) { const a = Math.PI * (0.28 + i * 0.144); arco.push([r * 0.08 + Math.cos(a) * r * 0.42, Math.sin(a) * r * 0.42]); }
      P.traco(ctx, arco, { w: 4.5, seed: seed + 2, cor: "#6b4a12" });
      P.traco(ctx, [[-r * 0.46, -r * 0.1], [r * 0.12, -r * 0.1]], { w: 3.5, seed: seed + 3, cor: "#6b4a12" });
      P.traco(ctx, [[-r * 0.46, r * 0.12], [r * 0.1, r * 0.12]], { w: 3.5, seed: seed + 4, cor: "#6b4a12" });
    }
    ctx.restore();
  };

  // policial (figurante); origem = pés; ~300 px de altura
  P.policial = function (ctx, st, t, seed) {
    const r = P.rng(seed), f = P.quadro(t), sd = (k) => f * 97 + seed * 13 + k;
    const peles = ["#efc8a0", "#d9a074", "#b9805a", "#f3d2b3"], pele = peles[Math.floor(r() * 4)];
    const alt = 0.92 + r() * 0.14, bigode = r() > 0.6, larg = 0.95 + r() * 0.12;
    ctx.save(); ctx.scale(larg, alt);
    const resp = (st.respira || 0) * 3;
    P.membro(ctx, [[-52, -200 + resp], [-62, -130], [-60, -70]], 30, "#33415e", sd(1), "#26324a");
    P.membro(ctx, [[52, -200 + resp], [62, -130], [60, -70]], 30, "#33415e", sd(2), "#26324a");
    P.forma(ctx, [[-58, 10], [-56, -150], [-50, -205 + resp], [-20, -222 + resp], [20, -222 + resp], [50, -205 + resp], [56, -150], [58, 10]], { fill: "#3b4a6b", sombra: "#2a3550", brilho: "rgba(255,255,255,.12)", seed: sd(3), sdx: -18, w: 5 });
    P.forma(ctx, P.ret(-58, -96, 116, 16, 4), { fill: "#1f2433", seed: sd(4), w: 4 });
    P.forma(ctx, P.ret(-34, -190, 22, 16, 3), { fill: "#e3b44c", seed: sd(5), w: 3 });
    [-60, 60].forEach((x, i) => P.forma(ctx, P.elipse(x, -64, 13, 12, 8), { fill: pele, sombra: "rgba(0,0,0,.15)", seed: sd(6 + i), w: 3.5 }));
    ctx.translate(0, resp * 0.6);
    P.forma(ctx, P.elipse(0, -268, 44, 48, 14), { fill: pele, sombra: "rgba(120,60,30,.22)", seed: sd(8), w: 5, sdx: -12 });
    const pis = P.piscar(t, st.piscadas || []);
    [-15, 15].forEach((x) => {
      if (pis > 0.7) { P.traco(ctx, [[x - 6, -268], [x + 6, -268]], { w: 3, seed: sd(9) }); return; }
      ctx.fillStyle = P.INK; ctx.beginPath(); ctx.ellipse(x + (st.olharX || 0) * 4, -268, 4.5, 6.5, 0, 0, 7); ctx.fill();
    });
    if (bigode) P.traco(ctx, [[-16, -246], [0, -250], [16, -246]], { w: 7, seed: sd(10), cor: "#4a3426" });
    else P.traco(ctx, [[-10, -244], [0, -241], [10, -244]], { w: 3.5, seed: sd(10) });
    P.forma(ctx, [[-46, -294], [-40, -330], [0, -340], [40, -330], [46, -294]], { fill: "#2f3b57", sombra: "#202a40", seed: sd(11), w: 5 });
    P.forma(ctx, [[-50, -296], [50, -296], [44, -282], [-30, -280]], { fill: "#14171f", seed: sd(12), w: 4 });
    P.forma(ctx, P.elipse(0, -316, 9, 10, 8), { fill: "#e3b44c", seed: sd(13), w: 3 });
    ctx.restore();
  };

  // prédio/casa; origem = base esquerda
  P.casa = function (ctx, x, y, w, h, cor, sombra, seed, t, telhado) {
    const r = P.rng(seed), f = P.quadro(t), sd = (k) => f * 59 + seed * 11 + k;
    P.forma(ctx, P.ret(x, y - h, w, h, 4), { fill: cor, sombra, brilho: "rgba(255,250,235,.22)", seed: sd(1), sdx: -w * 0.18, sdy: 0 });
    if (telhado === "agudo") P.forma(ctx, P.poli([[x - 12, y - h + 4], [x + w / 2, y - h - w * 0.42], [x + w + 12, y - h + 4]], 30), { fill: "#9c4632", sombra: "#7d3524", seed: sd(2) });
    else P.forma(ctx, P.ret(x - 8, y - h - 14, w + 16, 18, 3), { fill: "#5a4a40", seed: sd(2), w: 4.5 });
    const cols = Math.max(2, Math.round(w / 52)), rows = Math.max(2, Math.round((h - 60) / 58));
    const gw = (w - 24) / cols;
    for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
      const lit = r() > 0.35;
      P.forma(ctx, P.ret(x + 12 + i * gw + gw * 0.18, y - h + 20 + j * 58, gw * 0.64, 34, 3), { fill: lit ? "#f6dc9a" : "#7d8aa6", seed: sd(10 + i * 9 + j), w: 3 });
    }
    P.forma(ctx, P.ret(x + w / 2 - 16, y - 48, 32, 48, 3), { fill: "#3d3029", seed: sd(5), w: 3.5 });
  };

  window.Pincel = P;
})();
