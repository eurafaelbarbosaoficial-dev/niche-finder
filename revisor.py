"""Revisor de vídeo do Niche Finder: mede tudo o que dá para medir num vídeo pronto.

Uso:
  python -I revisor.py --video renders/x.mp4 --roteiro texto.txt|legenda.srt [--projeto pasta_hyperframes] [--idioma de] [--saida pasta]

Gera na pasta de saída:
  revisao.json   todos os números
  RELATORIO.md   resumo legível (o agente revisor completa com a parte visual)
  quadros/       folhas de contato (12 quadros cada, com o tempo em cada quadro)

Critérios marcados como "critério do revisor" são escolhas nossas, não regra do YouTube.
"""
import argparse, json, os, re, subprocess, sys, difflib, unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# ---------- critérios (todos num lugar só, para ajustar fácil) ----------
ALVO_LUFS = (-16.0, -12.0)      # mix final; o YouTube normaliza perto de -14 LUFS
PICO_MAX_DBTP = -1.0            # pico verdadeiro máximo do mix
MUSICA_ABAIXO_MIN = 12.0        # música pelo menos 12 LU abaixo da narração (critério do revisor)
MUSICA_ABAIXO_MAX = 30.0        # mais que isso, a música some (critério do revisor)
SFX_ACIMA_MAX = 3.0             # pico do efeito no máximo 3 LU acima da fala forte (p90) (critério do revisor)
SFX_ABAIXO_MAX = 20.0           # efeito mais de 20 LU abaixo da fala não se ouve (critério do revisor)
WER_MAX = 0.08                  # até 8% de palavras diferentes do roteiro (critério do revisor)
CONGELADO_MIN = 2.5             # tela parada por mais de 2,5 s vira aviso
PASSO_QUADROS = 0.5             # um quadro a cada 0,5 s nas folhas de contato


def rodar(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def ffprobe(video):
    r = rodar(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", video])
    d = json.loads(r.stdout or "{}")
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    num, den = (v.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
    return {
        "duracao": round(float(d.get("format", {}).get("duration", 0)), 2),
        "largura": v.get("width"), "altura": v.get("height"),
        "fps": round(float(num) / float(den or 1), 2) if float(den or 1) else None,
        "codec_video": v.get("codec_name"), "tem_audio": a is not None,
        "codec_audio": a.get("codec_name") if a else None,
    }


def ebur128(entrada, filtro_extra=None, inicio=None, dur=None):
    """Mede loudness: integrado (I), faixa (LRA), pico verdadeiro e o máximo momentâneo (M)."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats"]
    if inicio is not None:
        cmd += ["-ss", str(inicio)]
    if dur is not None:
        cmd += ["-t", str(dur)]
    cmd += ["-i", entrada]
    af = (filtro_extra + "," if filtro_extra else "") + "ebur128=peak=true:framelog=info"
    cmd += ["-af", af, "-f", "null", "-"]
    err = rodar(cmd).stderr
    ms = [float(x) for x in re.findall(r"\bM:\s*(-?\d+(?:\.\d+)?)", err)]
    ms = [m for m in ms if m > -70]
    resumo = err[err.rfind("Summary:"):] if "Summary:" in err else ""
    def achar(p):
        m = re.search(p, resumo)
        return float(m.group(1)) if m else None
    ordenado = sorted(ms)
    return {
        "I": achar(r"I:\s*(-?\d+(?:\.\d+)?) LUFS"),
        "LRA": achar(r"LRA:\s*(-?\d+(?:\.\d+)?) LU"),
        "pico_dbtp": achar(r"Peak:\s*(-?\d+(?:\.\d+)?) dBFS"),
        "M_max": max(ms) if ms else None,
        "M_mediana": ordenado[len(ordenado) // 2] if ordenado else None,
        "M_p90": ordenado[int(len(ordenado) * 0.9)] if ordenado else None,
    }


def camadas_do_projeto(projeto):
    """Lê os <audio> do index.html de um projeto HyperFrames: arquivo, início, duração e volume."""
    html = Path(projeto, "index.html").read_text(encoding="utf-8")
    clips = []
    for tag in re.findall(r"<audio\b[^>]*>", html):
        at = dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
        if "src" not in at:
            continue
        ident, src = at.get("id", ""), at["src"]
        nome = (ident + " " + src).lower()
        if re.search(r"\b(vo|narr|voz|voice)", nome):
            tipo = "narracao"
        elif re.search(r"(bgm|musica|music|trilha)", nome):
            tipo = "musica"
        else:
            tipo = "efeito"
        clips.append({"id": ident, "src": src, "tipo": tipo, "inicio": float(at.get("data-start", 0)),
                      "duracao": float(at.get("data-duration", 0)) or None, "volume": float(at.get("data-volume", 1))})
    return clips


def db(v):
    import math
    return 20 * math.log10(v) if v > 0 else -120


def medir_camadas(projeto):
    clips = camadas_do_projeto(projeto)
    for c in clips:
        caminho = str(Path(projeto, c["src"]))
        if not os.path.exists(caminho):
            c["erro"] = "arquivo não encontrado"
            continue
        c["medida"] = ebur128(caminho, f"volume={c['volume']}", dur=c["duracao"])
    narr = [c for c in clips if c["tipo"] == "narracao" and c.get("medida")]
    achados = []
    ref = None
    if narr:
        ref = narr[0]["medida"]
        fala_tipica = ref["M_p90"]  # trechos mais fortes da fala (90% do tempo a voz fica abaixo disso)
        for c in clips:
            m = c.get("medida")
            if not m or c["tipo"] == "narracao":
                continue
            if c["tipo"] == "musica" and m["I"] is not None and ref["I"] is not None:
                dif = ref["I"] - m["I"]
                c["abaixo_da_narracao_LU"] = round(dif, 1)
                if dif < MUSICA_ABAIXO_MIN:
                    achados.append(("alto", c["inicio"], "audio", f"Música {c['id']} só {dif:.1f} LU abaixo da narração (mínimo {MUSICA_ABAIXO_MIN:.0f}): pode cobrir a voz."))
                elif dif > MUSICA_ABAIXO_MAX:
                    achados.append(("baixo", c["inicio"], "audio", f"Música {c['id']} {dif:.1f} LU abaixo da narração: quase não se ouve."))
            if c["tipo"] == "efeito" and m["M_max"] is not None and fala_tipica is not None:
                dif = m["M_max"] - fala_tipica
                c["acima_da_fala_LU"] = round(dif, 1)
                if dif > SFX_ACIMA_MAX:
                    achados.append(("medio", c["inicio"], "audio", f"Efeito {c['id']} ({Path(c['src']).name}) chega a {dif:+.1f} LU da fala típica (limite +{SFX_ACIMA_MAX:.0f}): mais alto que a narração. Baixar o data-volume para ~{c['volume'] * 10 ** ((SFX_ACIMA_MAX - dif) / 20):.2f}."))
                elif dif < -SFX_ABAIXO_MAX:
                    achados.append(("baixo", c["inicio"], "audio", f"Efeito {c['id']} {dif:.1f} LU abaixo da fala: não vai ser ouvido."))
    else:
        achados.append(("medio", 0, "audio", "Não achei a faixa de narração no projeto (id com vo/narr/voz)."))
    return clips, achados


def normalizar(txt):
    txt = unicodedata.normalize("NFC", txt.lower())
    txt = re.sub(r"[^\w\s]", " ", txt)
    return txt.split()


def ler_roteiro(caminho):
    t = Path(caminho).read_text(encoding="utf-8")
    if caminho.lower().endswith((".srt", ".vtt")):
        linhas = [l for l in t.splitlines() if l.strip() and not re.match(r"^\d+$", l.strip()) and "-->" not in l and not l.startswith("WEBVTT")]
        t = " ".join(linhas)
    return t


def transcrever(video, idioma, modelo):
    from faster_whisper import WhisperModel
    import numpy as np
    m = WhisperModel(modelo, device="cpu", compute_type="int8")
    # o ffmpeg extrai o áudio (16 kHz, mono); evita o leitor de áudio da biblioteca, que falha em algumas máquinas
    bruto = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", video, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                           capture_output=True).stdout
    audio = np.frombuffer(bruto, dtype=np.int16).astype(np.float32) / 32768.0
    segs, info = m.transcribe(audio, language=idioma, word_timestamps=True, vad_filter=False, beam_size=5)
    palavras = []
    for s in segs:
        for w in s.words or []:
            palavras.append({"p": w.word.strip(), "ini": round(w.start, 2), "fim": round(w.end, 2), "conf": round(w.probability, 2)})
    return palavras, info.language


def comparar_texto(palavras, roteiro_txt):
    esperado = normalizar(roteiro_txt)
    ouvidas = []
    for w in palavras:
        for n in normalizar(w["p"]):
            ouvidas.append((n, w))
    hyp = [n for n, _ in ouvidas]
    sm = difflib.SequenceMatcher(a=esperado, b=hyp, autojunk=False)
    difs, erros = [], 0
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        erros += max(i2 - i1, j2 - j1)
        t = ouvidas[j1][1]["ini"] if j1 < len(ouvidas) else (ouvidas[-1][1]["fim"] if ouvidas else 0)
        difs.append({"tempo": t, "tipo": {"replace": "trocada", "delete": "faltou", "insert": "sobrou"}[op],
                     "roteiro": " ".join(esperado[i1:i2]), "ouvido": " ".join(hyp[j1:j2])})
    wer = erros / max(1, len(esperado))
    duvidosas = [w for w in palavras if w["conf"] < 0.5]
    return {"palavras_roteiro": len(esperado), "palavras_ouvidas": len(hyp), "wer": round(wer, 3), "diferencas": difs,
            "baixa_confianca": duvidosas}


def detectar_visual(video):
    err = rodar(["ffmpeg", "-hide_banner", "-nostats", "-i", video, "-vf", "blackdetect=d=0.25:pix_th=0.06,freezedetect=n=0.002:d=%s" % CONGELADO_MIN,
                 "-an", "-f", "null", "-"]).stderr
    pretos = [(float(a), float(b)) for a, b in re.findall(r"black_start:(\d+\.?\d*) black_end:(\d+\.?\d*)", err)]
    ini = [float(x) for x in re.findall(r"freeze_start: (\d+\.?\d*)", err)]
    fim = [float(x) for x in re.findall(r"freeze_end: (\d+\.?\d*)", err)]
    congelados = [(a, fim[i] if i < len(fim) else None) for i, a in enumerate(ini)]
    return pretos, congelados


def folhas_de_contato(video, duracao, pasta):
    from PIL import Image, ImageDraw, ImageFont
    pasta = Path(pasta)
    tmp = pasta / "_q"
    tmp.mkdir(parents=True, exist_ok=True)
    for f in tmp.glob("*.jpg"):
        f.unlink()
    rodar(["ffmpeg", "-hide_banner", "-y", "-i", video, "-vf", f"fps={1 / PASSO_QUADROS},scale=640:-2", "-q:v", "3", str(tmp / "q%04d.jpg")])
    quadros = sorted(tmp.glob("q*.jpg"))
    try:
        fonte = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 26)
    except OSError:
        fonte = ImageFont.load_default()
    folhas = []
    por_folha, cols = 12, 3
    for k in range(0, len(quadros), por_folha):
        grupo = quadros[k:k + por_folha]
        w, h = Image.open(grupo[0]).size
        linhas = (len(grupo) + cols - 1) // cols
        folha = Image.new("RGB", (cols * w + (cols + 1) * 8, linhas * (h + 40) + 8), (24, 24, 24))
        d = ImageDraw.Draw(folha)
        for i, q in enumerate(grupo):
            idx = k + i
            t = idx * PASSO_QUADROS + PASSO_QUADROS / 2
            x, y = 8 + (i % cols) * (w + 8), 8 + (i // cols) * (h + 40)
            folha.paste(Image.open(q), (x, y + 32))
            d.text((x, y), f"{t:.2f}s", fill=(255, 255, 255), font=fonte)
        nome = pasta / f"folha-{len(folhas) + 1:02d}.jpg"
        folha.save(nome, quality=88)
        folhas.append(str(nome))
    for f in tmp.glob("*.jpg"):
        f.unlink()
    tmp.rmdir()
    return folhas


def check_hyperframes(projeto):
    r = rodar("npx hyperframes check --json", cwd=projeto, shell=True)
    t = r.stdout
    try:
        d = json.loads(t[t.index("{"):t.rindex("}") + 1])
    except ValueError:
        return {"ok": None, "achados": []}
    ach = []
    for sec in ("lint", "layout", "craft", "audio"):
        for f in d.get(sec, {}).get("findings", []):
            if f.get("severity") in ("error", "warning"):
                ach.append({"secao": sec, "nivel": f.get("severity"), "msg": str(f.get("message"))[:300]})
    return {"ok": d.get("ok"), "achados": ach}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--roteiro", help="texto ou .srt com a narração esperada")
    ap.add_argument("--projeto", help="pasta do projeto HyperFrames (para medir cada camada de som)")
    ap.add_argument("--idioma", default="de")
    ap.add_argument("--modelo", default="medium")
    ap.add_argument("--saida")
    a = ap.parse_args()
    saida = Path(a.saida or Path(a.video).with_suffix("").as_posix() + "-revisao")
    saida.mkdir(parents=True, exist_ok=True)

    R = {"video": a.video, "achados": []}
    def achado(sev, t, area, msg):
        R["achados"].append({"gravidade": sev, "tempo": round(t, 2) if t is not None else None, "area": area, "msg": msg})

    print("1/6 dados técnicos…")
    R["tecnico"] = tec = ffprobe(a.video)
    if not tec["tem_audio"]:
        achado("alto", 0, "audio", "O vídeo não tem trilha de áudio.")
    if (tec["largura"], tec["altura"]) not in ((1920, 1080), (3840, 2160), (1080, 1920)):
        achado("medio", 0, "tecnico", f"Resolução {tec['largura']}x{tec['altura']} fora do padrão.")

    print("2/6 volume do mix final…")
    R["mix"] = mix = ebur128(a.video)
    if mix["I"] is not None and not (ALVO_LUFS[0] <= mix["I"] <= ALVO_LUFS[1]):
        achado("medio", 0, "audio", f"Volume geral {mix['I']} LUFS, fora da faixa {ALVO_LUFS[0]} a {ALVO_LUFS[1]} (o YouTube normaliza perto de -14).")
    if mix["pico_dbtp"] is not None and mix["pico_dbtp"] > PICO_MAX_DBTP:
        achado("alto", 0, "audio", f"Pico {mix['pico_dbtp']} dBTP acima de {PICO_MAX_DBTP}: risco de estourar/distorcer.")

    if a.projeto:
        print("3/6 camadas de som (narração × efeitos × música)…")
        R["camadas"], ach = medir_camadas(a.projeto)
        for s, t, ar, m in ach:
            achado(s, t, ar, m)
        if not any(c["tipo"] == "musica" for c in R["camadas"]):
            R["sem_musica"] = True
        print("   check do HyperFrames…")
        R["hyperframes"] = hf = check_hyperframes(a.projeto)
        for f in hf["achados"]:
            achado("medio" if f["nivel"] == "error" else "baixo", None, "layout", f"[{f['secao']}] {f['msg']}")
    else:
        print("3/6 (sem projeto: camadas de som não medidas)")

    if a.roteiro:
        print(f"4/6 transcrevendo (whisper {a.modelo}, {a.idioma})…")
        palavras, lang = transcrever(a.video, a.idioma, a.modelo)
        R["transcricao"] = {"idioma_detectado": lang, "texto": " ".join(w["p"] for w in palavras), "palavras": palavras}
        R["comparacao"] = cmp_ = comparar_texto(palavras, ler_roteiro(a.roteiro))
        if cmp_["wer"] > WER_MAX:
            achado("alto", None, "narracao", f"{cmp_['wer'] * 100:.1f}% das palavras diferem do roteiro (limite {WER_MAX * 100:.0f}%).")
        for d in cmp_["diferencas"]:
            achado("medio", d["tempo"], "narracao", f"Palavra {d['tipo']}: roteiro «{d['roteiro']}» × ouvido «{d['ouvido']}» (conferir de ouvido: pode ser a transcrição).")
    else:
        print("4/6 (sem roteiro: narração não conferida)")

    print("5/6 telas pretas e congeladas…")
    pretos, cong = detectar_visual(a.video)
    R["visual"] = {"pretos": pretos, "congelados": cong}
    for s, e in pretos:
        if s > 0.05 and e < tec["duracao"] - 0.05:
            achado("alto", s, "visual", f"Tela preta de {s:.2f}s a {e:.2f}s.")
    for s, e in cong:
        fim = e if e is not None else tec["duracao"]
        achado("baixo", s, "visual", f"Imagem parada de {s:.2f}s a {fim:.2f}s ({fim - s:.1f}s): conferir se é pausa de propósito.")

    print("6/6 folhas de contato…")
    R["folhas"] = folhas_de_contato(a.video, tec["duracao"], saida / "quadros")

    ordem = {"alto": 0, "medio": 1, "baixo": 2}
    R["achados"].sort(key=lambda x: (ordem[x["gravidade"]], x["tempo"] if x["tempo"] is not None else -1))
    Path(saida, "revisao.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")

    L = [f"# Relatório automático: {Path(a.video).name}", ""]
    L += [f"- Duração {tec['duracao']} s · {tec['largura']}x{tec['altura']} · {tec['fps']} fps · vídeo {tec['codec_video']} · áudio {tec['codec_audio']}",
          f"- Mix final: {mix['I']} LUFS (faixa-alvo {ALVO_LUFS[0]} a {ALVO_LUFS[1]}) · pico {mix['pico_dbtp']} dBTP · LRA {mix['LRA']} LU", ""]
    if R.get("camadas"):
        L += ["## Camadas de som", "", "| clip | tipo | início | volume | loudness (I) | pico momentâneo | vs fala |", "|---|---|---|---|---|---|---|"]
        for c in R["camadas"]:
            m = c.get("medida") or {}
            vs = c.get("acima_da_fala_LU", c.get("abaixo_da_narracao_LU", ""))
            if "abaixo_da_narracao_LU" in c:
                vs = f"-{vs} LU"
            elif vs != "":
                vs = f"{vs:+} LU"
            L.append(f"| {c['id']} | {c['tipo']} | {c['inicio']}s | {c['volume']} | {m.get('I')} | {m.get('M_max')} | {vs} |")
        if R.get("sem_musica"):
            L += ["", "Sem faixa de música no projeto."]
        L.append("")
    if R.get("comparacao"):
        c = R["comparacao"]
        L += ["## Narração × roteiro", "", f"- {c['palavras_roteiro']} palavras no roteiro, {c['palavras_ouvidas']} ouvidas · diferença {c['wer'] * 100:.1f}%",
              f"- Transcrição: {R['transcricao']['texto']}", ""]
    L += ["## Achados automáticos", ""]
    if not R["achados"]:
        L.append("Nenhum.")
    for x in R["achados"]:
        t = f"{x['tempo']:.2f}s" if x["tempo"] is not None else "—"
        L.append(f"- **{x['gravidade']}** · {t} · {x['area']}: {x['msg']}")
    L += ["", "## Folhas de contato", ""] + [f"- {f}" for f in R["folhas"]]
    Path(saida, "RELATORIO.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\npronto: {saida}")
    print(f"achados: {sum(1 for x in R['achados'] if x['gravidade']=='alto')} altos, {sum(1 for x in R['achados'] if x['gravidade']=='medio')} médios, {sum(1 for x in R['achados'] if x['gravidade']=='baixo')} baixos")


if __name__ == "__main__":
    main()
