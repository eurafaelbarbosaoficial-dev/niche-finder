"""Bíblia visual do canal de referência (Raj, vídeo 29, 2:10).

Baixa as thumbs e os vídeos mais vistos do canal que estamos modelando e MEDE o estilo, para o Claude escrever a
"bíblia visual" (como ele edita, que cores usa, como é a thumb). Mede, não opina: a opinião vem depois, no
biblia-visual.md, sempre apontando o quadro/o número que prova.

Uso:
  python -I producao/biblia.py <url ou id do canal> <slug> [--videos 2] [--thumbs 12] [--minutos 3]

Gera em referencias/<slug>/:
  thumbs.jpg          grade das thumbs mais vistas (com as views)
  video-N.jpg         folha de quadros do vídeo N (1 quadro a cada 3 s nos primeiros minutos)
  medidas.json        cortes por minuto, duração média do plano, paleta dominante (thumbs e vídeo), lista de vídeos
O vídeo baixado fica em referencias/<slug>/_videos/ (fora do git).
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[1]
BIN = Path.home() / ".watch-skill" / "bin"
YTDLP = str(BIN / "yt-dlp.exe") if (BIN / "yt-dlp.exe").exists() else "yt-dlp"


def yt(*a, **kw):
    return subprocess.run([YTDLP, "--no-warnings", "--encoding", "utf-8", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def canal_url(c):
    if c.startswith("http"):
        return c.rstrip("/") + ("" if c.rstrip("/").endswith("/videos") else "/videos")
    if c.startswith("UC"):
        return f"https://www.youtube.com/channel/{c}/videos"
    return f"https://www.youtube.com/@{c.lstrip('@')}/videos"


def listar(url):
    r = yt("--flat-playlist", "--print", "%(id)s\t%(view_count)s\t%(duration)s\t%(title)s", url, timeout=300)
    vs = []
    for ln in r.stdout.splitlines():
        p = ln.split("\t")
        if len(p) == 4:
            vs.append({"id": p[0], "views": int(p[1]) if p[1].isdigit() else 0,
                       "dur": int(float(p[2])) if p[2] not in ("NA", "") else None, "titulo": p[3]})
    return vs


def paleta(img_paths, k=6):
    """Cores dominantes (k-means simples em numpy) de um conjunto de imagens."""
    import numpy as np
    px = []
    for p in img_paths:
        b = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(p), "-vf", "scale=64:36", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if b:
            px.append(np.frombuffer(b, dtype=np.uint8).reshape(-1, 3))
    if not px:
        return []
    X = np.concatenate(px).astype(float)
    rng = np.random.default_rng(1)
    C = X[rng.choice(len(X), k, replace=False)]
    for _ in range(15):
        d = ((X[:, None, :] - C[None]) ** 2).sum(-1)
        lab = d.argmin(1)
        C = np.array([X[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(k)])
    cont = np.bincount(lab, minlength=k) / len(X)
    ordem = cont.argsort()[::-1]
    return [{"cor": "#%02x%02x%02x" % tuple(int(v) for v in C[j]), "fatia": round(float(cont[j]), 3)} for j in ordem]


def grade(imgs, legendas, saida, cols=4, w=480, h=270):
    import shutil
    tmp = saida.parent / "_tmp_grade"
    shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir()
    for i, (im, lg) in enumerate(zip(imgs, legendas)):
        lg = re.sub(r"[':\\%]", " ", lg)[:60]
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(im), "-vf",
                        f"scale={w}:{h},drawbox=y=ih-30:w=iw:h=30:color=black@0.7:t=fill,drawtext=text='{lg}':x=8:y=h-24:fontsize=17:fontcolor=white",
                        str(tmp / f"{i:03d}.png")])
    n = len(imgs)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "1", "-i", str(tmp / "%03d.png"), "-vf",
                    f"tile={cols}x{(n + cols - 1) // cols}:padding=4:color=black", "-frames:v", "1", "-q:v", "3", str(saida)])
    shutil.rmtree(tmp, ignore_errors=True)


def cortes(video):
    """Trocas de cena (ffmpeg scene > 0,3): cortes por minuto e duração média do plano."""
    r = subprocess.run(["ffmpeg", "-i", str(video), "-vf", "select='gt(scene,0.3)',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    ts = [float(m) for m in re.findall(r"pts_time:([\d.]+)", r.stderr)]
    dur = float(re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr).groups()[2]) if False else None
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    if m:
        dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    return {"duracao": round(dur or 0, 1), "cortes": len(ts), "cortes_por_min": round(len(ts) / (dur / 60), 1) if dur else None,
            "plano_medio_seg": round(dur / (len(ts) + 1), 2) if dur else None, "tempos": [round(t, 2) for t in ts[:400]]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("canal"); ap.add_argument("slug")
    ap.add_argument("--videos", type=int, default=2); ap.add_argument("--thumbs", type=int, default=12)
    ap.add_argument("--minutos", type=float, default=3)
    a = ap.parse_args()
    pasta = RAIZ / "referencias" / a.slug
    (pasta / "_videos").mkdir(parents=True, exist_ok=True)
    (pasta / "thumbs").mkdir(exist_ok=True)
    print("listando vídeos…", flush=True)
    vs = listar(canal_url(a.canal))
    longos = [v for v in vs if (v["dur"] or 0) >= 240 or v["dur"] is None]
    top = sorted(longos, key=lambda v: -v["views"])
    print(f"{len(vs)} vídeos ({len(longos)} longos)")

    # thumbs
    ths = []
    for v in top[: a.thumbs]:
        f = pasta / "thumbs" / f"{v['id']}.jpg"
        if not f.exists():
            for q in ("maxresdefault", "hqdefault"):
                subprocess.run(["curl", "-s", "-f", "-o", str(f), f"https://i.ytimg.com/vi/{v['id']}/{q}.jpg"])
                if f.exists() and f.stat().st_size > 2000:
                    break
        if f.exists():
            ths.append((f, v))
    def fv(n): return f"{n/1e6:.1f} mi" if n >= 1e6 else f"{n/1e3:.0f} mil" if n >= 1e3 else str(n)
    grade([t[0] for t in ths], [f"{fv(t[1]['views'])} - {t[1]['titulo']}" for t in ths], pasta / "thumbs.jpg")
    med = {"canal": a.canal, "videos_no_canal": len(vs), "lista": top[:30],
           "thumbs": {"arquivos": [t[0].name for t in ths], "paleta": paleta([t[0] for t in ths])}, "videos": []}

    # vídeos mais vistos: quadros e cortes
    for i, v in enumerate(top[: a.videos], 1):
        print(f"baixando {v['id']} ({fv(v['views'])})…", flush=True)
        dest = pasta / "_videos" / f"{v['id']}.mp4"
        if not dest.exists():
            yt("-f", "bv*[height<=360][ext=mp4]/bv*[height<=360]/worst", "-o", str(dest), f"https://www.youtube.com/watch?v={v['id']}", timeout=1800)
        if not dest.exists():
            print("  não consegui baixar"); continue
        c = cortes(dest)
        qd = pasta / "_videos" / f"q{i}"
        qd.mkdir(exist_ok=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-t", str(a.minutos * 60), "-i", str(dest), "-vf", "fps=1/3,scale=480:270", str(qd / "%03d.jpg")])
        qs = sorted(qd.glob("*.jpg"))
        grade(qs, [f"{(k*3)//60}:{(k*3)%60:02d}" for k in range(len(qs))], pasta / f"video-{i}.jpg", cols=6)
        c.update({"id": v["id"], "titulo": v["titulo"], "views": v["views"], "paleta": paleta(qs[::3])})
        med["videos"].append(c)
        print(f"  {c['cortes_por_min']} cortes/min · plano médio {c['plano_medio_seg']} s")
    (pasta / "medidas.json").write_text(json.dumps(med, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"pronto: {pasta}  → agora escreva {pasta / 'biblia-visual.md'} olhando thumbs.jpg e video-N.jpg")


if __name__ == "__main__":
    main()
