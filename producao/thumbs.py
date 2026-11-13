"""3 thumbs por vídeo para o "Testar e comparar" do YouTube (sugestão 4 da revisão de 13/11).

Mesmo desenho (estilo do canal de referência, lição L011), textos diferentes. Cada texto tem de ser um FATO do
roteiro (lição L010). "|" quebra em 2 linhas; *palavra* sai em amarelo.

Uso: python -I producao/thumbs.py <pasta-do-video> "TEXTO A" "TEXTO B" "TEXTO C"
Saída: videos/<pasta>/publicar/thumb-A.jpg, thumb-B.jpg, thumb-C.jpg (+ thumbs-lado-a-lado.jpg para comparar).
"""
import json, re, shutil, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(__file__).resolve().parents[1]
MOD = R / "producao" / "modelo-thumb"


def main():
    pasta, textos = sys.argv[1], sys.argv[2:]
    pub = R / "videos" / pasta / "publicar"; pub.mkdir(parents=True, exist_ok=True)
    trab = R / "videos" / pasta / "thumbs"
    if not trab.exists():
        shutil.copytree(MOD, trab)
    base = (MOD / "index.html").read_text(encoding="utf-8")
    saidas = []
    for i, t in enumerate(textos):
        letra = "ABCDE"[i]
        html = base.replace("<script>\n      const CENAS", f"<script>window.THUMB = {json.dumps({'texto': t}, ensure_ascii=False)};</script>\n    <script>\n      const CENAS", 1)
        (trab / "index.html").write_text(html, encoding="utf-8")
        r = subprocess.run("npx hyperframes snapshot --at 0.5 --json", cwd=trab, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        png = sorted(trab.glob(".hyperframes/artifacts/snapshots/*/frame-00-at-0.5s.png"), key=lambda p: p.stat().st_mtime)[-1]
        dst = pub / f"thumb-{letra}.jpg"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(png), "-q:v", "2", str(dst)], check=True)
        saidas.append(dst)
        print(f"{letra}: {t} → {dst}")
    ins = sum([["-i", str(s)] for s in saidas], [])
    fil = "".join(f"[{i}]scale=640:360[s{i}];" for i in range(len(saidas))) + "".join(f"[s{i}]" for i in range(len(saidas))) + f"hstack=inputs={len(saidas)}"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *ins, "-filter_complex", fil, str(pub / "thumbs-lado-a-lado.jpg")], check=True)
    print("lado a lado:", pub / "thumbs-lado-a-lado.jpg")


if __name__ == "__main__":
    main()
