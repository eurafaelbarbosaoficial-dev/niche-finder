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
CAUDA, CABECA = 0.3, 1.75
PAUSA_MAX, PAUSA_FICA = 1.4, 0.7   # pausa na fala maior que 1,4 s vira 0,7 s


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
    # pausas longas medidas no próprio áudio da narração (o whisper estica a última palavra sobre o silêncio)
    import re
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(AQUI / spec["voz"]), "-af", f"silencedetect=noise=-38dB:d={PAUSA_MAX}", "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    sil = list(zip([float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)], [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]))
    trechos, ini = [], a
    for s0, s1 in sil:
        x0, x1 = ini_voz + s0, ini_voz + s1
        if x0 <= a + 0.5 or x1 >= b - 0.5:
            continue  # começo/fim: já cortados acima
        trechos.append((ini, x0 + PAUSA_FICA / 2))
        ini = x1 - PAUSA_FICA / 2
    trechos.append((ini, b))
    return [(arq, x, y) for x, y in trechos]


def main():
    saida = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / "renders" / "bankskandale-completo.mp4"
    saida.parent.mkdir(parents=True, exist_ok=True)
    # capítulo 1: uma tomada contínua de voz (capitulo1.py → k1/), sem emendas de gravação
    k1 = AQUI / "k1" / "renders" / "k1.mp4"
    w1 = json.load(open(AQUI / "voz" / "bloco-1.palavras.json", encoding="utf-8"))
    partes = [(k1, 0.0, min(dur(k1), w1[-1]["fim"] + CAUDA), None)]
    for n in range(2, 9):
        js = janela(f"k{n}", True)
        partes += [(*x, f"k{n}" if j == 0 else None) for j, x in enumerate(js)]
        if len(js) > 1:
            print(f"k{n}: {len(js) - 1} pausa(s) longa(s) encurtada(s)")
    cmd, filtros, rot = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"], [], []
    # o capítulo 1 tem 4 pedaços (amostra + partes novas): entre eles, transição suave (crossfade) + som de transição
    N1 = 4 if all(p[3] is None for p in partes[:4]) else 1
    X = 0.45
    inicios, t, juncoes = {"k1": 0.0}, 0.0, []
    for i, (arq, a, b, cap) in enumerate(partes):
        cmd += ["-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(arq)]
        d = b - a
        if 0 < i < N1:
            t -= X                      # o crossfade sobrepõe X segundos
            juncoes.append(round(t, 2))
        if cap:
            inicios[cap] = round(t, 2)
        t += d
        filtros.append(f"[{i}:v]fps=30,scale=1920:1080,setsar=1,format=yuv420p[v{i}]")
        fade = f",afade=t=in:d=0.03,afade=t=out:st={max(0, d - 0.08):.3f}:d=0.08" if i >= N1 else ""
        filtros.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo{fade}[a{i}]")
    # bloco do capítulo 1 com xfade/acrossfade
    lv, la, comp = "v0", "a0", partes[0][2] - partes[0][1]
    for i in range(1, N1):
        filtros.append(f"[{lv}][v{i}]xfade=transition=fade:duration={X}:offset={comp - X:.3f}[xv{i}]")
        filtros.append(f"[{la}][a{i}]acrossfade=d={X}:c1=tri:c2=tri[xa{i}]")
        lv, la = f"xv{i}", f"xa{i}"
        comp += (partes[i][2] - partes[i][1]) - X
    rot.append(f"[{lv}][{la}]")
    for i in range(N1, len(partes)):
        rot.append(f"[v{i}][a{i}]")
    n = len(partes)
    filtros.append("".join(rot) + f"concat=n={len(rot)}:v=1:a=1[v][a0x]")
    # som de transição em cada capítulo novo e em cada junção do capítulo 1
    trans = AQUI / "comum" / "sfx" / "transicao.mp3"
    mix = ["[a0x]"]
    marcas = [max(0, j - 0.1) for j in juncoes] + [max(0, inicios[f"k{k}"] - 0.05) for k in range(2, 9)]
    for j, tm in enumerate(marcas):
        cmd += ["-i", str(trans)]
        ms = int(tm * 1000)
        filtros.append(f"[{n + j}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:1.6,volume=0.32,afade=t=out:st=1.1:d=0.5,adelay={ms}|{ms}[t{j}]")
        mix.append(f"[t{j}]")
    filtros.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first[a]")
    cmd += ["-filter_complex", ";".join(filtros), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
            "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", str(saida)]
    subprocess.run(cmd, check=True)
    json.dump(inicios, open(saida.parent / "capitulos.json", "w", encoding="utf-8"), indent=1)
    print("pronto:", saida, f"{dur(saida):.1f} s", inicios, "junções suaves em", juncoes)


if __name__ == "__main__":
    main()
