"""Tempo de cada palavra da narração (faster-whisper local). Uso: python -I palavras.py voz/bloco-1.mp3 [...]"""
import json, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel

sys.stdout.reconfigure(encoding="utf-8")
m = WhisperModel("medium", device="cpu", compute_type="int8")
for arq in sys.argv[1:]:
    b = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", arq, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(b, dtype=np.int16).astype(np.float32) / 32768.0
    segs, _ = m.transcribe(a, language="de", word_timestamps=True, beam_size=5, vad_filter=True, condition_on_previous_text=False)
    out = [{"p": w.word.strip(), "ini": round(float(w.start), 2), "fim": round(float(w.end), 2)} for s in segs for w in (s.words or [])]
    json.dump(out, open(arq.rsplit(".", 1)[0] + ".palavras.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(arq, len(out), "palavras", flush=True)
