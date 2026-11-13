"""Monta o projeto HyperFrames de um capítulo a partir da lista de cenas (cenas.py) e dos tempos das palavras.

Uso: python -I montar.py <capitulo>      (ex.: k2, k1b)
Cada cena tem "em": a frase da narração em que ela começa. "passos": frases (ou segundos) em que os elementos
entram. O script acha o segundo exato de cada frase na transcrição palavra por palavra e escreve <cap>/index.html.
"""
import json, re, shutil, subprocess, sys, unicodedata, difflib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
from cenas import CAPITULOS  # noqa: E402

INICIO_VOZ = 0.35      # a voz começa 0,35 s depois do primeiro quadro
CAUDA = 0.9            # segura um pouco depois da última palavra


def norm(s):
    s = unicodedata.normalize("NFC", s.lower()).replace("ß", "ss")
    return re.sub(r"[^\w]", "", s)


def achar(palavras, frase, cursor):
    alvo = [norm(w) for w in frase.split() if norm(w)]
    ws = [norm(w["p"]) for w in palavras]
    n = len(alvo)
    for i in range(cursor, len(ws) - n + 1):
        if ws[i:i + n] == alvo:
            return i
    # tolerante: melhor janela parecida (número escrito diferente, etc.)
    melhor, mi = 0, None
    for i in range(cursor, len(ws) - n + 1):
        r = difflib.SequenceMatcher(a=" ".join(alvo), b=" ".join(ws[i:i + n])).ratio()
        if r > melhor:
            melhor, mi = r, i
    if mi is not None and melhor >= 0.72:
        return mi
    raise SystemExit(f"Não achei «{frase}» depois da palavra {cursor} ({' '.join(ws[cursor:cursor + 12])}…)")


def licoes():
    """Mostra as lições do revisor antes de montar (feedback loop): o erro de um vídeo não volta no próximo."""
    arq = Path(__file__).resolve().parents[2] / "producao" / "licoes.json"
    if not arq.exists():
        return
    ls = [l for l in json.loads(arq.read_text(encoding="utf-8")) if l["etapa"] in ("voz", "montagem", "imagem", "som")]
    print(f"LIÇÕES DO REVISOR ({len(ls)}) — seguir na montagem:")
    for l in ls:
        print(f"  [{l['id']}] {l['regra']}")


def main():
    cap = sys.argv[1]
    licoes()
    spec = CAPITULOS[cap]
    global INICIO_VOZ
    INICIO_VOZ = spec.get("abertura", INICIO_VOZ)
    voz = AQUI / spec["voz"]
    palavras = json.load(open(str(voz).rsplit(".", 1)[0] + ".palavras.json", encoding="utf-8"))
    dur_voz = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(voz)], capture_output=True, text=True).stdout)
    cenas, cursor = [], 0
    for c in spec["cenas"]:
        c = dict(c)
        if c.get("em") is None:
            t0 = 0.0
        else:
            i = achar(palavras, c["em"], cursor)
            cursor = i
            t0 = palavras[i]["ini"] + INICIO_VOZ - 0.12
        passos = []
        for p in c.get("passos", []):
            if isinstance(p, (int, float)) or p is None:
                passos.append(p)
            else:
                i = achar(palavras, p, cursor)
                passos.append(round(palavras[i]["ini"] + INICIO_VOZ - t0, 2))
        c["passos"] = passos
        c["t0"] = round(max(0.0, t0), 2)
        cenas.append(c)
    total = round(dur_voz + INICIO_VOZ + CAUDA, 2)
    cenas[0]["t0"] = 0.0
    for a, b in zip(cenas, cenas[1:]):
        a["t1"] = b["t0"]
    cenas[-1]["t1"] = total + 1

    # batidas de câmera: onde a cena passaria mais de 2,8 s sem nada novo, um "punch-in" a cada ~2,2 s
    for c in cenas:
        d = c["t1"] - c["t0"]
        # só eventos GRANDES contam (linha de texto pequena não segura o olho)
        GRANDES = {"numero": {0, 3}, "titulo": {0, 1}, "documento": {0, 1}, "lista": set(), "local": set(), "banco": {1},
                   "celular": {0}, "iceberg": set(), "detetive": {0}, "balanca": {0}, "carta": set(), "rota": set(), "tempo": set(), "comparar": set()}
        idx = GRANDES.get(c["tipo"])
        grandes = [p_ for j, p_ in enumerate(c["passos"]) if p_ is not None and 0 <= p_ < d and (idx is None or j in idx)]
        evs = sorted([0.0] + grandes + ([grandes[0] + 1.4] if c["tipo"] == "numero" and grandes else []) + [d])
        bat = []
        for a_, b_ in zip(evs, evs[1:]):
            if b_ - a_ > 2.8:
                n = int((b_ - a_) / 2.2)
                bat += [round(a_ + (b_ - a_) * (k + 1) / (n + 1), 2) for k in range(n)]
        if c["tipo"] == "iceberg":
            bat = []  # o iceberg já tem câmera própria; zoom extra corta o título no topo
        c["batidas"] = bat
        c["passos_b"] = bat

    # efeitos sonoros automáticos (poucos e com função)
    sfx = []
    def som(arq, t, vol, dur=None, fade=None):
        sfx.append((arq, round(t, 2), vol, dur, fade))
    ant_fundo = None
    for k, c in enumerate(cenas):
        fundo = "agua" if c["tipo"] == "iceberg" else c.get("fundo", "papel")
        if k == 0 and c["tipo"] == "iceberg":
            som("transicao.mp3", 0.05, 0.32, 1.6, 0.5)
        if k > 0:
            if c["tipo"] == "iceberg":
                som("transicao.mp3", c["t0"] - 0.15, 0.32, 1.6, 0.5)
            elif fundo != ant_fundo or c.get("woosh"):
                som("whoosh.mp3", c["t0"] - 0.1, 0.35, 0.6)
        ant_fundo = fundo
        P = c["passos"]
        if c.get("carimbo"):
            idx = {"numero": 3, "banco": 1, "documento": 1}.get(c["tipo"], len(c.get("itens", [])) or len(c.get("cidades", [])) or 0)
            if c["tipo"] == "comparar":
                idx = len(c["itens"])
            pt = P[idx] if idx < len(P) and P[idx] is not None else {"numero": 1.5, "banco": 1.6, "documento": 2, "comparar": 3}.get(c["tipo"], 2)
            som("carimbo.mp3", c["t0"] + pt + 0.12, 0.85, 0.6)
            som("impacto.mp3", c["t0"] + pt + 0.1, 0.35, 1.6, 0.8)
        if c["tipo"] == "numero" and c.get("icone") in ("moedas", "notas"):
            som("moedas.mp3", c["t0"] + (P[0] if P and P[0] is not None else 0.1), 0.55, 2.0, 0.6)
        if c["tipo"] in ("lista", "rota", "fluxo", "tempo", "comparar"):
            for j, p in enumerate(P[: len(c.get("itens") or c.get("cidades") or c.get("nos") or c.get("marcos") or [])]):
                if p is not None and j > 0:
                    som("pop.mp3", c["t0"] + p, 0.6, 0.7)
        if c.get("caixa"):
            som("caixa.mp3", c["t0"] + c["caixa"], 0.5, 1.1)
    sfx = [s for s in sfx if 0 <= s[1] < total - 0.2]

    out = AQUI / cap
    (out / "assets" / "js").mkdir(parents=True, exist_ok=True)
    (out / "assets" / "sfx").mkdir(parents=True, exist_ok=True)
    (out / "assets" / "audio").mkdir(parents=True, exist_ok=True)
    for f in (AQUI / "comum" / "js").glob("*.js"):
        shutil.copy(f, out / "assets" / "js" / f.name)
    for f in (AQUI / "comum" / "sfx").glob("*.mp3"):
        shutil.copy(f, out / "assets" / "sfx" / f.name)
    shutil.copy(voz, out / "assets" / "audio" / "narracao.mp3")
    if (AQUI / "comum" / ".media").exists() and not (out / ".media").exists():
        shutil.copytree(AQUI / "comum" / ".media", out / ".media")

    clips = [f'<audio id="vo" class="clip" src="assets/audio/narracao.mp3" data-start="{INICIO_VOZ}" data-duration="{round(dur_voz, 2)}" data-track-index="2" data-volume="1"></audio>']
    for n, (arq, t, vol, dur, fade) in enumerate(sfx):
        d = dur or 1.0
        extra = f' data-fade-out="{fade}"' if fade else ""
        clips.append(f'<audio id="sfx-{n}" class="clip" src="assets/sfx/{arq}" data-start="{t}" data-duration="{d}" data-track-index="{3 + n % 4}" data-volume="{vol}"{extra}></audio>')

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
      html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: #efe6d2; }}
      #root {{ position: relative; width: 100%; height: 100%; }}
      #cv {{ position: absolute; inset: 0; width: 1920px; height: 1080px; }}
      .fontes {{ position: absolute; left: -4000px; top: 0; opacity: 0; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1920" data-height="1080">
      <canvas id="cv" width="1920" height="1080"></canvas>
      <div class="fontes"><span style="font: 700 20px 'Playfair Display'">Aa</span><span style="font: italic 700 20px 'Playfair Display'">Aa</span><span style="font: 700 20px Inter">Aa</span><span style="font: 600 20px Inter">Aa</span></div>
      {chr(10).join("      " + c for c in clips).strip()}
    </div>
    <script>
      const CENAS = {json.dumps(cenas, ensure_ascii=False)};
      (async function () {{
        try {{ await Promise.all(['700 80px "Playfair Display"', 'italic 700 80px "Playfair Display"', '700 40px Inter', '600 40px Inter'].map((f) => document.fonts.load(f))); }} catch (e) {{}}
        const ctx = document.getElementById("cv").getContext("2d");
        const tl = gsap.timeline({{ paused: true }});
        const r = {{ t: 0 }};
        tl.fromTo(r, {{ t: 0 }}, {{ t: {total}, duration: {total}, ease: "none", onUpdate: () => Motor.desenhar(ctx, CENAS, r.t) }}, 0);
        Motor.desenhar(ctx, CENAS, 0);
        window.__timelines["main"] = tl;
      }})();
    </script>
  </body>
</html>
'''
    (out / "index.html").write_text(html, encoding="utf-8")
    if not (out / "hyperframes.json").exists():
        for f in ("hyperframes.json", "meta.json", "package.json"):
            src = AQUI / "base" / f
            if src.exists():
                shutil.copy(src, out / f)
    # retenção: momentos em que algo novo entra (início de cena + passos); modelos com movimento contínuo contam
    CONTINUO = {"rota", "fluxo", "guiche", "teia", "carta"}
    ev = []
    for c in cenas:
        ev.append(c["t0"])
        for p_ in c["passos"] + c["batidas"]:
            if p_ is not None and 0 <= p_ < (c["t1"] - c["t0"]):
                ev.append(c["t0"] + p_)
        if c["tipo"] in CONTINUO:
            ev += [c["t0"] + k * 1.5 for k in range(int((c["t1"] - c["t0"]) / 1.5) + 1)]
        if c["tipo"] == "numero":
            ev.append(c["t0"] + (c["passos"][0] if c["passos"] and c["passos"][0] is not None else 0.1) + 1.3)
    ev = sorted(set(round(x, 2) for x in ev if x < total)) + [total]
    for a_, b_ in zip(ev, ev[1:]):
        if b_ - a_ > 3.0:
            print(f"  ⚠ {b_ - a_:.1f} s sem novidade em {a_:.1f}–{b_:.1f} s")
    print(f"{cap}: {len(cenas)} cenas, {len(sfx)} efeitos, {total} s")
    # ritmo planejado × receita da referência (projeto.json → ritmo_alvo; lição L013)
    durs = [c["t1"] - c["t0"] for c in cenas]
    alvo = {}
    if (AQUI / "projeto.json").exists():
        alvo = json.load(open(AQUI / "projeto.json", encoding="utf-8")).get("ritmo_alvo", {})
    if durs:
        med = sum(durs) / len(durs)
        print(f"  ritmo planejado: cena média {med:.1f} s · {60 / med:.1f} trocas/min" + (f" (alvo: cena média {alvo['cena_media']} s, máx. {alvo['cena_max']} s)" if alvo else ""))
        for c in cenas:
            if alvo and c["t1"] - c["t0"] > alvo.get("cena_max", 99):
                print(f"  ⚠ cena longa: {c['t0']:.1f}–{c['t1']:.1f} s ({c['t1'] - c['t0']:.1f} s, {c['tipo']}): dividir em cenas com cenário próprio")
    for c in cenas:
        print(f"  {c['t0']:7.2f}–{c['t1']:7.2f}  {c['tipo']:10s} {str(c.get('texto') or c.get('titulo') or c.get('lugar') or c.get('nome') or c.get('rotulo') or '')[:60]}  passos={c['passos']}")


if __name__ == "__main__":
    main()
