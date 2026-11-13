"""Junta as partes renderizadas no vídeo completo (um único encode, fades curtos de áudio nos cortes).

Uso: python -I juntar.py [saida.mp4]
Capítulo 1 = amostra aprovada (0–16,95 s) + k1b + amostra (16,95–28,3 s) + k1d. Depois k2…k8.
"""
import subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).parent
AMOSTRA = AQUI.parent / "amostra-bankskandale" / "renders" / "amostra-bankskandale.mp4"
PARTES = [
    (AMOSTRA, 0.0, 16.95),
    (AQUI / "k1b" / "renders" / "k1b.mp4", None, None),
    (AMOSTRA, 16.95, 28.3),
    (AQUI / "k1d" / "renders" / "k1d.mp4", None, None),
] + [(AQUI / f"k{n}" / "renders" / f"k{n}.mp4", None, None) for n in range(2, 9)]


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)


def main():
    saida = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / "renders" / "bankskandale-completo.mp4"
    saida.parent.mkdir(parents=True, exist_ok=True)
    cmd, filtros, rot = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"], [], []
    for i, (arq, a, b) in enumerate(PARTES):
        if not arq.exists():
            raise SystemExit(f"falta {arq}")
        if a is not None:
            cmd += ["-ss", str(a), "-to", str(b)]
        cmd += ["-i", str(arq)]
        d = (b - a) if a is not None else dur(arq)
        filtros.append(f"[{i}:v]fps=30,scale=1920:1080,setsar=1,format=yuv420p[v{i}]")
        filtros.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.03,afade=t=out:st={max(0, d - 0.06):.3f}:d=0.06[a{i}]")
        rot.append(f"[v{i}][a{i}]")
    filtros.append("".join(rot) + f"concat=n={len(PARTES)}:v=1:a=1[v][a]")
    cmd += ["-filter_complex", ";".join(filtros), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
            "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", str(saida)]
    subprocess.run(cmd, check=True)
    print("pronto:", saida, f"{dur(saida):.1f} s")


if __name__ == "__main__":
    main()
