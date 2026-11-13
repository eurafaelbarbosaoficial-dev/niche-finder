"""Refaz só o áudio de um capítulo renderizado (narração + efeitos do index.html) e coloca de volta no vídeo, sem
renderizar a imagem de novo. Uso: python -I remixar.py k2 [k3 ...]
Volumes por arquivo podem ser trocados em VOL (ex.: moedas mais altas)."""
import re, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).parent
VOL = {"moedas.mp3": 0.55, "pop.mp3": 0.6}


def main():
    for cap in sys.argv[1:]:
        d = AQUI / cap
        html = (d / "index.html").read_text(encoding="utf-8")
        total = float(re.search(r'data-composition-id="main"[^>]*data-duration="([\d.]+)"', html).group(1))
        clips = []
        for tag in re.findall(r"<audio\b[^>]*>", html):
            at = dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
            arq = at["src"].split("/")[-1]
            vol = VOL.get(arq, float(at.get("data-volume", 1)))
            clips.append((d / at["src"], float(at["data-start"]), float(at["data-duration"]), vol, float(at.get("data-fade-out", 0) or 0)))
        video = d / "renders" / f"{cap}.mp4"
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video)]
        filt, rot = [], []
        for i, (arq, ini, dur, vol, fade) in enumerate(clips, 1):
            cmd += ["-i", str(arq)]
            f = f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{dur},asetpts=PTS-STARTPTS,volume={vol}"
            if fade:
                f += f",afade=t=out:st={max(0, dur - fade):.3f}:d={fade}"
            f += f",adelay={int(ini * 1000)}|{int(ini * 1000)}[a{i}]"
            filt.append(f)
            rot.append(f"[a{i}]")
        filt.append("".join(rot) + f"amix=inputs={len(rot)}:normalize=0:duration=longest,atrim=0:{total}[a]")
        saida = d / "renders" / f"{cap}-remix.mp4"
        cmd += ["-filter_complex", ";".join(filt), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", str(saida)]
        subprocess.run(cmd, check=True)
        saida.replace(video)
        print(cap, "áudio refeito:", len(clips), "faixas")


if __name__ == "__main__":
    main()
