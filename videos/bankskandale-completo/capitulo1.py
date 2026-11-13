"""Monta o capítulo 1 com UMA tomada contínua de voz (voz/bloco-1.mp3), sem emenda de gravações.

As 5 cenas aprovadas da amostra (datum, razzia, zentrale, klischee, konto) são reaproveitadas, com o relógio
interno "reajustado" (time-warp) para cair nas mesmas palavras da tomada nova. As partes "Der Verdacht…" e
"Wir haben…" são desenhadas pelo motor, presas às palavras da mesma tomada. Nos cortes entre cenas muito
diferentes: um "dip" curto para a cor do papel + o som de transição.

Uso: python -I capitulo1.py   → escreve k1/ (projeto HyperFrames) pronto para renderizar.
"""
import json, re, shutil, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
import montar  # noqa: E402  (usa norm/achar)
from cenas import CAPITULOS  # noqa: E402

AMOSTRA = AQUI.parent / "amostra-bankskandale"
OUT = AQUI / "k1"
VOZ = AQUI / "voz" / "bloco-1.mp3"
NOVA = json.load(open(AQUI / "voz" / "bloco-1.palavras.json", encoding="utf-8"))
VELHA = json.load(open(AQUI / "voz-extra" / "amostra.palavras.json", encoding="utf-8"))


def meio(a, b):
    return round((NOVA[a]["fim"] + NOVA[b]["ini"]) / 2, 2)


# fronteiras na tomada nova (palavras do roteiro): A = 0–24, B = 25–59, C = 60–85, D = 86–147
FIM_A = meio(24, 25)
FIM_B = meio(59, 60)
FIM_C = meio(85, 86)
TOTAL = round(NOVA[-1]["fim"] + 0.6, 2)
# pares (tempo velho na amostra, tempo novo na tomada) palavra por palavra
PARES_A = [(VELHA[i]["ini"], NOVA[i]["ini"]) for i in range(0, 25)]
PARES_C = [(VELHA[25 + j]["ini"], NOVA[60 + j]["ini"]) for j in range(0, 26)]


def mapa(pares, t):
    """tempo velho → novo (linear por partes entre as palavras)."""
    if t <= pares[0][0]:
        return pares[0][1] + (t - pares[0][0])
    for (o0, n0), (o1, n1) in zip(pares, pares[1:]):
        if o0 <= t <= o1:
            return n0 + (t - o0) * (n1 - n0) / max(1e-6, o1 - o0)
    return pares[-1][1] + (t - pares[-1][0])


# cenas da amostra: início/fim velhos → novos
CENAS_AMOSTRA = {
    "datum": (0.0, 5.35, PARES_A, 0.0, None),
    "razzia": (5.35, 12.78, PARES_A, None, None),
    "zentrale": (12.78, 16.95, PARES_A, None, FIM_A),
    "klischee": (16.95, 22.55, PARES_C, FIM_B, None),
    "konto": (22.55, 29.2, PARES_C, None, FIM_C),
}


def janela_nova(nome):
    o0, o1, pares, n0, n1 = CENAS_AMOSTRA[nome]
    a = n0 if n0 is not None else round(mapa(pares, o0), 2)
    b = n1 if n1 is not None else round(mapa(pares, o1), 2)
    return a, b


def warp_local(nome):
    """pares (novo local, velho local) para o relógio interno da cena."""
    o0, o1, pares, _, _ = CENAS_AMOSTRA[nome]
    a, b = janela_nova(nome)
    pts = [(0.0, 0.0)]
    for o, n in pares:
        if o0 < o < o1 and a < n < b:
            pts.append((round(n - a, 3), round(o - o0, 3)))
    pts.append((round(b - a, 3), round(o1 - o0, 3)))
    return pts


def wl(pts, x):
    for (n0, o0), (n1, o1) in zip(pts, pts[1:]):
        if n0 <= x <= n1:
            return o0 + (x - n0) * (o1 - o0) / max(1e-6, n1 - n0)
    return pts[-1][1]


def inverso(pts, o):
    """velho local → novo local (para data-start das peças da cena)."""
    for (n0, o0), (n1, o1) in zip(pts, pts[1:]):
        if o0 <= o <= o1:
            return n0 + (o - o0) * (n1 - n0) / max(1e-6, o1 - o0)
    return pts[-1][0] + (o - pts[-1][1])


def ajustar_composicao(nome):
    pts = warp_local(nome)
    a, b = janela_nova(nome)
    src = (AMOSTRA / "compositions" / f"{nome}.html").read_text(encoding="utf-8")
    # 1) janelas de visibilidade das peças (data-start/data-duration em tempo local velho)
    def troca_clip(m):
        s0, d0 = float(m.group(1)), float(m.group(2))
        n0, n1 = inverso(pts, s0), inverso(pts, s0 + d0)
        return f'data-start="{n0:.2f}" data-duration="{max(0.05, n1 - n0):.2f}"'
    src = re.sub(r'data-start="([\d.]+)" data-duration="([\d.]+)"', troca_clip, src)
    # 2) relógio: a linha do tempo original é "seekada" pelo tempo reajustado
    reg = f'window.__timelines["{nome}"] = tl;'
    assert reg in src, nome
    pjs = json.dumps(pts)
    src = src.replace(reg, f'''(function () {{
        const W = {pjs}, inner = tl, D = {b - a:.3f};
        const wl = (x) => {{ for (let k = 0; k < W.length - 1; k++) {{ const [n0, o0] = W[k], [n1, o1] = W[k + 1]; if (x >= n0 && x <= n1) return o0 + (x - n0) * (o1 - o0) / Math.max(1e-6, n1 - n0); }} return W[W.length - 1][1]; }};
        const outer = gsap.timeline({{ paused: true }}); const rr = {{ t: 0 }};
        outer.fromTo(rr, {{ t: 0 }}, {{ t: D, duration: D, ease: "none", onUpdate: () => inner.seek(wl(rr.t), false) }}, 0);
        inner.seek(0, false);
        window.__timelines["{nome}"] = outer;
      }})();''')
    (OUT / "compositions" / f"{nome}.html").write_text(src, encoding="utf-8")
    return a, b


def cenas_motor(cap, i0, t0, dur):
    """resolve as cenas do motor (cenas.py) nas palavras da tomada nova, a partir da palavra i0; tempos locais."""
    out, cursor = [], i0
    for c in CAPITULOS[cap]["cenas"]:
        c = dict(c)
        i = montar.achar(NOVA, c["em"], cursor)
        cursor = i
        ts = NOVA[i]["ini"] - 0.12 - t0
        ps = []
        for p in c.get("passos", []):
            if isinstance(p, (int, float)) or p is None:
                ps.append(p)
            else:
                j = montar.achar(NOVA, p, cursor)
                ps.append(round(NOVA[j]["ini"] - t0 - ts, 2))
        c["passos"], c["t0"] = ps, round(max(0.0, ts), 2)
        out.append(c)
    out[0]["t0"] = 0.0
    for x, y in zip(out, out[1:]):
        x["t1"] = y["t0"]
    out[-1]["t1"] = dur + 1
    # batidas de câmera (mesma regra do montar.py)
    GR = {"numero": {0, 3}, "titulo": {0, 1}, "documento": {0, 1}, "lista": set(), "local": set(), "banco": {1}, "celular": {0},
          "iceberg": set(), "detetive": {0}, "balanca": {0}, "carta": set(), "rota": set(), "tempo": set(), "comparar": set()}
    for c in out:
        d = c["t1"] - c["t0"]
        idx = GR.get(c["tipo"])
        gs = [p for j, p in enumerate(c["passos"]) if p is not None and 0 <= p < d and (idx is None or j in idx)]
        evs = sorted([0.0] + gs + ([gs[0] + 1.4] if c["tipo"] == "numero" and gs else []) + [d])
        bat = []
        for x0, x1 in zip(evs, evs[1:]):
            if x1 - x0 > 2.8:
                n = int((x1 - x0) / 2.2)
                bat += [round(x0 + (x1 - x0) * (k + 1) / (n + 1), 2) for k in range(n)]
        c["batidas"] = [] if (c["tipo"] == "iceberg" and c.get("nivel")) else bat
        if c["tipo"] == "iceberg" and not c.get("nivel"):
            c["foco"] = [1450, 620]  # o zoom mira nos nomes dos níveis: nada sai do quadro
    return out


def sfx_motor(cenas, base):
    s = []
    ant = None
    for k, c in enumerate(cenas):
        P, t0 = c["passos"], base + c["t0"]
        fundo = "agua" if c["tipo"] == "iceberg" else c.get("fundo", "papel")
        if k > 0 and c["tipo"] == "iceberg":
            s.append(("transicao.mp3", t0 - 0.15, 0.32, 1.6, 0.5))
        elif k > 0 and fundo != ant:
            s.append(("whoosh.mp3", t0 - 0.1, 0.35, 0.6, None))
        ant = fundo
        if c["tipo"] == "numero" and c.get("icone") in ("moedas", "notas"):
            s.append(("moedas.mp3", t0 + (P[0] if P and P[0] is not None else 0.1), 0.55, 2.0, 0.6))
        if c["tipo"] in ("lista", "fluxo", "rota", "comparar", "tempo"):
            n = len(c.get("itens") or c.get("nos") or c.get("cidades") or c.get("marcos") or [])
            for j, p in enumerate(P[:n]):
                if p is not None and j > 0 and p < c["t1"] - c["t0"]:
                    s.append(("pop.mp3", t0 + p, 0.85, 0.7, None))
    return s


def comp_motor(nome, cenas, dur):
    return f'''<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; background: #efe6d2; }}
    #cv-{nome} {{ position: absolute; inset: 0; width: 1920px; height: 1080px; }}
  </style>
  <div id="root" data-composition-id="{nome}" data-width="1920" data-height="1080">
    <canvas id="cv-{nome}" width="1920" height="1080"></canvas>
  </div>
  <script>
    (function () {{
      const CENAS = {json.dumps(cenas, ensure_ascii=False)};
      const ctx = document.getElementById("cv-{nome}").getContext("2d");
      const tl = gsap.timeline({{ paused: true }});
      const r = {{ t: 0 }};
      tl.fromTo(r, {{ t: 0 }}, {{ t: {dur:.3f}, duration: {dur:.3f}, ease: "none", onUpdate: () => Motor.desenhar(ctx, CENAS, r.t) }}, 0);
      Motor.desenhar(ctx, CENAS, 0);
      window.__timelines["{nome}"] = tl;
    }})();
  </script>
</template>
'''


def main():
    (OUT / "compositions").mkdir(parents=True, exist_ok=True)
    if (OUT / ".media").exists():
        shutil.rmtree(OUT / ".media", ignore_errors=True)
    for d in ("assets/js", "assets/sfx", "assets/audio"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    for f in (AQUI / "comum" / "js").glob("*.js"):
        shutil.copy(f, OUT / "assets" / "js" / f.name)
    for f in (AQUI / "comum" / "sfx").glob("*.mp3"):
        shutil.copy(f, OUT / "assets" / "sfx" / f.name)
    shutil.copytree(AQUI / "comum" / ".media", OUT / ".media", dirs_exist_ok=True)
    dur_voz = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(VOZ)], capture_output=True, text=True).stdout)
    shutil.copy(VOZ, OUT / "assets" / "audio" / "narracao.mp3")
    for f in ("hyperframes.json", "meta.json", "package.json"):
        if (AMOSTRA / f).exists():
            shutil.copy(AMOSTRA / f, OUT / f)

    hosts = {}
    for nome in CENAS_AMOSTRA:
        hosts[nome] = ajustar_composicao(nome)
    # partes do motor
    cb = cenas_motor("k1b", 25, FIM_A, FIM_B - FIM_A)
    cd = cenas_motor("k1d", 86, FIM_C, TOTAL - FIM_C)
    (OUT / "compositions" / "parteb.html").write_text(comp_motor("parteb", cb, FIM_B - FIM_A), encoding="utf-8")
    (OUT / "compositions" / "parted.html").write_text(comp_motor("parted", cd, TOTAL - FIM_C), encoding="utf-8")
    hosts["parteb"] = (FIM_A, FIM_B)
    hosts["parted"] = (FIM_C, TOTAL)

    # efeitos: os da amostra (tempos reajustados) + os das partes do motor + transições nos cortes
    raiz = (AMOSTRA / "index.html").read_text(encoding="utf-8")
    sfx = []
    for tag in re.findall(r"<audio\b[^>]*>", raiz):
        at = dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
        if at.get("id") == "vo":
            continue
        t = float(at["data-start"])
        tn = mapa(PARES_A, t) if t < 16.95 else mapa(PARES_C, t) - mapa(PARES_C, 16.95) + FIM_B
        arq = at["src"].split("/")[-1]
        vol = float(at.get("data-volume", 1))
        if arq == "moedas.mp3":
            vol = 0.45  # arquivo tratado (mais alto que o original)
        if arq == "pop.mp3":
            vol = 0.85  # sob esta tomada de voz os pops sumiam
        sfx.append((arq, round(tn, 2), vol, float(at["data-duration"]), float(at.get("data-fade-out", 0) or 0) or None))
    sfx += sfx_motor(cb, FIM_A) + sfx_motor(cd, FIM_C)
    sfx += [("transicao.mp3", FIM_B - 0.1, 0.32, 1.6, 0.5), ("whoosh.mp3", FIM_C - 0.1, 0.35, 0.6, None)]
    sfx = [x for x in sfx if 0 <= x[1] < TOTAL - 0.2]

    h = []
    for nome, (a, b) in hosts.items():
        h.append(f'<div id="{nome}" data-composition-id="{nome}" data-composition-src="compositions/{nome}.html" data-start="{a:.2f}" data-duration="{b - a:.2f}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>')
    au = [f'<audio id="vo" class="clip" src="assets/audio/narracao.mp3" data-start="0" data-duration="{dur_voz:.2f}" data-track-index="2" data-volume="1"></audio>']
    for n, (arq, t, vol, d, fade) in enumerate(sfx):
        fx = f' data-fade-out="{fade}"' if fade else ""
        au.append(f'<audio id="sfx-{n}" class="clip" src="assets/sfx/{arq}" data-start="{t}" data-duration="{d}" data-track-index="{3 + n % 5}" data-volume="{vol}"{fx}></audio>')
    # "dip" para a cor do papel nos cortes entre cenas muito diferentes (noite → papel) e entre as partes
    cortes = [FIM_A, FIM_B, FIM_C]
    dips = '      tl.set("#dip", { opacity: 0 }, 0);\n' + "\n".join(f'      tl.to("#dip", {{ opacity: 1, duration: 0.22, ease: "power1.in" }}, {c - 0.22:.2f}); tl.to("#dip", {{ opacity: 0, duration: 0.28, ease: "power1.out" }}, {c:.2f});' for c in cortes)
    html = f'''<!doctype html>
<html lang="de">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <script src="assets/js/perfect-freehand.js"></script>
    <script src="assets/js/pincel.js"></script>
    <script src="assets/js/motor.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: #0d1322; }}
      #root {{ position: relative; width: 100%; height: 100%; }}
      #dip {{ position: absolute; inset: 0; background: #efe6d2; opacity: 0; z-index: 50; }}
      .fontes {{ position: absolute; left: -4000px; top: 0; opacity: 0; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
      {chr(10).join("      " + x for x in h).strip()}
      <div id="dip" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="9"></div>
      <div class="fontes"><span style="font: 700 20px 'Playfair Display'">Aa</span><span style="font: italic 700 20px 'Playfair Display'">Aa</span><span style="font: 700 20px Inter">Aa</span><span style="font: 600 20px Inter">Aa</span></div>
      {chr(10).join("      " + x for x in au).strip()}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
{dips}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print("k1 montado:", TOTAL, "s")
    for nome, (a, b) in hosts.items():
        print(f"  {nome:9s} {a:6.2f}–{b:6.2f}")
    print("  efeitos:", len(sfx), "| cortes com dip:", cortes)


if __name__ == "__main__":
    main()
