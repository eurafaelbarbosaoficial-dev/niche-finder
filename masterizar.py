"""Masteriza o áudio de um vídeo renderizado: ajusta o volume geral para o padrão do YouTube.

Uso: python -I masterizar.py videos/<projeto>/renders/<nome>.mp4
Gera <nome>-final.mp4 ao lado (o vídeo não é recodificado, só o áudio).

Alvo: -14 LUFS integrado, pico verdadeiro -1,5 dBTP (o YouTube normaliza perto de -14 e não aumenta vídeo baixo).
Usa o loudnorm do ffmpeg em duas passadas (mede primeiro, depois aplica) para não distorcer.
"""
import json, re, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ALVO_I, ALVO_TP, ALVO_LRA = -14.0, -1.5, 11.0


def main():
    ent = Path(sys.argv[1])
    sai = ent.with_name(ent.stem + "-final.mp4")
    filtro = f"loudnorm=I={ALVO_I}:TP={ALVO_TP}:LRA={ALVO_LRA}"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(ent), "-af", filtro + ":print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = json.loads(re.findall(r"\{[^{}]*\}", r.stderr)[-1])
    print(f"antes: {m['input_i']} LUFS, pico {m['input_tp']} dBTP")
    f2 = (f"{filtro}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
          f",aresample=192000,alimiter=limit=0.82:attack=2:release=60:level=false,aresample=48000")  # garante o pico verdadeiro < -1,5 dBTP
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(ent), "-c:v", "copy", "-af", f2,
                    "-ar", "48000", "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", str(sai)], check=True)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(sai), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    i = re.search(r"I:\s*(-?\d+\.\d) LUFS", r[r.rfind("Summary"):])
    p = re.search(r"Peak:\s*(-?\d+\.\d)", r[r.rfind("Summary"):])
    print(f"depois: {i.group(1) if i else '?'} LUFS, pico {p.group(1) if p else '?'} dBTP → {sai}")


if __name__ == "__main__":
    main()
