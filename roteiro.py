"""Roteiro por engenharia reversa (método do Raj: copiar a ESTRUTURA do vídeo que funcionou, nunca o texto).

Passo 1 — baixar a referência:
  python -I roteiro.py baixar <id ou link do vídeo> <slug>
  Baixa a legenda (original do vídeo), grava roteiros/<slug>/transcricao.txt com o tempo a cada ~20 s e
  roteiros/<slug>/medidas.json (duração, palavras, palavras por minuto, título, canal, views).
Passo 2 — o Claude lê a transcrição e escreve roteiros/<slug>/analise.json (o mapa da estrutura: gancho, blocos com
  tempo de início e função, ritmo, transições, gatilhos, fechamento) e roteiros/<slug>/roteiro.json (o roteiro novo
  para o tema do dono, bloco a bloco, seguindo o mapa; fatos com fonte).
Passo 3 — publicar: python -I roteiro.py publicar <slug>  → docs/roteiros/<slug>.json + índice (página roteiro.html).
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cacador import yt  # noqa: E402

BASE = Path(__file__).resolve().parent


def vid_id(s):
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", s)
    return m.group(1) if m else s.strip()


def baixar(ref, slug):
    vid = vid_id(ref)
    pasta = BASE / "roteiros" / slug
    pasta.mkdir(parents=True, exist_ok=True)
    info = json.loads(yt(["-J", "--skip-download", f"https://www.youtube.com/watch?v={vid}"]) or "{}")
    lang = (info.get("language") or "en").split("-")[0]
    with tempfile.TemporaryDirectory() as tmp:
        yt(["--skip-download", "--write-auto-subs", "--write-subs", "--sub-langs", f"{lang}-orig,{lang}", "--sub-format",
            "json3", "-o", str(Path(tmp) / "s.%(ext)s"), f"https://www.youtube.com/watch?v={vid}"])
        arqs = sorted(Path(tmp).glob("s.*.json3"), key=lambda a: ("orig" not in a.name, a.name))
        if not arqs:
            print("Sem legenda nesse vídeo. Alternativa: transcrever com Whisper (watch-skill).")
            return
        ev = json.loads(arqs[0].read_text(encoding="utf-8")).get("events", [])
    blocos, atual, t0, palavras = [], [], None, 0
    for e in ev:
        txt = "".join(s.get("utf8", "") for s in e.get("segs", []) or []).replace("\n", " ").strip()
        if not txt:
            continue
        t = e.get("tStartMs", 0) / 1000
        t0 = t if t0 is None else t0
        if t - t0 >= 20 and atual:
            blocos.append((t0, " ".join(atual))); atual, t0 = [], t
        atual.append(txt); palavras += len(txt.split())
    if atual:
        blocos.append((t0, " ".join(atual)))
    dur = info.get("duration") or (blocos[-1][0] if blocos else 0)
    (pasta / "transcricao.txt").write_text(
        "\n".join(f"[{int(t)//60}:{int(t)%60:02d}] {x}" for t, x in blocos), encoding="utf-8")
    med = {"id": vid, "titulo": info.get("title"), "canal": info.get("channel"), "views": info.get("view_count"),
           "duracao": dur, "idioma": lang, "palavras": palavras,
           "palavras_por_minuto": round(palavras / (dur / 60)) if dur else None,
           "capitulos": [{"ini": c.get("start_time"), "titulo": c.get("title")} for c in info.get("chapters") or []]}
    (pasta / "medidas.json").write_text(json.dumps(med, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(med, ensure_ascii=False)[:400])
    print(f"Transcrição: {pasta / 'transcricao.txt'} ({len(blocos)} trechos)")


def publicar(slug):
    pasta = BASE / "roteiros" / slug
    out = {"slug": slug, **{k: json.loads((pasta / f"{k}.json").read_text(encoding="utf-8"))
                            for k in ("medidas", "analise", "roteiro") if (pasta / f"{k}.json").exists()}}
    d = BASE / "docs" / "roteiros"; d.mkdir(parents=True, exist_ok=True)
    (d / f"{slug}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    idx_p = d / "index.json"
    idx = json.loads(idx_p.read_text(encoding="utf-8")) if idx_p.exists() else []
    idx = [x for x in idx if x["slug"] != slug]
    idx.insert(0, {"slug": slug, "referencia": out.get("medidas", {}).get("titulo"),
                   "formato": (out.get("analise") or {}).get("formato"), "views": out.get("medidas", {}).get("views"),
                   "titulo": (out.get("roteiro") or {}).get("titulo"), "idioma": (out.get("roteiro") or {}).get("idioma")})
    idx_p.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    if "--sem-push" in sys.argv:
        return print(f"Gravado: docs/roteiros/{slug}.json")
    subprocess.run(["git", "add", "docs/roteiros", "roteiros"], cwd=BASE)
    subprocess.run(["git", "commit", "-q", "-m", f"Roteiro: {slug}"], cwd=BASE)
    subprocess.run(["git", "push", "-q"], cwd=BASE)
    print(f"Publicado: docs/roteiros/{slug}.json")


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "baixar":
        baixar(sys.argv[2], sys.argv[3])
    elif len(sys.argv) >= 3 and sys.argv[1] == "publicar":
        publicar(sys.argv[2])
    else:
        print(__doc__)
