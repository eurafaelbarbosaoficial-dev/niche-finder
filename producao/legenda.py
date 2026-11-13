"""Legenda SRT do vídeo final, com o TEXTO EXATO do roteiro e o tempo da voz.

1. Transcreve o áudio do vídeo final (faster-whisper local, palavra por palavra).
2. Alinha as palavras do roteiro às da transcrição (difflib): a grafia vem do roteiro (nomes, números, tremas),
   o tempo vem da voz. Palavra do roteiro sem par ganha o tempo das vizinhas.
3. Quebra em legendas de no máximo 2 linhas × 42 caracteres e 6 s, cortando de preferência no fim da frase.

Uso: python -I producao/legenda.py <video.mp4> <roteiro.json> <saida.srt> [--idioma de]
"""
import argparse, difflib, json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
MAX_CH, MAX_SEG = 70, 6.0


def norm(w):
    return re.sub(r"[^\wäöüß]", "", w.lower())


def transcrever(video, idioma):
    import subprocess
    import numpy as np
    from faster_whisper import WhisperModel
    # o ffmpeg extrai o áudio; o leitor de áudio da biblioteca falha nesta máquina (versão do PyAV)
    b = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(video), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    audio = np.frombuffer(b, dtype=np.int16).astype(np.float32) / 32768.0
    m = WhisperModel("medium", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(audio, language=idioma, word_timestamps=True, beam_size=5, vad_filter=True, condition_on_previous_text=False)
    return [{"p": w.word.strip(), "ini": w.start, "fim": w.end} for s in segs for w in s.words]


def tc(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("roteiro"); ap.add_argument("saida"); ap.add_argument("--idioma", default="de")
    a = ap.parse_args()
    cache = Path(a.saida).with_suffix(".palavras.json")
    if cache.exists():
        tr = json.loads(cache.read_text(encoding="utf-8"))
    else:
        print("transcrevendo (alguns minutos)…", flush=True)
        tr = transcrever(a.video, a.idioma)
        cache.write_text(json.dumps(tr, ensure_ascii=False), encoding="utf-8")
    r = json.loads(Path(a.roteiro).read_text(encoding="utf-8"))
    rot = [w for b in r["blocos"] for w in b["texto"].split()]
    sm = difflib.SequenceMatcher(a=[norm(w) for w in rot], b=[norm(x["p"]) for x in tr], autojunk=False)
    tempo = [None] * len(rot)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                tempo[i1 + k] = (tr[j1 + k]["ini"], tr[j1 + k]["fim"])
        elif op == "replace" and j2 > j1:
            # distribui o trecho da voz entre as palavras do roteiro
            t0, t1 = tr[j1]["ini"], tr[j2 - 1]["fim"]
            n = i2 - i1
            for k in range(n):
                tempo[i1 + k] = (t0 + (t1 - t0) * k / n, t0 + (t1 - t0) * (k + 1) / n)
    casados = sum(1 for t in tempo if t)
    # preenche os que sobraram com as vizinhas
    for i in range(len(tempo)):
        if tempo[i] is None:
            ant = next((tempo[j] for j in range(i - 1, -1, -1) if tempo[j]), (0, 0))
            tempo[i] = (ant[1], ant[1] + 0.2)
    leg, cur = [], []
    for i, w in enumerate(rot):
        cur.append(i)
        txt = " ".join(rot[k] for k in cur)
        dur = tempo[cur[-1]][1] - tempo[cur[0]][0]
        fim_frase = w.endswith((".", "?", "!", ":"))
        prox = len(txt) + 1 + len(rot[i + 1]) if i + 1 < len(rot) else 999
        if fim_frase and len(txt) > 30 or prox > MAX_CH or dur > MAX_SEG or i == len(rot) - 1:
            leg.append(cur); cur = []
    out = []
    for n, c in enumerate(leg, 1):
        palavras = [rot[k] for k in c]
        txt = " ".join(palavras)
        if len(txt) > 42:  # 2 linhas, quebra perto do meio
            meio, acc, corte = len(txt) / 2, 0, 1
            for k, w in enumerate(palavras):
                acc += len(w) + 1
                if acc >= meio:
                    corte = k + 1; break
            txt = " ".join(palavras[:corte]) + "\n" + " ".join(palavras[corte:])
        ini = tempo[c[0]][0]
        fim = tempo[c[-1]][1]
        if n < len(leg):
            fim = min(fim + 0.3, tempo[leg[n][0]][0] - 0.02)
        out.append(f"{n}\n{tc(ini)} --> {tc(max(fim, ini + 0.5))}\n{txt}\n")
    Path(a.saida).write_text("\n".join(out), encoding="utf-8")
    print(f"ok: {a.saida} · {len(leg)} legendas · {casados}/{len(rot)} palavras do roteiro casadas com a voz")


if __name__ == "__main__":
    main()
