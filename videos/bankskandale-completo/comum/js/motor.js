/* Motor de cenas do canal: desenha uma lista de cenas (geradas a partir do roteiro) em Canvas 2D com o Pincel.
   Cada cena: { t0, t1, tipo, ...parâmetros, passos: [segundos locais em que cada elemento entra] }.
   Tudo é função do tempo (determinístico). */
(function () {
  const P = window.Pincel, C = P.COR, INK = P.INK;
  const M = {};
  const W = 1920, H = 1080;
  let papel = null, papelNoite = null;
  const FONT_T = '"Playfair Display", serif', FONT_L = 'Inter, sans-serif';

  // ---------- utilidades ----------
  const seg = P.seg, ease = P.ease, clamp = P.clamp, lerp = P.lerp;
  const entra = (lt, t0, d = 0.45) => ease.out(seg(lt, t0, t0 + d));
  const pop = (lt, t0, d = 0.4) => ease.back(seg(lt, t0, t0 + d));
  const fmt = (v, casas = 0) => v.toLocaleString("de-DE", { minimumFractionDigits: casas, maximumFractionDigits: casas });

  function fundo(ctx, tipo) {
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    if (tipo === "noite") {
      ctx.fillStyle = "#1a2238"; ctx.fillRect(0, 0, W, H);
      P.brilhoSuave(ctx, 1000, 120, 1100, "rgba(64,86,135,0.7)");
    } else if (tipo === "agua") {
      const g = ctx.createLinearGradient(0, 0, 0, H);
      g.addColorStop(0, "#dfe9ee"); g.addColorStop(0.28, "#bcd3dd"); g.addColorStop(0.29, "#6f98b0"); g.addColorStop(1, "#1f3a55");
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    } else {
      ctx.drawImage(papel, 0, 0);
    }
    ctx.restore();
  }
  function textura(ctx, tipo) {
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    if (tipo === "noite" || tipo === "agua") {
      ctx.globalCompositeOperation = "overlay"; ctx.globalAlpha = 0.45; ctx.drawImage(papelNoite, 0, 0);
      ctx.globalCompositeOperation = "source-over"; ctx.globalAlpha = 1;
      P.vinheta(ctx, W, H, 0.45);
    } else P.vinheta(ctx, W, H, 0.24);
    ctx.restore();
  }

  // texto rico: *palavra* = itálico terracota; quebra de linha automática; revela palavra por palavra (u 0..1)
  function texto(ctx, str, x, y, o = {}) {
    const tam = o.tam || 80, lh = o.lh || tam * 1.12, maxW = o.maxW || 1500, cor = o.cor || INK;
    const peso = o.peso || 700, fam = o.fam || FONT_T, alinha = o.alinha || "left";
    const tokens = [];
    let ital = false;
    str.split(/\s+/).forEach((w) => {
      if (!w) return;
      let a = w, i0 = ital;
      if (a.startsWith("*")) { i0 = true; a = a.slice(1); }
      let fecha = false;
      if (a.endsWith("*")) { fecha = true; a = a.slice(0, -1); }
      else if (/\*[.,:;!?…]$/.test(a)) { fecha = true; a = a.replace("*", ""); }
      tokens.push({ w: a, it: i0 });
      ital = fecha ? false : i0;
    });
    const fonte = (it) => `${it ? "italic " : ""}${peso} ${tam}px ${fam}`;
    const linhas = [[]];
    let lw = 0;
    ctx.textAlign = "left";
    const esp = (() => { ctx.font = fonte(false); return ctx.measureText(" ").width; })();
    tokens.forEach((tk) => {
      ctx.font = fonte(tk.it); tk.larg = ctx.measureText(tk.w).width;
      if (lw + tk.larg > maxW && linhas[linhas.length - 1].length) { linhas.push([]); lw = 0; }
      linhas[linhas.length - 1].push(tk); lw += tk.larg + esp;
    });
    const u = o.u == null ? 1 : o.u, n = tokens.length;
    let k = 0;
    ctx.save(); ctx.textBaseline = "alphabetic"; ctx.textAlign = "left";
    if (o.sombra) { ctx.shadowColor = o.sombra; ctx.shadowBlur = 24; ctx.shadowOffsetY = 4; }
    linhas.forEach((ln, li) => {
      const total = ln.reduce((s, tk) => s + tk.larg, 0) + esp * (ln.length - 1);
      let cx = alinha === "center" ? x - total / 2 : alinha === "right" ? x - total : x;
      ln.forEach((tk) => {
        const ap = clamp(u * n * 1.0 - k, 0, 1); k++;
        if (ap > 0) {
          ctx.globalAlpha = ap * (o.alpha == null ? 1 : o.alpha);
          ctx.font = fonte(tk.it); ctx.fillStyle = tk.it ? (o.corIt || C.terracota) : cor;
          ctx.fillText(tk.w, cx, y + li * lh + (1 - ap) * 14);
        }
        cx += tk.larg + esp;
      });
    });
    ctx.restore();
    return { linhas: linhas.length, altura: linhas.length * lh };
  }
  M.texto = texto;

  // ---------- ícones desenhados ----------
  function icone(ctx, nome, x, y, s, f) {
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    const sd = (k) => f * 23 + k;
    switch (nome) {
      case "banco":
        P.forma(ctx, P.poli([[-120, -60], [0, -130], [120, -60]], 30), { fill: "#d8cdb5", sombra: "#b9ab8e", seed: sd(1) });
        [-80, -27, 27, 80].forEach((cx, i) => P.forma(ctx, P.ret(cx - 14, -52, 28, 120), { fill: "#efe6d2", sombra: "#cfc3a8", seed: sd(2 + i), w: 4 }));
        P.forma(ctx, P.ret(-135, 68, 270, 26), { fill: "#d8cdb5", sombra: "#b9ab8e", seed: sd(7) });
        break;
      case "celular":
        P.forma(ctx, P.ret(-70, -130, 140, 260), { fill: "#2e3348", sombra: "#232738", seed: sd(1), w: 6 });
        P.forma(ctx, P.ret(-56, -110, 112, 200), { fill: "#e9eef2", seed: sd(2), w: 3 });
        P.forma(ctx, P.elipse(0, 112, 10, 10, 8), { fill: "#e9eef2", seed: sd(3), w: 3 });
        break;
      case "documento":
        P.forma(ctx, P.ret(-90, -120, 180, 240), { fill: "#fbf7ee", sombra: "#ddd2bb", seed: sd(1) });
        for (let i = 0; i < 6; i++) P.traco(ctx, [[-60, -80 + i * 32], [i === 5 ? 10 : 60, -80 + i * 32]], { w: 4, cor: "#9a8f7c", seed: sd(2 + i) });
        break;
      case "moedas":
        for (let i = 0; i < 5; i++) P.moeda(ctx, -30 + (i % 2) * 10, 60 - i * 26, 56, Math.PI / 2.2, sd(i));
        P.moeda(ctx, 60, 40, 56, 0, sd(9));
        break;
      case "notas":
        for (let i = 0; i < 4; i++) P.forma(ctx, P.ret(-110 + i * 6, -40 - i * 22, 220, 110), { fill: "#9cbf86", sombra: "#7a9c66", seed: sd(i) });
        P.forma(ctx, P.elipse(-80, -80, 26, 26, 12), { fill: "#c3dcb2", seed: sd(8), w: 3 });
        break;
      case "caixa":
        P.forma(ctx, P.poli([[-110, -40], [110, -40], [110, 90], [-110, 90]], 30), { fill: "#c9a46a", sombra: "#a07a3c", seed: sd(1) });
        P.forma(ctx, P.poli([[-110, -40], [-70, -90], [150, -90], [110, -40]], 30), { fill: "#ddb97f", seed: sd(2) });
        P.forma(ctx, P.poli([[110, -40], [150, -90], [150, 40], [110, 90]], 30), { fill: "#a07a3c", seed: sd(3) });
        break;
      case "globo":
        P.forma(ctx, P.elipse(0, 0, 110, 110, 24), { fill: "#9cc3d6", sombra: "#6f98b0", seed: sd(1) });
        P.forma(ctx, [[-60, -50], [-10, -70], [20, -30], [-20, 10], [-50, -10]], { fill: C.salvia, seed: sd(2), w: 3.5 });
        P.forma(ctx, [[20, 20], [70, 10], [80, 50], [40, 80]], { fill: C.salvia, seed: sd(3), w: 3.5 });
        break;
      case "alerta":
        P.forma(ctx, P.poli([[0, -110], [120, 95], [-120, 95]], 30), { fill: C.ocre, sombra: "#b98a2f", seed: sd(1) });
        P.traco(ctx, [[0, -40], [0, 30]], { w: 22, seed: sd(2) });
        P.forma(ctx, P.elipse(0, 62, 12, 12, 8), { fill: INK, seed: sd(3), w: 2 });
        break;
      case "martelo":
        P.membro(ctx, [[-90, 90], [30, -30]], 26, "#8a5a34", sd(1), "#6a4426");
        ctx.save(); ctx.translate(40, -40); ctx.rotate(-Math.PI / 4);
        P.forma(ctx, P.ret(-90, -40, 180, 80), { fill: "#6a4426", sombra: "#4f321c", seed: sd(2) });
        ctx.restore();
        P.forma(ctx, P.ret(-130, 100, 200, 30), { fill: "#8a5a34", seed: sd(3) });
        break;
      case "grade":
        P.forma(ctx, P.ret(-120, -120, 240, 240), { fill: "#d6ccb8", seed: sd(1) });
        for (let i = 0; i < 5; i++) P.traco(ctx, [[-90 + i * 45, -120], [-90 + i * 45, 120]], { w: 12, cor: "#4a4a55", seed: sd(2 + i) });
        break;
      case "lupa":
        P.membro(ctx, [[40, 40], [110, 110]], 26, "#5a4636", sd(1));
        P.forma(ctx, P.elipse(-10, -10, 80, 80, 20), { fill: "rgba(200,225,240,.6)", seed: sd(2), w: 9 });
        break;
      case "envelope":
        P.forma(ctx, P.ret(-130, -80, 260, 170), { fill: "#fbf7ee", sombra: "#ddd2bb", seed: sd(1) });
        P.traco(ctx, P.linha([[-130, -80], [0, 20], [130, -80]], 20), { w: 5, seed: sd(2) });
        break;
      case "relogio":
        P.forma(ctx, P.elipse(0, 0, 100, 100, 22), { fill: "#fbf7ee", sombra: "#ddd2bb", seed: sd(1), w: 7 });
        P.traco(ctx, [[0, 0], [0, -62]], { w: 8, seed: sd(2) });
        P.traco(ctx, [[0, 0], [44, 18]], { w: 8, seed: sd(3) });
        break;
      case "aktie":
        P.forma(ctx, P.ret(-120, -90, 240, 180), { fill: "#fbf7ee", sombra: "#ddd2bb", seed: sd(1) });
        P.traco(ctx, P.linha([[-90, 50], [-40, 0], [10, 20], [80, -50]], 15), { w: 9, cor: C.terracota, seed: sd(2) });
        break;
      case "aviao":
        P.forma(ctx, [[-120, 0], [100, -16], [130, 0], [100, 16]], { fill: "#e9eef2", seed: sd(1) });
        P.forma(ctx, [[-10, -8], [40, -70], [60, -70], [30, -4]], { fill: "#cfd8e3", seed: sd(2), w: 4 });
        P.forma(ctx, [[-10, 8], [40, 70], [60, 70], [30, 4]], { fill: "#cfd8e3", seed: sd(3), w: 4 });
        break;
      case "aranha":
        for (let r = 1; r <= 4; r++) P.traco(ctx, P.elipse(0, 0, r * 30, r * 30, 8), { w: 3, fechado: true, cor: "#7d7466", seed: sd(r) });
        for (let i = 0; i < 8; i++) P.traco(ctx, [[0, 0], [Math.cos(i * Math.PI / 4) * 130, Math.sin(i * Math.PI / 4) * 130]], { w: 3, cor: "#7d7466", seed: sd(10 + i) });
        break;
      default:
        P.forma(ctx, P.elipse(0, 0, 60, 60, 14), { fill: C.ocre, seed: sd(1) });
    }
    ctx.restore();
  }
  M.icone = icone;

  // ---------- detetive com poses ----------
  const POSES = {
    neutro: { boca: 0.2 }, sorri: { boca: 0.7, sobrancelha: 0.3 }, pensa: { mao: 1, olhar: [0.6, -0.8], sobrancelha: 0.6, boca: -0.1, cocar: 1 },
    surpreso: { sobrancelha: 1.2, bocaO: 1, olhar: [0.3, -0.2] }, bravo: { zangado: 1, boca: -0.6 }, aponta: { aponta: 1, olhar: [1, 0], sobrancelha: 0.4, boca: 0.3 },
    desconfia: { zangado: 0.5, sobrancelha: 0.4, boca: -0.2, olhar: [0.8, 0.1] }, preocupado: { sobrancelha: 0.8, boca: -0.5, olhar: [0.3, 0.4] },
  };
  function detetive(ctx, x, y, s, pose, lt, t, extra) {
    const base = Object.assign({ boca: 0.2, sobrancelha: 0, olhar: [0, 0], mao: 0, aponta: 0, bocaO: 0, zangado: 0, cocar: 0 }, POSES[pose] || {}, extra || {});
    const k = ease.out(seg(lt, 0.05, 0.4));
    const st = {
      respira: Math.sin(t * Math.PI * 2 / 2.6), incl: Math.sin(t * 0.9) * 0.02 + (base.incl || 0),
      olhar: [base.olhar[0] * k, base.olhar[1] * k], pisca: P.piscar(lt, [0.9, 3.1, 5.4, 7.6, 9.8]),
      sobrancelha: base.sobrancelha * k, boca: base.boca, bocaO: base.bocaO * k, mao: base.mao * k, aponta: base.aponta * k,
      zangado: base.zangado * k, cocar: base.cocar * seg(lt, 0.4, 0.6),
    };
    ctx.save(); ctx.translate(x, y + (1 - ease.out(seg(lt, 0, 0.35))) * 120); ctx.scale(s, s);
    P.detetive(ctx, st, t);
    ctx.restore();
  }
  M.detetive = detetive;

  function carimbo(ctx, txt, x, y, lt, t0, rot = -0.12, tam = 70, cor = "#c0392b") {
    const u = seg(lt, t0, t0 + 0.16);
    if (u <= 0) return;
    const sc = lerp(2.2, 1, ease.inOut(u));
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc); ctx.globalAlpha = 0.92 * u;
    ctx.font = `700 ${tam}px ${FONT_T}`; const w = ctx.measureText(txt).width + 70;
    ctx.fillStyle = "rgba(251,247,238,.85)"; ctx.fillRect(-w / 2, -tam * 0.85, w, tam * 1.5);
    P.traco(ctx, P.ret(-w / 2, -tam * 0.85, w, tam * 1.5), { w: 9, fechado: true, cor, seed: 7 });
    ctx.fillStyle = cor; ctx.textAlign = "center"; ctx.fillText(txt, 0, tam * 0.3);
    ctx.restore();
  }
  function rotulo(ctx, txt, x, y, lt, t0, o = {}) {
    const u = entra(lt, t0, 0.35);
    if (u <= 0) return;
    const tam = o.tam || 38;
    ctx.save(); ctx.globalAlpha = u; ctx.font = `700 ${tam}px ${FONT_L}`;
    const w = ctx.measureText(txt).width + 50, h = tam * 1.6;
    const cx = o.alinha === "center" ? x - w / 2 : x;
    ctx.translate(0, (1 - u) * 16);
    P.forma(ctx, P.ret(cx, y - h * 0.72, w, h), { fill: o.fundo || "#fbf7ee", seed: o.seed || 3, w: 4, sombra: "rgba(0,0,0,.06)" });
    ctx.fillStyle = o.cor || INK; ctx.fillText(txt, cx + 25, y + tam * 0.05);
    ctx.restore();
  }
  M.rotulo = rotulo;

  // ---------- modelos de cena ----------
  const T = {};
  const passo = (c, i, def = 0) => (c.passos && c.passos[i] != null ? c.passos[i] : def);

  // título/afirmação com ícone e detetive
  T.titulo = (ctx, c, lt, t, f) => {
    fundo(ctx, c.fundo);
    const noite = c.fundo === "noite";
    const icX = c.iconeX || (c.detetive ? 1560 : 1480), icY = c.iconeY || (c.detetive ? 640 : 560);
    if (c.icone) icone(ctx, c.icone, icX, icY, (c.iconeS || (c.detetive ? 1.3 : 1.6)) * pop(lt, passo(c, 1, 0.3)), f);
    if (c.detetive) detetive(ctx, c.detX || 330, 1150, 0.9, c.detetive, lt, t);
    const x = c.detetive ? 640 : 140;
    const maxW = c.maxW || (c.icone ? icX - 230 - x : 1800 - x);
    let tam = c.tam || 92;
    for (let k = 0; k < 8 && texto(ctx, c.texto, x, -999, { tam, maxW, u: 0 }).linhas > 3; k++) tam = Math.round(tam * 0.9);
    const hT = texto(ctx, c.texto, c.alinha === "center" ? 960 : x, c.y || 300, { tam, maxW, u: entra(lt, passo(c, 0, 0.1), Math.max(0.5, (c.dur || 2) * 0.35)),
      cor: noite ? "#f4ecdc" : INK, corIt: noite ? "#e3b44c" : C.terracota, alinha: c.alinha, sombra: noite ? "rgba(10,14,30,.6)" : null }).altura;
    if (c.sub) texto(ctx, c.sub, c.alinha === "center" ? 960 : x, (c.y || 300) + hT + 20, { tam: 44, peso: 600, fam: FONT_L, maxW, u: entra(lt, passo(c, 2, 0.8), 0.5), cor: noite ? "#a9b8d6" : "#5d544a", alinha: c.alinha });
    textura(ctx, c.fundo);
  };

  // número grande que conta + rótulo + ícone
  T.numero = (ctx, c, lt, t, f) => {
    fundo(ctx, c.fundo);
    const noite = c.fundo === "noite";
    const u = ease.out(seg(lt, passo(c, 0, 0.1), passo(c, 0, 0.1) + (c.conta || 1.2)));
    if (c.icone) icone(ctx, c.icone, 1520, 560, 1.9 * pop(lt, 0.15), f);
    // sublinhado desenhado embaixo do número (movimento extra enquanto conta)
    const us = ease.inOut(seg(lt, passo(c, 0, 0.1) + 0.6, passo(c, 0, 0.1) + 1.3));
    if (us > 0) P.traco(ctx, P.parcial(P.linha([[130, 640], [700, 634], [1150, 642]], 20), us), { w: 12, cor: "#d9a441", seed: f * 7 + 5, alpha: 0.9 });
    if (c.rotulo) texto(ctx, c.rotulo, 140, 330, { tam: 52, peso: 700, fam: FONT_L, u: entra(lt, passo(c, 4, 0), 1.2), cor: noite ? "#a9b8d6" : "#5d544a", maxW: 1200 });
    ctx.save();
    let tamN = c.tam || 250;
    const sFim = (c.prefixo || "") + fmt(c.valor, c.casas || 0);
    const limite = c.icone ? 1180 : 1650;
    for (let k = 0; k < 12; k++) {
      ctx.font = `700 ${tamN}px ${FONT_T}`; const w1 = ctx.measureText(sFim).width;
      ctx.font = `italic 700 ${Math.round(tamN * 0.42)}px ${FONT_T}`; const w2 = ctx.measureText(c.sufixo || "").width;
      if (w1 + 30 + w2 <= limite) break;
      tamN = Math.round(tamN * 0.92);
    }
    ctx.font = `700 ${tamN}px ${FONT_T}`; ctx.fillStyle = noite ? "#f4ecdc" : INK;
    const v = fmt(c.valor * u, c.casas || 0);
    const s = (c.prefixo || "") + v;
    ctx.globalAlpha = entra(lt, passo(c, 0, 0.1), 0.3);
    ctx.fillText(s, 130, 600);
    const w = (() => { ctx.font = `700 ${tamN}px ${FONT_T}`; return ctx.measureText(sFim).width; })();
    ctx.font = `italic 700 ${Math.round(tamN * 0.42)}px ${FONT_T}`; ctx.fillStyle = noite ? "#e3b44c" : C.terracota;
    ctx.globalAlpha = entra(lt, passo(c, 0, 0.1) + 0.3, 0.4);
    ctx.fillText(c.sufixo || "", 150 + w, 600);
    ctx.restore();
    if (c.nota) texto(ctx, c.nota, 140, 760, { tam: 50, peso: 600, fam: FONT_L, u: entra(lt, passo(c, 1, 1.2), 0.6), maxW: 1150, cor: noite ? "#d6dceb" : "#3d362f" });
    if (c.nota2) texto(ctx, c.nota2, 140, 860, { tam: 50, peso: 600, fam: FONT_L, u: entra(lt, passo(c, 2, 2.2), 0.6), maxW: 1150, cor: noite ? "#d6dceb" : "#3d362f" });
    if (c.carimbo) carimbo(ctx, c.carimbo, 1450, 880, lt, passo(c, 3, 1.5));
    textura(ctx, c.fundo);
  };

  // dois (ou três) valores comparados em barras proporcionais (dados reais)
  T.comparar = (ctx, c, lt, t, f) => {
    fundo(ctx, c.fundo);
    if (c.titulo) texto(ctx, c.titulo, 140, 200, { tam: 76, u: entra(lt, 0, 0.5), maxW: 1600 });
    const max = Math.max(...c.itens.map((x) => x.valor));
    const n = c.itens.length, larg = Math.min(380, 1300 / n), gap = (1640 - n * larg) / (n + 1);
    c.itens.forEach((it, i) => {
      const t0 = passo(c, i, 0.4 + i * 0.8);
      const u = ease.out(seg(lt, t0, t0 + 0.9));
      const hmax = 560, h = Math.max(8, hmax * (it.valor / max)) * u;
      const x = 140 + gap + i * (larg + gap), base = 950;
      if (u > 0) {
        P.forma(ctx, P.ret(x, base - h, larg, h), { fill: it.cor || (i === n - 1 ? C.terracota : C.ardosia), sombra: "rgba(0,0,0,.18)", seed: f * 7 + i, sdx: -larg * 0.2, sdy: 0 });
        ctx.save(); ctx.globalAlpha = entra(lt, t0 + 0.5, 0.4);
        ctx.font = `700 64px ${FONT_T}`; ctx.fillStyle = INK; ctx.textAlign = "center";
        ctx.fillText(it.texto, x + larg / 2, base - h - 30);
        ctx.font = `700 38px ${FONT_L}`; ctx.fillStyle = "#3d362f";
        ctx.fillText(it.rotulo, x + larg / 2, base + 60);
        if (it.rotulo2) { ctx.font = `600 32px ${FONT_L}`; ctx.fillStyle = "#6d645a"; ctx.fillText(it.rotulo2, x + larg / 2, base + 104); }
        ctx.restore();
      }
    });
    P.traco(ctx, [[120, 952], [1800, 948]], { w: 5, seed: f * 3 });
    if (c.carimbo) carimbo(ctx, c.carimbo, 1500, 330, lt, passo(c, n, 3));
    textura(ctx, c.fundo);
  };

  // local + data (abre um caso)
  T.local = (ctx, c, lt, t, f) => {
    fundo(ctx, c.fundo || "papel");
    const noite = c.fundo === "noite";
    // horizonte desenhado + pino caindo
    const R = P.rng(c.seed || 4);
    ctx.save(); ctx.translate(0, 40 * (1 - ease.out(seg(lt, 0, 3))));
    for (let x = -40, i = 0; x < 1960; i++) { const w = 90 + R() * 150, h = 70 + R() * 150; P.forma(ctx, P.ret(x, 1080 - h, w, h + 40), { fill: noite ? "#1d2640" : "#e3d6bd", sombra: noite ? "#151c32" : "#cfc0a3", seed: f * 5 + i, w: 4, inkCor: noite ? "#0c1020" : INK }); x += w + 6; }
    ctx.restore();
    const py = lerp(-200, 470, ease.back(seg(lt, 0.15, 0.7)));
    ctx.save(); ctx.translate(1450, py);
    P.forma(ctx, [[0, 120], [-70, 10], [-80, -40], [-50, -95], [0, -115], [50, -95], [80, -40], [70, 10]], { fill: C.terracota, sombra: "#963d2b", seed: f * 3 + 1, w: 6 });
    P.forma(ctx, P.elipse(0, -35, 30, 30, 12), { fill: "#fbf7ee", seed: f * 3 + 2, w: 4 });
    ctx.restore();
    const hL = texto(ctx, c.lugar, 140, 330, { tam: 120, u: entra(lt, 0.1, 0.5), cor: noite ? "#f4ecdc" : INK, sombra: noite ? "rgba(10,14,30,.6)" : null, maxW: 1150 }).altura;
    const yD = 330 + hL + 10;
    if (c.data) texto(ctx, c.data, 140, yD, { tam: 64, peso: 700, fam: FONT_T, u: entra(lt, passo(c, 0, 0.6), 0.5), cor: noite ? "#e3b44c" : C.terracota, maxW: 1150, corIt: noite ? "#e3b44c" : C.terracota });
    if (c.sub) texto(ctx, c.sub, 140, yD + (c.data ? 100 : 0), { tam: 46, peso: 600, fam: FONT_L, u: entra(lt, passo(c, 1, 1.2), 0.5), cor: noite ? "#a9b8d6" : "#5d544a", maxW: 1100 });
    textura(ctx, c.fundo || "papel");
  };

  // prédio de banco com placa de nome (sem logo) + carimbo
  T.banco = (ctx, c, lt, t, f) => {
    fundo(ctx, c.fundo || "papel");
    const u = ease.back(seg(lt, 0.05, 0.6));
    ctx.save(); ctx.translate(1300, 980); ctx.scale(1, u); ctx.translate(-1300, -980);
    const x = 950, w = 700, h = 520, base = 980;
    P.forma(ctx, P.ret(x, base - h, w, h), { fill: c.cor || "#e3dccb", sombra: "#c4baa3", brilho: "rgba(255,255,255,.2)", seed: f * 11 + 1, sdx: -110, sdy: 0 });
    P.forma(ctx, P.poli([[x - 40, base - h + 6], [x + w / 2, base - h - 170], [x + w + 40, base - h + 6]], 30), { fill: "#d1c6ad", sombra: "#b3a688", seed: f * 11 + 2 });
    for (let i = 0; i < 6; i++) P.forma(ctx, P.ret(x + 50 + i * 110, base - h + 130, 46, h - 160), { fill: "#f3ecdc", sombra: "#d3c8b0", seed: f * 11 + 3 + i, w: 4 });
    P.forma(ctx, P.ret(x - 30, base - 30, w + 60, 34), { fill: "#d1c6ad", seed: f * 11 + 10 });
    P.forma(ctx, P.ret(x + 120, base - h + 30, w - 240, 80), { fill: "#2e3348", seed: f * 11 + 11, w: 5 });
    ctx.font = `700 50px ${FONT_T}`; ctx.fillStyle = "#e3b44c"; ctx.textAlign = "center";
    ctx.fillText(c.nome, x + w / 2, base - h + 88);
    ctx.restore();
    P.traco(ctx, [[60, 982], [1860, 978]], { w: 5, seed: f * 3 });
    texto(ctx, c.titulo || c.nome, 140, 330, { tam: c.tam || 96, u: entra(lt, 0.2, 0.5), maxW: 760 });
    if (c.sub) texto(ctx, c.sub, 140, 330 + (c.subY || 150), { tam: 46, peso: 600, fam: FONT_L, u: entra(lt, passo(c, 0, 0.8), 0.5), cor: "#5d544a", maxW: 740 });
    if (c.detetive) detetive(ctx, 380, 1180, 0.75, c.detetive, lt, t);
    if (c.carimbo) carimbo(ctx, c.carimbo, 1300, 650, lt, passo(c, 1, 1.6), -0.1, c.carimboTam || 76);
    textura(ctx, c.fundo || "papel");
  };

  // rota entre cidades com moedas viajando (converte moeda)
  T.rota = (ctx, c, lt, t, f) => {
    fundo(ctx, c.fundo || "papel");
    if (c.titulo) texto(ctx, c.titulo, 140, 190, { tam: 72, u: entra(lt, 0, 0.5), maxW: 1650 });
    const cid = c.cidades;
    cid.forEach((cc, i) => {
      const t0 = passo(c, i, 0.3 + i * 0.7);
      const u = pop(lt, t0);
      if (u <= 0) return;
      ctx.save(); ctx.translate(cc[1], cc[2]); ctx.scale(u, u);
      P.forma(ctx, P.elipse(0, 0, 26, 26, 12), { fill: C.terracota, sombra: "#963d2b", seed: f * 5 + i, w: 5 });
      ctx.restore();
      ctx.save(); ctx.globalAlpha = clamp(u, 0, 1); ctx.font = `700 52px ${FONT_T}`; ctx.fillStyle = INK; ctx.textAlign = "center";
      ctx.fillText(cc[0], cc[1], cc[2] + 90);
      if (cc[3]) { ctx.font = `600 34px ${FONT_L}`; ctx.fillStyle = "#6d645a"; ctx.fillText(cc[3], cc[1], cc[2] + 136); }
      ctx.restore();
      if (i > 0) {
        const a = cid[i - 1], u2 = ease.inOut(seg(lt, t0 - 0.2, t0 + 0.5));
        const pts = []; for (let k = 0; k <= 30; k++) { const s = k / 30; pts.push([lerp(a[1], cc[1], s), lerp(a[2], cc[2], s) - Math.sin(Math.PI * s) * 140]); }
        if (u2 > 0) P.traco(ctx, P.parcial(pts, u2), { w: 6, cor: "#6d645a", seed: f + i });
      }
    });
    // moedas que viajam pela rota em loop (contínuo, sem parar a cena)
    if (cid.length > 1 && lt > passo(c, cid.length - 1, 1.5)) {
      for (let m = 0; m < 3; m++) {
        const ph = ((lt * 0.45 + m / 3) % 1), seg2 = ph * (cid.length - 1), i = Math.min(cid.length - 2, Math.floor(seg2)), s = seg2 - i;
        const a = cid[i], b = cid[i + 1];
        const x = lerp(a[1], b[1], s), y = lerp(a[2], b[2], s) - Math.sin(Math.PI * s) * 140;
        P.moeda(ctx, x, y, 34, lt * 8 + m, f * 13 + m);
      }
    }
    if (c.nota) texto(ctx, c.nota, 960, 960, { tam: 52, peso: 700, fam: FONT_L, u: entra(lt, passo(c, cid.length, 2.5), 0.5), alinha: "center", maxW: 1700, cor: "#3d362f" });
    textura(ctx, c.fundo || "papel");
  };

  // cadeia de caixas: A → B → C, com dinheiro passando
  T.fluxo = (ctx, c, lt, t, f) => {
    fundo(ctx, c.fundo || "papel");
    if (c.titulo) texto(ctx, c.titulo, 140, 200, { tam: 72, u: entra(lt, 0, 0.5), maxW: 1650 });
    const n = c.nos.length, w = Math.min(420, 1500 / n - 60), gap = (1640 - n * w) / (n - 1 || 1), y = 560;
    const xs = c.nos.map((_, i) => 140 + i * (w + gap));
    c.nos.forEach((no, i) => {
      const t0 = passo(c, i, 0.3 + i * 0.7), u = pop(lt, t0);
      if (u <= 0) return;
      ctx.save(); ctx.translate(xs[i] + w / 2, y); ctx.scale(u, u);
      P.forma(ctx, P.ret(-w / 2, -110, w, 220), { fill: i === n - 1 && c.destacaFim ? "#f1d9c9" : "#fbf7ee", sombra: "#ddd2bb", seed: f * 9 + i, w: 6 });
      if (no.icone) icone(ctx, no.icone, 0, -48, 0.45, f + i);
      ctx.restore();
      ctx.save(); ctx.globalAlpha = clamp(u, 0, 1);
      texto(ctx, no.texto, xs[i] + w / 2, y + (no.icone ? 50 : 18), { tam: no.icone ? 34 : 44, peso: 700, fam: FONT_L, alinha: "center", maxW: w - 40, lh: 40 });
      ctx.restore();
      if (i > 0) {
        const u2 = ease.inOut(seg(lt, t0 - 0.25, t0 + 0.2));
        if (u2 > 0) {
          const ax = xs[i - 1] + w + 14, bx = xs[i] - 14;
          P.traco(ctx, P.parcial(P.linha([[ax, y], [bx, y]], 12), u2), { w: 7, seed: f + i });
          if (u2 >= 1) P.traco(ctx, [[bx - 26, y - 20], [bx, y], [bx - 26, y + 20]], { w: 7, seed: f + i + 50 });
        }
      }
    });
    if (lt > passo(c, n - 1, 1.5) + 0.4) {
      for (let m = 0; m < 2; m++) {
        const ph = (lt * 0.4 + m * 0.5) % 1, x = lerp(xs[0] + w / 2, xs[n - 1] + w / 2, ph);
        P.moeda(ctx, x, y - 170 - Math.sin(ph * Math.PI * (n - 1)) * 30, 30, lt * 8 + m, f * 3 + m);
      }
    }
    if (c.nota) texto(ctx, c.nota, 960, 880, { tam: 50, peso: 700, fam: FONT_L, u: entra(lt, passo(c, n, 2.4), 0.5), alinha: "center", maxW: 1700, cor: "#3d362f" });
    textura(ctx, c.fundo || "papel");
  };

  // iceberg: visão geral (níveis aparecendo) ou um nível em destaque
  const NIVEIS = ["Die Bank auf deinem Handy", "Die Banken, die wegschauen", "Die Maschine", "Die Bank der Kartelle", "Eine Filiale, 200 Milliarden", "Die Bank, die das Verbrechen war"];
  T.iceberg = (ctx, c, lt, t, f) => {
    fundo(ctx, "agua");
    const nv = c.nivel || 0, DX = -230;
    const yN = (i) => 360 + (i - 1) * 118;
    const cam = nv ? Math.min(60, (yN(nv) - 560) * 0.35) * ease.inOut(seg(lt, 0.1, 1.3)) : 0;
    ctx.save(); ctx.translate(0, -cam);
    for (let k = 0; k < 3; k++) P.traco(ctx, P.linha([[0, 312 + k * 6], [1920, 312 + k * 6]], 60).map((p, i) => [p[0], p[1] + Math.sin(i * 0.7 + lt * 2 + k) * 4]), { w: 3, cor: "rgba(255,255,255,.6)", seed: f + k });
    const gelo = [[700, 310], [790, 170], [860, 130], [930, 190], [1010, 110], [1090, 210], [1180, 310], [1330, 480], [1400, 760], [1360, 1000], [1240, 1130], [960, 1180], [690, 1120], [540, 980], [510, 760], [580, 480]].map(([x, y]) => [x + DX, y]);
    P.forma(ctx, gelo, { fill: "#eef6f9", sombra: "#bcd5e0", brilho: "rgba(255,255,255,.5)", seed: f * 7 + 1, w: 6, sdx: -60, sdy: -20 });
    ctx.save(); ctx.beginPath(); P.caminho(ctx, gelo, true); ctx.clip();
    for (let i = 1; i <= 6; i++) {
      const y0 = yN(i) - 60;
      ctx.fillStyle = `rgba(31,58,85,${0.06 + i * 0.05})`; ctx.fillRect(0, Math.max(312, y0), 1920, 118);
      if (nv === i) { ctx.fillStyle = "rgba(184,80,58,.28)"; ctx.fillRect(0, Math.max(312, y0), 1920, 118); }
      P.traco(ctx, P.linha([[400, y0 + 118], [1300, y0 + 118]], 40), { w: 3, cor: "rgba(31,58,85,.35)", seed: f + i * 3 });
    }
    ctx.restore();
    for (let i = 1; i <= 6; i++) {
      const y = yN(i) + 12;
      const tAp = c.passos && c.passos[i - 1] != null ? c.passos[i - 1] : (nv ? -1 : 0.3 + (i - 1) * 0.5);
      const ap = nv ? (i <= nv ? 1 : 0.4) : entra(lt, tAp, 0.4);
      if (ap <= 0) continue;
      const on = nv === i;
      ctx.save(); ctx.globalAlpha = ap;
      const label = (i === 6 ? "Grund · " : `Ebene ${i} · `) + NIVEIS[i - 1];
      let fz = on ? 38 : 33;
      ctx.font = `700 ${fz}px ${FONT_L}`;
      while (ctx.measureText(label).width > 1880 - 1170 - 30 && fz > 22) { fz -= 1; ctx.font = `700 ${fz}px ${FONT_L}`; }
      const w = ctx.measureText(label).width;
      if (on) P.forma(ctx, P.ret(1170 - 24, y - 46, w + 48, 66), { fill: C.terracota, seed: f + 90, w: 4 });
      else { ctx.fillStyle = "rgba(20,40,62,.55)"; ctx.fillRect(1170 - 14, y - fz - 6, w + 28, fz + 18); }
      ctx.fillStyle = on ? "#fbf7ee" : "#e9f2f6";
      ctx.fillText(label, 1170, y);
      P.traco(ctx, [[1130, y - 12], [1060, y - 12]], { w: 4, cor: on ? C.terracota : "rgba(255,255,255,.6)", seed: f + i });
      ctx.restore();
    }
    if (nv) {
      ctx.save(); ctx.globalAlpha = entra(lt, 0.9, 0.4);
      icone(ctx, "lupa", 960 + DX, yN(nv) + Math.sin(lt * 2) * 6, 0.5, f);
      ctx.restore();
    }
    ctx.restore();
    if (c.titulo) {
      const u = entra(lt, passo(c, 6, nv ? 0.8 : 0.2), 0.5);
      let tz = 58;
      for (let k = 0; k < 6 && texto(ctx, c.titulo, 1170, -999, { tam: tz, maxW: 700, u: 0 }).linhas > 2; k++) tz = Math.round(tz * 0.9);
      texto(ctx, c.titulo, 1170, 110, { tam: tz, u, cor: "#1f3a55", corIt: C.terracota, maxW: 700 });
    }
    textura(ctx, "agua");
  };

  // documento oficial com citação marcada + carimbo
  T.documento = (ctx, c, lt, t, f) => {
    fundo(ctx, "papel");
    const u = ease.out(seg(lt, 0, 0.5));
    ctx.save(); ctx.translate(c.detetive ? 1180 : 980, 560 + (1 - u) * 300); ctx.rotate(-0.03);
    P.forma(ctx, P.ret(-520, -440, 1040, 900), { fill: "#fbf9f2", sombra: "#e0d7c2", seed: f * 3 + 1, w: 5, sdx: -30, sdy: -20 });
    ctx.font = `700 34px ${FONT_L}`; ctx.fillStyle = "#6d645a"; ctx.fillText(c.cabecalho || "", -450, -360);
    ctx.font = `700 64px ${FONT_T}`; ctx.fillStyle = INK; ctx.fillText(c.titulo || "", -450, -280);
    P.traco(ctx, [[-450, -250], [440, -254]], { w: 4, seed: f + 2 });
    const fimL = c.citacao ? Math.max(1.2, passo(c, 0, 0.8) - 0.1) : 2.5;
    for (let i = 0; i < 9; i++) {
      const ul = ease.inOut(seg(lt, 0.3 + i * (fimL - 0.3) / 9, 0.3 + (i + 1) * (fimL - 0.3) / 9));
      if (ul > 0) P.traco(ctx, P.parcial(P.linha([[-450, -190 + i * 44], [i % 3 === 2 ? 120 : 440, -190 + i * 44]], 30), ul), { w: 4, cor: "#b8ae9c", seed: f + 10 + i });
    }
    if (ease.inOut(seg(lt, 0.2, fimL)) < 1) { const k = Math.min(8, Math.floor(seg(lt, 0.3, fimL) * 9)); P.traco(ctx, [[-470 + 40, -200 + k * 44], [-470 + 70, -230 + k * 44]], { w: 6, cor: INK, seed: f }); }
    if (c.citacao) {
      const uq = entra(lt, passo(c, 0, 0.8), 0.5);
      ctx.save(); ctx.globalAlpha = uq;
      ctx.fillStyle = "rgba(242,193,78,.45)"; ctx.fillRect(-470, 230, 940 * ease.inOut(seg(lt, passo(c, 0, 0.8), passo(c, 0, 0.8) + 0.8)), 150);
      ctx.restore();
      texto(ctx, c.aspas ? "„" + c.citacao + "“" : c.citacao, -450, 290, { tam: 50, u: uq, maxW: 900, fam: FONT_T, peso: 700 });
    }
    ctx.restore();
    if (c.carimbo) carimbo(ctx, c.carimbo, c.detetive ? 1500 : 1330, 300, lt, passo(c, 1, 2), 0.1, 64);
    if (c.detetive) detetive(ctx, 330, 1170, 0.85, c.detetive, lt, t);
    textura(ctx, "papel");
  };

  // lista de itens que entram um por um
  T.lista = (ctx, c, lt, t, f) => {
    fundo(ctx, c.fundo || "papel");
    texto(ctx, c.titulo, 140, 190, { tam: 76, u: entra(lt, 0, 0.5), maxW: 1650 });
    c.itens.forEach((it, i) => {
      const t0 = passo(c, i, 0.6 + i * 0.6), u = entra(lt, t0, 0.35);
      if (u <= 0) return;
      const col = c.itens.length > 5 ? Math.floor(i / Math.ceil(c.itens.length / 2)) : 0;
      const row = c.itens.length > 5 ? i % Math.ceil(c.itens.length / 2) : i;
      const x = 160 + col * 860, y = 360 + row * (c.itens.length > 5 ? 130 : 150);
      ctx.save(); ctx.globalAlpha = u; ctx.translate((1 - u) * -30, 0);
      P.forma(ctx, P.elipse(x + 20, y - 18, 18, 18, 10), { fill: C.terracota, seed: f + i, w: 4 });
      ctx.restore();
      texto(ctx, it, x + 70, y, { tam: c.itens.length > 5 ? 48 : 60, peso: 700, fam: FONT_L, u, maxW: c.itens.length > 5 ? 760 : 1100 });
    });
    if (c.detetive) detetive(ctx, 1560, 1170, 0.9, c.detetive, lt, t);
    textura(ctx, c.fundo || "papel");
  };

  // celular com app de banco (sem marca)
  T.celular = (ctx, c, lt, t, f) => {
    fundo(ctx, "papel");
    const u = ease.back(seg(lt, 0, 0.5));
    ctx.save(); ctx.translate(1350, 560); ctx.scale(u, u); ctx.rotate(0.05);
    P.forma(ctx, P.ret(-230, -420, 460, 840), { fill: "#2e3348", sombra: "#232738", seed: f * 3 + 1, w: 7 });
    P.forma(ctx, P.ret(-200, -370, 400, 700), { fill: "#f2f5f7", seed: f * 3 + 2, w: 3 });
    const fase = c.fase || "abrir";
    ctx.font = `700 40px ${FONT_L}`; ctx.fillStyle = INK; ctx.textAlign = "center";
    if (fase === "abrir") {
      ctx.fillText("Konto eröffnen", 0, -260);
      const k = ease.out(seg(lt, passo(c, 0, 0.8), passo(c, 0, 0.8) + 1.2));
      P.forma(ctx, P.ret(-160, -200, 320, 26), { fill: "#d8dde3", seed: f + 3, w: 2 });
      ctx.fillStyle = C.salvia; ctx.fillRect(-158, -198, 316 * k, 22);
      [["Name", -120], ["Ausweis", -30], ["Selfie", 60]].forEach(([s, y], i) => {
        const ok = k > (i + 1) / 3.2;
        P.forma(ctx, P.ret(-160, y - 34, 320, 66), { fill: ok ? "#e1efd8" : "#ffffff", seed: f + 10 + i, w: 3 });
        ctx.font = `600 32px ${FONT_L}`; ctx.fillStyle = INK; ctx.textAlign = "left"; ctx.fillText(s, -130, y + 10);
        if (ok) P.traco(ctx, [[100, y], [118, y + 18], [148, y - 16]], { w: 7, cor: "#4f8a3a", seed: f + 20 + i });
      });
      if (k >= 1) { ctx.textAlign = "center"; ctx.font = `700 46px ${FONT_L}`; ctx.fillStyle = "#4f8a3a"; ctx.fillText("Fertig!", 0, 230); }
    } else {
      ctx.fillText("Verdachtsmeldung", 0, -260);
      const k = seg(lt, passo(c, 0, 0.6), passo(c, 0, 0.6) + 2.5);
      P.forma(ctx, P.elipse(0, -20, 120, 120, 20), { fill: "#fbf7ee", seed: f + 3, w: 6 });
      P.traco(ctx, [[0, -20], [Math.sin(k * 6.28) * 80, -20 - Math.cos(k * 6.28) * 80]], { w: 8, seed: f + 4 });
      ctx.font = `700 46px ${FONT_L}`; ctx.fillStyle = C.terracota; ctx.fillText("zu spät", 0, 200);
    }
    ctx.restore();
    if (c.texto) texto(ctx, c.texto, 140, 320, { tam: 84, u: entra(lt, 0.2, 0.6), maxW: 900 });
    if (c.sub) texto(ctx, c.sub, 140, 560, { tam: 46, peso: 600, fam: FONT_L, u: entra(lt, passo(c, 1, 1.0), 0.5), cor: "#5d544a", maxW: 880 });
    textura(ctx, "papel");
  };

  // caixas de dinheiro passando pelo guichê
  T.guiche = (ctx, c, lt, t, f) => {
    fundo(ctx, "papel");
    P.forma(ctx, P.ret(900, 200, 900, 760), { fill: "#d8cdb5", sombra: "#b9ab8e", seed: f * 3 + 1, sdx: -60, sdy: 0 });
    P.forma(ctx, P.ret(1180, 480, 340, 240), { fill: "#3a3f52", seed: f * 3 + 2, w: 6 });
    ctx.font = `700 40px ${FONT_L}`; ctx.fillStyle = INK; ctx.textAlign = "center"; ctx.fillText("Schalter", 1350, 450);
    for (let k = 0; k < 4; k++) {
      const ph = ((lt - 0.5) * 0.35 + k * 0.25) % 1;
      if (lt < 0.5 + k * 0.7) continue;
      const x = lerp(100, 1350, ease.inOut(clamp(ph * 1.4, 0, 1)));
      ctx.save(); ctx.translate(x, 600); ctx.scale(0.95, 0.95);
      ctx.globalAlpha = x > 1300 ? clamp(1 - (x - 1300) / 60, 0, 1) : 1;
      icone(ctx, "caixa", 0, 0, 1, f + k);
      ctx.restore();
    }
    P.traco(ctx, [[60, 722], [1860, 718]], { w: 5, seed: f });
    if (c.texto) texto(ctx, c.texto, 120, 200, { tam: 72, u: entra(lt, 0.1, 0.6), maxW: 760 });
    if (c.sub) texto(ctx, c.sub, 120, 860, { tam: 46, peso: 600, fam: FONT_L, u: entra(lt, passo(c, 0, 1.2), 0.5), cor: "#3d362f", maxW: 1700 });
    textura(ctx, "papel");
  };

  // carta de alerta indo para 3 destinos + relógio dos anos
  T.carta = (ctx, c, lt, t, f) => {
    fundo(ctx, "papel");
    detetive(ctx, 330, 1170, 0.9, "preocupado", lt, t);
    const dest = c.destinos || ["Vorstand", "Compliance", "Revision"];
    dest.forEach((d, i) => {
      const y = 300 + i * 230, t0 = passo(c, 0, 0.8) + i * 0.4;
      rotulo(ctx, d, 1450, y, lt, t0, { tam: 44 });
      const u = ease.inOut(seg(lt, t0 - 0.4, t0));
      if (u > 0 && u < 1) icone(ctx, "envelope", lerp(600, 1400, u), lerp(620, y - 10, u) - Math.sin(u * Math.PI) * 120, 0.4, f + i);
    });
    if (c.anos) {
      const u = entra(lt, passo(c, 1, 2.5), 0.5);
      if (u > 0) { ctx.save(); ctx.globalAlpha = u; icone(ctx, "relogio", 880, 800, 0.9, f); ctx.restore(); texto(ctx, c.anos, 1000, 830, { tam: 64, u, maxW: 500 }); }
    }
    if (c.texto) texto(ctx, c.texto, 120, 170, { tam: 72, u: entra(lt, 0, 0.5), maxW: 1200 });
    textura(ctx, "papel");
  };

  // teia de empresas
  T.teia = (ctx, c, lt, t, f) => {
    fundo(ctx, "noite");
    const cx = 1150, cy = 560, R = P.rng(11), nos = [];
    for (let i = 0; i < 14; i++) { const a = i / 14 * 6.28 + R() * 0.3, r = 180 + (i % 3) * 120 + R() * 40; nos.push([cx + Math.cos(a) * r * 1.3, cy + Math.sin(a) * r * 0.8]); }
    const u = ease.out(seg(lt, 0.2, 2.6));
    nos.forEach((n, i) => {
      const ui = clamp(u * 14 - i, 0, 1);
      if (ui <= 0) return;
      P.traco(ctx, P.parcial([[cx, cy], n], ui), { w: 3, cor: "rgba(220,230,245,.55)", seed: f + i });
      const j = nos[(i + 3) % 14];
      P.traco(ctx, P.parcial([n, j], ui), { w: 2, cor: "rgba(220,230,245,.3)", seed: f + i + 30 });
      ctx.save(); ctx.globalAlpha = ui;
      P.forma(ctx, P.ret(n[0] - 34, n[1] - 24, 68, 48), { fill: "#36558a", seed: f + i + 60, w: 3, inkCor: "#0c1020" });
      ctx.restore();
    });
    P.forma(ctx, P.elipse(cx, cy, 70, 70, 16), { fill: C.terracota, sombra: "#963d2b", seed: f, w: 5, inkCor: "#0c1020" });
    ctx.font = `700 40px ${FONT_L}`; ctx.fillStyle = "#fbf7ee"; ctx.textAlign = "center"; ctx.fillText(c.centro || "BCCI", cx, cy + 14);
    if (c.texto) texto(ctx, c.texto, 120, 200, { tam: 70, u: entra(lt, 0.1, 0.6), maxW: 760, cor: "#f4ecdc", corIt: "#e3b44c", sombra: "rgba(10,14,30,.6)" });
    if (c.sub) texto(ctx, c.sub, 120, 860, { tam: 44, peso: 600, fam: FONT_L, u: entra(lt, passo(c, 0, 1.5), 0.5), cor: "#a9b8d6", maxW: 760 });
    textura(ctx, "noite");
  };

  // balança: bancos pagam × pessoas
  T.balanca = (ctx, c, lt, t, f) => {
    fundo(ctx, "papel");
    const inc = lerp(0, 0.22, ease.inOut(seg(lt, passo(c, 0, 1), passo(c, 0, 1) + 1.2)));
    ctx.save(); ctx.translate(1230, 330);
    P.membro(ctx, [[0, 0], [0, 600]], 18, "#8a7a5a", f);
    P.forma(ctx, P.ret(-150, 590, 300, 40), { fill: "#8a7a5a", seed: f + 1 });
    ctx.rotate(inc);
    P.membro(ctx, [[-380, 0], [380, 0]], 16, "#8a7a5a", f + 2);
    [[-380, c.esquerda || "Strafen"], [380, c.direita || "Anklagen"]].forEach(([x, rot], i) => {
      ctx.save(); ctx.translate(x, 0); ctx.rotate(-inc);
      P.traco(ctx, [[-90, 200], [0, 0], [90, 200]], { w: 4, seed: f + 5 + i });
      P.forma(ctx, P.poli([[-140, 200], [140, 200], [100, 250], [-100, 250]], 30), { fill: "#d9c08a", seed: f + 7 + i });
      if (i === 0) { const um = entra(lt, passo(c, 0, 1) - 0.4, 0.4); if (um > 0) for (let m = 0; m < 3; m++) P.moeda(ctx, -60 + m * 60, 150 - (m % 2) * 30, 40 * um, 0, f + m); }
      let fz = 44; ctx.font = `700 ${fz}px ${FONT_L}`;
      while (ctx.measureText(rot).width > 330 && fz > 26) { fz -= 2; ctx.font = `700 ${fz}px ${FONT_L}`; }
      ctx.fillStyle = INK; ctx.textAlign = "center"; ctx.fillText(rot, 0, 320);
      ctx.restore();
    });
    ctx.restore();
    if (c.texto) texto(ctx, c.texto, 120, 220, { tam: 76, u: entra(lt, 0.1, 0.6), maxW: 700 });
    if (c.sub) texto(ctx, c.sub, 120, 700, { tam: 46, peso: 600, fam: FONT_L, u: entra(lt, passo(c, 1, 2), 0.5), cor: "#3d362f", maxW: 700 });
    textura(ctx, "papel");
  };

  // detetive grande falando/reagindo com balão
  T.detetive = (ctx, c, lt, t, f) => {
    fundo(ctx, c.fundo || "papel");
    P.brilhoSuave(ctx, 520, 760, 520, "rgba(232,180,80,0.30)");
    detetive(ctx, 520, 1150, 1.0, c.pose || "neutro", lt, t);
    if (c.balao || c.icone) {
      const u = pop(lt, passo(c, 0, 0.5));
      if (u > 0) {
        ctx.save(); ctx.translate(1320, 470); ctx.scale(u, u); ctx.translate(-1320, -470);
        P.nuvem(ctx, 1320, 470, 560, 340, f * 7 + 3);
        if (c.icone) icone(ctx, c.icone, 1320, c.balao ? 380 : 470, 1.35, f);
        if (c.balao) texto(ctx, c.balao, 1320, c.icone ? 600 : 470, { tam: c.icone ? 58 : 72, peso: 700, fam: c.icone ? FONT_L : FONT_T, alinha: "center", maxW: 760 });
        ctx.restore();
      }
    }
    if (c.texto) texto(ctx, c.texto, 130, 180, { tam: 76, u: entra(lt, 0.1, 0.5), maxW: 1600 });
    textura(ctx, c.fundo || "papel");
  };

  // linha do tempo
  T.tempo = (ctx, c, lt, t, f) => {
    fundo(ctx, "papel");
    if (c.titulo) texto(ctx, c.titulo, 140, 200, { tam: 72, u: entra(lt, 0, 0.5), maxW: 1650 });
    const n = c.marcos.length, x0 = 200, x1 = 1720, y = 600;
    const ul = ease.inOut(seg(lt, 0.2, 1.0));
    P.traco(ctx, P.parcial(P.linha([[x0, y], [x1, y]], 30), ul), { w: 7, seed: f });
    c.marcos.forEach((m, i) => {
      const x = n === 1 ? (x0 + x1) / 2 : lerp(x0, x1, i / (n - 1)), t0 = passo(c, i, 0.6 + i * 0.7), u = pop(lt, t0);
      if (u <= 0) return;
      ctx.save(); ctx.translate(x, y); ctx.scale(u, u);
      P.forma(ctx, P.elipse(0, 0, 22, 22, 10), { fill: i === n - 1 ? C.terracota : C.ardosia, seed: f + i, w: 4 });
      ctx.restore();
      ctx.save(); ctx.globalAlpha = clamp(u, 0, 1); ctx.textAlign = "center";
      ctx.font = `700 60px ${FONT_T}`; ctx.fillStyle = INK; ctx.fillText(m[0], x, y - 60);
      ctx.restore();
      texto(ctx, m[1], x, y + 90, { tam: 36, peso: 600, fam: FONT_L, alinha: "center", maxW: Math.min(420, 1500 / n), u: clamp(u, 0, 1), cor: "#3d362f" });
    });
    textura(ctx, "papel");
  };

  // tela final: inscrever-se
  T.cta = (ctx, c, lt, t, f) => {
    fundo(ctx, "papel");
    P.brilhoSuave(ctx, 520, 760, 520, "rgba(232,180,80,0.30)");
    detetive(ctx, 520, 1150, 1.0, "aponta", lt, t);
    texto(ctx, c.texto || "", 960, 260, { tam: 76, u: entra(lt, 0.1, 0.6), maxW: 900, alinha: "left" });
    const u = pop(lt, passo(c, 0, 1.2));
    if (u > 0) {
      ctx.save(); ctx.translate(1300, 660); ctx.scale(u, u);
      P.forma(ctx, P.ret(-250, -70, 500, 140), { fill: "#c0392b", sombra: "#962d22", seed: f, w: 6 });
      ctx.font = `700 56px ${FONT_L}`; ctx.fillStyle = "#fff"; ctx.textAlign = "center"; ctx.fillText("Abonnieren", 0, 20);
      ctx.restore();
    }
    textura(ctx, "papel");
  };


  // miniatura do vídeo (thumbnail): iceberg com um banco no fundo + detetive chocado + número grande
  T.thumb = (ctx, c, lt, t, f) => {
    fundo(ctx, "agua");
    ctx.save(); ctx.translate(300, 0);
    const gelo = [[700, 310], [790, 170], [860, 130], [930, 190], [1010, 110], [1090, 210], [1180, 310], [1330, 480], [1400, 760], [1360, 1000], [1240, 1130], [960, 1180], [690, 1120], [540, 980], [510, 760], [580, 480]];
    P.forma(ctx, gelo, { fill: "#eef6f9", sombra: "#bcd5e0", brilho: "rgba(255,255,255,.5)", seed: 3, w: 8, sdx: -60, sdy: -20 });
    ctx.save(); ctx.beginPath(); P.caminho(ctx, gelo, true); ctx.clip();
    const g = ctx.createLinearGradient(0, 312, 0, 1100); g.addColorStop(0, "rgba(31,58,85,.1)"); g.addColorStop(1, "rgba(31,58,85,.75)");
    ctx.fillStyle = g; ctx.fillRect(0, 312, 1920, 900);
    ctx.restore();
    P.brilhoSuave(ctx, 960, 930, 330, "rgba(229,72,77,.75)");
    icone(ctx, "banco", 960, 900, 1.25, 5);
    ctx.restore();
    for (let k = 0; k < 2; k++) P.traco(ctx, P.linha([[0, 312 + k * 7], [1920, 312 + k * 7]], 60), { w: 4, cor: "rgba(255,255,255,.7)", seed: k });
    detetive(ctx, 330, 1180, 0.95, "surpreso", 5, 0, { aponta: 1, olhar: [1, 0.4] });
    ctx.save(); ctx.lineJoin = "round";
    ctx.font = `700 210px ${FONT_T}`; ctx.lineWidth = 22; ctx.strokeStyle = INK; ctx.strokeText("200 Mrd. €", 70, 230);
    ctx.fillStyle = "#f2c14e"; ctx.fillText("200 Mrd. €", 70, 230);
    ctx.font = `800 64px ${FONT_L}`; ctx.lineWidth = 14; ctx.strokeText("durch EINE Filiale", 84, 330);
    ctx.fillStyle = "#fbf7ee"; ctx.fillText("durch EINE Filiale", 84, 330);
    ctx.restore();
    textura(ctx, "agua");
  };

  // ---------- desenhar o quadro ----------
  M.iniciar = function () {
    if (!papel) { papel = P.papel(W, H); papelNoite = P.papel(W, H, "#8a8577"); }
  };
  M.desenhar = function (ctx, cenas, t) {
    M.iniciar();
    let i = cenas.findIndex((c) => t >= c.t0 && t < c.t1);
    if (i < 0) i = t < cenas[0].t0 ? 0 : cenas.length - 1;
    const c = cenas[i], lt = t - c.t0, f = P.quadro(t);
    c.dur = c.t1 - c.t0;
    const fn = T[c.tipo];
    ctx.save();
    // pequena aproximação contínua da câmera (nada fica 100% parado)
    let z = 1 + 0.025 * ease.inOut(seg(lt, 0, Math.max(2, c.dur)));
    let px = 0, py = 0;
    (c.batidas || []).forEach((b, k) => {
      const u = ease.inOut(seg(lt, b, b + 0.32));
      z += (k % 2 === 0 ? 0.08 : -0.06) * u;
      px += (k % 2 === 0 ? -1 : 1) * 46 * u; py += (k % 3 === 0 ? -1 : 1) * 22 * u;
    });
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    if (fn) {
      const ox = c.foco ? c.foco[0] : 960, oy = c.foco ? c.foco[1] : 540;
      const tr = ctx.setTransform.bind(ctx);
      // os modelos chamam setTransform(1..) em fundo/textura; a câmera é aplicada nos elementos via escala global
      ctx.translate(ox + px, oy + py); ctx.scale(z, z); ctx.translate(-ox, -oy);
      fn(ctx, c, lt, t, f);
    }
    ctx.restore();
    // fade curto entre cenas (0,18 s) para o corte não "piscar"
    const fadeIn = 1 - seg(lt, 0, 0.18);
    if (fadeIn > 0 && i > 0 && !c.semFade) { ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = fadeIn * 0.6; ctx.fillStyle = "#efe6d2"; ctx.fillRect(0, 0, W, H); ctx.restore(); }
  };
  M.T = T;
  window.Motor = M;
})();
