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
# --- retenção (critério do revisor: canal explicativo animado) ---
SEM_NOVIDADE_MEDIO = 3.0        # mais de 3 s sem nenhum elemento novo na tela
SEM_NOVIDADE_ALTO = 5.0         # mais de 5 s: risco real de a pessoa sair
FIM_LIVRE = 2.5                 # a pausa final do vídeo pode ficar parada até 2,5 s
SILENCIO_MEDIO = 0.9            # pausa na fala maior que 0,9 s no meio do vídeo
SILENCIO_ALTO = 1.6
PRIMEIRA_PALAVRA_MAX = 1.0      # gancho: a voz tem de começar em até 1 s
PPM_FAIXA = {"de": (95, 160), "en": (130, 190), "pt": (130, 195), "es": (135, 200), "fr": (125, 190)}  # palavras/min (critério do revisor)
SFX_AUDIVEL_MIN = 1.0           # o efeito tem de subir o som do mix em pelo menos 1 LU para ser ouvido


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


def origem_dos_efeitos(projeto, clips):
    """Diz o que cada arquivo de efeito É de verdade, segundo a fonte de onde veio (descrição + licença).
    Pega erro de arquivo trocado: um 'sirene.mp3' que na fonte é um 'Short whoosh'."""
    import hashlib
    man = Path(projeto, ".media", "manifest.jsonl")
    if not man.exists():
        return {}
    por_hash = {}
    for linha in man.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        arq = Path(projeto, d.get("path", ""))
        if arq.exists():
            h = hashlib.md5(arq.read_bytes()).hexdigest()
            pv = d.get("provenance") or {}
            lic = pv.get("license") or ("embutido no HyperFrames" if pv.get("provider") == "bundled.sfx" or d.get("source") == "bundled" else None)
            por_hash[h] = {"descricao": d.get("description"), "licenca": lic, "fonte": pv.get("source_url")}
    out = {}
    for c in clips:
        if c["tipo"] != "efeito":
            continue
        arq = Path(projeto, c["src"])
        if arq.exists():
            out[c["src"]] = por_hash.get(hashlib.md5(arq.read_bytes()).hexdigest(), {"descricao": "(origem desconhecida)"})
    return out


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
            palavras.append({"p": w.word.strip(), "ini": round(float(w.start), 2), "fim": round(float(w.end), 2), "conf": round(float(w.probability), 2)})
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


def ritmo_visual(video, duracao):
    """Acha os momentos em que algo NOVO aparece na tela (ignora o tremor do traço) e os cortes de cena."""
    import numpy as np
    b = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", video, "-vf", "fps=10,scale=320:180,format=gray", "-f", "rawvideo", "-"],
                       capture_output=True).stdout
    f = np.frombuffer(b, dtype=np.uint8).reshape(-1, 180, 320).astype(np.int16)
    lag = 4
    ch = np.abs(f[lag:] - f[:-lag]) > 35
    g = ch.reshape(-1, 12, 15, 16, 20).mean(axis=(2, 4))
    celulas = (g > 0.35).sum(axis=(1, 2))
    tempos = (np.arange(len(celulas)) + lag) / 10.0
    eventos = [round(float(t), 1) for t, c in zip(tempos, celulas) if c >= 1]
    cortes, ult = [], -9
    for t, c in zip(tempos, celulas):
        if c >= 150 and t - ult > 0.8:
            cortes.append(round(float(t) - 0.2, 1))
            ult = t
    pontos = [0.0] + eventos + [duracao]
    lacunas = [(round(a, 1), round(b2, 1)) for a, b2 in zip(pontos, pontos[1:]) if b2 - a >= SEM_NOVIDADE_MEDIO]
    planos = [b2 - a for a, b2 in zip([0.0] + cortes, cortes + [duracao])]
    return {"eventos": eventos, "cortes": cortes, "lacunas": lacunas,
            "plano_medio_s": round(sum(planos) / len(planos), 1) if planos else None,
            "plano_max_s": round(max(planos), 1) if planos else None}


def ritmo_fala(palavras):
    r = {"primeira_palavra": palavras[0]["ini"] if palavras else None, "silencios": [], "ppm": None}
    if not palavras:
        return r
    for a, b in zip(palavras, palavras[1:]):
        gap = b["ini"] - a["fim"]
        if gap >= SILENCIO_MEDIO:
            r["silencios"].append({"de": float(a["fim"]), "ate": float(b["ini"]), "dur": round(float(gap), 2), "depois_de": a["p"]})
    falado = palavras[-1]["fim"] - palavras[0]["ini"]
    r["ppm"] = round(len(palavras) / falado * 60) if falado > 0 else None
    return r


def _pcm(caminho, filtro=None):
    import numpy as np
    cmd = ["ffmpeg", "-loglevel", "error", "-i", caminho]
    if filtro:
        cmd += ["-af", filtro]
    cmd += ["-ac", "1", "-ar", "16000", "-f", "s16le", "-"]
    b = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(b, dtype=np.int16).astype(np.float32) / 32768.0


def _rms_db(x, jan=800):
    import numpy as np
    n = len(x) // jan
    if n == 0:
        return np.array([-90.0])
    r = np.sqrt((x[: n * jan].reshape(n, jan) ** 2).mean(axis=1) + 1e-12)
    return 20 * np.log10(r)


def efeitos_audiveis(video, projeto, clips):
    """Confere no mix final se cada efeito aparece por cima da voz (um efeito pode existir e ninguém ouvir).
    Compara o mix com a voz sozinha em janelas de 50 ms, no trecho do efeito."""
    import numpy as np
    narr = next((c for c in clips if c["tipo"] == "narracao"), None)
    if not narr:
        return []
    mix = _pcm(video)
    vo = np.zeros_like(mix)
    v = _pcm(str(Path(projeto, narr["src"])), f"volume={narr['volume']}")
    i0 = int(narr["inicio"] * 16000)
    vo[i0:i0 + len(v)] = v[: max(0, len(mix) - i0)]
    # ganho do mix em relação à voz (o vídeo pode ter sido masterizado depois)
    fala = _rms_db(vo) > -45
    off = float(np.median((_rms_db(mix) - _rms_db(vo))[fala])) if fala.any() else 0.0
    out = []
    for c in clips:
        if c["tipo"] != "efeito":
            continue
        a = int(c["inicio"] * 16000)
        b = int((c["inicio"] + min(c["duracao"] or 1.0, 1.5)) * 16000)
        m_db, v_db = _rms_db(mix[a:b]), _rms_db(vo[a:b]) + off
        k = min(len(m_db), len(v_db))
        if k == 0:
            continue
        ganho = float(np.max(m_db[:k] - np.maximum(v_db[:k], -60)))
        # som curto e seco (clink, estalo): o ouvido percebe pelo pico, não pela média
        lin = 10 ** (off / 20)
        pk_m = float(np.max(np.abs(mix[a:b]))) if b > a else 0
        pk_v = float(np.max(np.abs(vo[a:b]))) * lin if b > a else 0
        if pk_m > 0 and pk_v > 0:
            ganho = max(ganho, 20 * np.log10(pk_m / pk_v))
        elif pk_m > 0:
            ganho = max(ganho, 60.0)
        out.append({"id": c["id"], "inicio": c["inicio"], "ganho_LU": round(ganho, 1)})
    return out


def efeitos_com_fala(projeto, clips):
    """Um efeito sonoro não pode ter voz gravada (já aconteceu: um 'carimbo' que era uma pessoa dizendo 'rubber stamp')."""
    import numpy as np
    from faster_whisper import WhisperModel
    m = WhisperModel("small", device="cpu", compute_type="int8")
    vistos, out = set(), []
    for c in clips:
        if c["tipo"] != "efeito" or c["src"] in vistos:
            continue
        vistos.add(c["src"])
        b = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(Path(projeto, c["src"])), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                           capture_output=True).stdout
        a = np.frombuffer(b, dtype=np.int16).astype(np.float32) / 32768.0
        segs, _ = m.transcribe(a, vad_filter=True)
        txt = " ".join(x.text.strip() for x in segs if x.no_speech_prob < 0.6).strip()
        if len(re.sub(r"\W", "", txt)) >= 3:
            out.append({"src": c["src"], "texto": txt, "inicio": c["inicio"]})
    return out


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
        print("   efeitos audíveis no mix e efeitos com voz gravada…")
        R["efeitos_no_mix"] = aud = efeitos_audiveis(a.video, a.projeto, R["camadas"])
        for e in aud:
            if e["ganho_LU"] is not None and e["ganho_LU"] < SFX_AUDIVEL_MIN:
                achado("medio", e["inicio"], "audio", f"Efeito {e['id']} quase não se ouve no mix: no melhor momento sobe só {e['ganho_LU']} dB por cima da voz (mínimo {SFX_AUDIVEL_MIN}). Aumentar o volume ou mudar de lugar.")
        R["origem_efeitos"] = origem_dos_efeitos(a.projeto, R["camadas"])
        R["efeitos_com_fala"] = fal = efeitos_com_fala(a.projeto, R["camadas"])
        for e in fal:
            achado("alto", e["inicio"], "audio", f"O efeito {e['src']} tem VOZ gravada («{e['texto']}»): não é o som certo. Trocar o arquivo.")
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
        R["fala"] = rf = ritmo_fala(palavras)
        if rf["primeira_palavra"] is not None and rf["primeira_palavra"] > PRIMEIRA_PALAVRA_MAX:
            achado("alto", 0, "retencao", f"A voz só começa em {rf['primeira_palavra']} s: o gancho tem de começar em até {PRIMEIRA_PALAVRA_MAX} s.")
        sons = [c["inicio"] for c in R.get("camadas", []) if c["tipo"] == "efeito"]
        for si in rf["silencios"]:
            if si["de"] < tec["duracao"] - 1.5:
                g = "alto" if si["dur"] >= SILENCIO_ALTO else "medio"
                if any(si["de"] - 0.3 <= t0 <= si["ate"] for t0 in sons) and si["dur"] < SILENCIO_ALTO:
                    g = "baixo"  # a pausa é preenchida por um efeito sonoro
                achado(g, si["de"], "retencao", f"Silêncio de {si['dur']} s na fala depois de «{si['depois_de']}»: buraco que derruba retenção (cortar a pausa ou cobrir com som/imagem).")
        fx = PPM_FAIXA.get(a.idioma, (120, 190))
        if rf["ppm"] and not (fx[0] <= rf["ppm"] <= fx[1]):
            achado("medio", None, "retencao", f"Ritmo da fala {rf['ppm']} palavras/min, fora de {fx[0]}–{fx[1]} para '{a.idioma}'.")
    else:
        print("4/6 (sem roteiro: narração não conferida)")

    print("5/6 telas pretas, congeladas e ritmo visual…")
    R["ritmo"] = rv = ritmo_visual(a.video, tec["duracao"])
    for x0, x1 in rv["lacunas"]:
        if x1 >= tec["duracao"] - 0.05 and x1 - x0 <= FIM_LIVRE:
            continue
        dur = x1 - x0
        g = "alto" if dur >= SEM_NOVIDADE_ALTO else "medio"
        achado(g, x0, "retencao", f"{dur:.1f} s sem nada novo na tela ({x0}–{x1} s): a pessoa perde o interesse. Colocar um elemento, um movimento de câmera ou uma reação do personagem.")
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
        if R.get("origem_efeitos"):
            L += ["", "**O que cada arquivo de efeito é de verdade (segundo a fonte)**: conferir se bate com o papel dele na cena:", ""]
            for src, o in R["origem_efeitos"].items():
                L.append(f"- `{src}` → {o.get('descricao')} · licença {o.get('licenca') or '?'} · {o.get('fonte') or ''}")
        if R.get("sem_musica"):
            L += ["", "Sem faixa de música no projeto."]
        L.append("")
    if R.get("comparacao"):
        c = R["comparacao"]
        L += ["## Narração × roteiro", "", f"- {c['palavras_roteiro']} palavras no roteiro, {c['palavras_ouvidas']} ouvidas · diferença {c['wer'] * 100:.1f}%",
              f"- Transcrição: {R['transcricao']['texto']}", ""]
    rv = R.get("ritmo", {})
    L += ["## Ritmo (retenção)", "",
          f"- Elementos novos na tela: {len(rv.get('eventos', []))} momentos · cortes de cena em {rv.get('cortes')} · plano médio {rv.get('plano_medio_s')} s (maior {rv.get('plano_max_s')} s)",
          f"- Trechos sem novidade de {SEM_NOVIDADE_MEDIO} s ou mais: {rv.get('lacunas') or 'nenhum'}"]
    if R.get("fala"):
        f_ = R["fala"]
        L += [f"- Voz começa em {f_['primeira_palavra']} s · {f_['ppm']} palavras/min · pausas de {SILENCIO_MEDIO} s ou mais: {[(x['de'], x['dur']) for x in f_['silencios']] or 'nenhuma'}"]
    if R.get("efeitos_no_mix"):
        L += ["- Quanto cada efeito aparece por cima da voz no mix: " + ", ".join(f"{e['id']} {e['ganho_LU']:+} LU" for e in R["efeitos_no_mix"] if e["ganho_LU"] is not None)]
    L += [""]
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
