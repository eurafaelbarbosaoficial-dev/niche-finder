"""Junta as partes renderizadas no vídeo completo (um único encode).

Uso: python -I juntar.py [saida.mp4]
Capítulo 1 = amostra aprovada (0–16,95 s) + k1b + amostra (16,95–28,3 s) + k1d. Depois k2…k8.
Retenção: corta o silêncio entre capítulos. Cada parte termina 0,4 s depois da última palavra, e cada capítulo novo
começa 1,15 s antes da primeira palavra (o iceberg já na tela). O som de transição entra em cada corte.
Grava renders/capitulos.json com o início real de cada capítulo (para a descrição do YouTube).
"""
import json, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
from cenas import CAPITULOS  # noqa: E402

AMOSTRA = AQUI.parent / "amostra-bankskandale" / "renders" / "amostra-bankskandale.mp4"
CAUDA, CABECA = 0.4, 1.15


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)


def janela(cap, corta_cabeca):
    """(início, fim) do trecho útil de um capítulo renderizado, pelos tempos das palavras."""
    spec = CAPITULOS[cap]
    ini_voz = spec.get("abertura", 0.35)
    w = json.load(open(str(AQUI / spec["voz"]).rsplit(".", 1)[0] + ".palavras.json", encoding="utf-8"))
    arq = AQUI / cap / "renders" / f"{cap}.mp4"
    a = max(0.0, ini_voz + w[0]["ini"] - CABECA) if corta_cabeca else 0.0
    b = min(dur(arq), ini_voz + w[-1]["fim"] + CAUDA)
    return arq, a, b


def main():
    saida = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / "renders" / "bankskandale-completo.mp4"
    saida.parent.mkdir(parents=True, exist_ok=True)
    partes = [(AMOSTRA, 0.0, 16.95, None), (*janela("k1b", False), None), (AMOSTRA, 16.95, 28.3, None), (*janela("k1d", False), None)]
    for n in range(2, 9):
        partes.append((*janela(f"k{n}", True), f"k{n}"))
    cmd, filtros, rot = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"], [], []
    inicios, t = {"k1": 0.0}, 0.0
    for i, (arq, a, b, cap) in enumerate(partes):
        cmd += ["-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(arq)]
        d = b - a
        if cap:
            inicios[cap] = round(t, 2)
        t += d
        filtros.append(f"[{i}:v]fps=30,scale=1920:1080,setsar=1,format=yuv420p[v{i}]")
        filtros.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.03,afade=t=out:st={max(0, d - 0.08):.3f}:d=0.08[a{i}]")
        rot.append(f"[v{i}][a{i}]")
    n = len(partes)
    filtros.append("".join(rot) + f"concat=n={n}:v=1:a=1[v][a0]")
    # som de transição em cada capítulo novo
    trans = AQUI / "comum" / "sfx" / "transicao.mp3"
    mix = ["[a0]"]
    for j, cap in enumerate([f"k{k}" for k in range(2, 9)]):
        cmd += ["-i", str(trans)]
        ms = int(max(0, inicios[cap] - 0.05) * 1000)
        filtros.append(f"[{n + j}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:1.6,volume=0.32,afade=t=out:st=1.1:d=0.5,adelay={ms}|{ms}[t{j}]")
        mix.append(f"[t{j}]")
    filtros.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first[a]")
    cmd += ["-filter_complex", ";".join(filtros), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
            "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", str(saida)]
    subprocess.run(cmd, check=True)
    json.dump(inicios, open(saida.parent / "capitulos.json", "w", encoding="utf-8"), indent=1)
    print("pronto:", saida, f"{dur(saida):.1f} s", inicios)


if __name__ == "__main__":
    main()
