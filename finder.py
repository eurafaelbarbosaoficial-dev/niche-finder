"""Niche Finder — acha CANAIS NOVOS (criados há até 30 dias) que já performam bem com vídeos longos, em vários nichos
amplos e em PT, ES, EN, DE e FR. Grava docs/dados.json, que o site (docs/index.html) lê e mostra em cards.

Uso:  python -I finder.py [--por-busca 20] [--dias-canal 30] [--bom-video 50000] [--min-duracao 240]
"Performando" = o canal tem pelo menos UM vídeo longo com 50 mil views ou mais (não é a soma do canal).

Como funciona (cada rodada):
1. Busca no YouTube os termos de categorias.json (vídeos enviados no último mês).
2. Para cada canal achado que ainda não foi descartado:
   - mais de 60 vídeos → fora para sempre (canal grande);
   - 1º vídeo mais velho que 30 dias → fora para sempre (canal com vídeos antigos);
   - data de criação (aba "Sobre") mais velha que 30 dias → fora para sempre (canal antigo que recomeçou);
   - senão é CANAL NOVO: mede views dos vídeos longos (4 min ou mais) e guarda o histórico.
3. Canais novos já conhecidos são medidos de novo a cada rodada (views crescem) até passarem de 30 dias.
Só vídeos longos contam (Shorts e vídeos com menos de 4 min ficam de fora). Nada é inventado: o que o YouTube não
informou fica vazio ("?" no site).
"""
import argparse, datetime as dt, json, os, re, sys, time, urllib.request
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")  # Windows: -I ignora PYTHONIOENCODING
    except Exception:
        pass
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from cacador import yt, buscar, data_video, palavras_canal  # noqa: E402

ESTADO = AQUI / "estado"
CACHE_F = ESTADO / "canais.json"
DADOS_F = AQUI / "docs" / "dados.json"
LOG_F = ESTADO / "log.txt"
MESES = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
MAX_VIDEOS = 60


def agora():
    return dt.datetime.now().replace(microsecond=0)


def log(msg):
    linha = f"{agora():%d/%m %H:%M:%S} {msg}"
    print(linha, flush=True)
    with LOG_F.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def ler(f, padrao):
    try:
        return json.loads(Path(f).read_text(encoding="utf-8"))
    except Exception:
        return padrao


def gravar(f, obj):
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, f)


def data_criacao(cid):
    """Data em que o canal foi criado ("Joined Oct 12, 2026" na aba Sobre). None se não achar."""
    req = urllib.request.Request(f"https://www.youtube.com/channel/{cid}/about",
                                 headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9",
                                          "Cookie": "CONSENT=YES+1"})
    for _ in range(2):
        try:
            txt = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
            m = re.search(r'"joinedDateText":\{"content":"Joined (\w{3})\w* (\d{1,2}), (\d{4})"', txt)
            return dt.date(int(m.group(3)), MESES[m.group(1)], int(m.group(2))).isoformat() if m else None
        except Exception:
            time.sleep(3)
    return None


def lista_videos(cid, lang=None):
    args = ["-J", "--flat-playlist", "--playlist-end", str(MAX_VIDEOS + 1)]
    if lang and not lang.startswith("en"):
        args += ["--extractor-args", f"youtube:lang={lang.split('-')[0]}"]
    out = yt(args + [f"https://www.youtube.com/channel/{cid}/videos"])
    if not out.strip():
        return None
    try:
        return json.loads(out)
    except Exception:
        return None


def medir_videos(d, min_dur):
    ents = [e for e in d.get("entries") or [] if e.get("id")]
    longos = [{"id": e["id"], "titulo": e.get("title"), "views": e.get("view_count"), "dur": e.get("duration")}
              for e in ents if (e.get("duration") or 0) >= min_dur]
    views = [v["views"] for v in longos if v["views"] is not None]
    return {"inscritos": d.get("channel_follower_count"), "n_longos": len(longos),
            "views_total": sum(views) if views else 0,
            "melhor": max(longos, key=lambda v: v["views"] or 0) if longos else None,
            "videos": sorted(longos, key=lambda v: -(v["views"] or 0))[:5],
            "palavras": palavras_canal([v["titulo"] for v in longos])}


def checar_novo(cid, dias_canal, min_dur):
    """Primeira checagem de um canal. Devolve o registro (status: novo | fora | tentar)."""
    hoje = dt.date.today()
    d = lista_videos(cid)
    if d is None:
        return {"status": "tentar", "motivo": "não abriu a aba de vídeos"}
    base = {"nome": d.get("channel") or d.get("uploader"), "inscritos": d.get("channel_follower_count")}
    ents = [e for e in d.get("entries") or [] if e.get("id")]
    if len(ents) > MAX_VIDEOS:
        return {**base, "status": "fora", "motivo": "canal grande (mais de 60 vídeos)"}
    if not ents:
        return {**base, "status": "tentar", "motivo": "sem vídeos na aba de vídeos"}
    primeiro, lang = data_video(ents[-1]["id"])
    if primeiro and (hoje - primeiro).days > dias_canal:
        return {**base, "status": "fora", "motivo": f"vídeos antigos (1º em {primeiro})"}
    criado = data_criacao(cid)
    if not criado:
        return {**base, "status": "tentar", "motivo": "não consegui ler a data de criação"}
    if (hoje - dt.date.fromisoformat(criado)).days > dias_canal:
        return {**base, "status": "fora", "motivo": f"canal antigo (criado em {criado})"}
    if lang and not lang.startswith("en"):  # títulos originais, não os traduzidos pelo YouTube
        d = lista_videos(cid, lang) or d
    return {**base, "status": "novo", "criado": criado, "primeiro_video": str(primeiro) if primeiro else None,
            "idioma": (lang or "?").split("-")[0], **medir_videos(d, min_dur)}


def montar_dados(cache, info, cfg, a):
    hoje = dt.date.today()
    canais, fora = [], {}
    for cid, c in cache.items():
        if c.get("status") == "fora":
            k = c["motivo"].split(" (")[0]
            fora[k] = fora.get(k, 0) + 1
        if c.get("status") != "novo":
            continue
        dias = (hoje - dt.date.fromisoformat(c["criado"])).days
        if dias > a.dias_canal:
            continue
        d1 = (hoje - dt.date.fromisoformat(c["primeiro_video"])).days if c.get("primeiro_video") else None
        canais.append({**{k: c.get(k) for k in ("nome", "inscritos", "idioma", "categoria", "grupo", "termo", "criado",
                                                "primeiro_video", "n_longos", "views_total", "melhor", "videos",
                                                "palavras", "historico", "visto_em")},
                       "id": cid, "url": f"https://www.youtube.com/channel/{cid}", "dias_canal": dias,
                       "dias_primeiro": d1, "views_dia": round((c.get("views_total") or 0) / max(d1 or dias, 1)),
                       "performando": ((c.get("melhor") or {}).get("views") or 0) >= a.bom_video})
    return {"atualizado": agora().isoformat(), "rodada": info,
            "criterios": {"dias_canal": a.dias_canal, "bom_video": a.bom_video, "min_duracao": a.min_duracao,
                          "idiomas": ["pt", "es", "en", "de", "fr"]},
            "categorias": {k: v["grupo"] for k, v in cfg.items()},
            "checados": sum(1 for c in cache.values() if c.get("status") in ("novo", "fora")),
            "fora": fora, "canais": canais}


def publicar():
    """Envia docs/ para o GitHub (o GitHub Pages mostra o site). Erro aqui não para a busca."""
    import subprocess
    try:
        subprocess.run(["git", "add", "docs", "estado/canais.json"], cwd=AQUI, capture_output=True, timeout=60)
        subprocess.run(["git", "commit", "-m", f"dados {agora():%d/%m %H:%M}"], cwd=AQUI, capture_output=True, timeout=60)
        p = subprocess.run(["git", "push", "-q"], cwd=AQUI, capture_output=True, text=True, timeout=180)
        log("site publicado no GitHub" if p.returncode == 0 else f"não consegui publicar: {p.stderr.strip()[:200]}")
    except Exception as e:
        log(f"não consegui publicar: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--por-busca", type=int, default=20)
    ap.add_argument("--dias-canal", type=int, default=30)
    ap.add_argument("--bom-video", type=int, default=50000,
                    help="performando = o canal tem pelo menos UM vídeo longo com esse número de views ou mais")
    ap.add_argument("--min-duracao", type=int, default=240)
    ap.add_argument("--periodo", default="mes")
    ap.add_argument("--publicar", type=int, default=0,
                    help="manda o site para o GitHub a cada N minutos durante a rodada (0 = não manda)")
    a = ap.parse_args()
    ESTADO.mkdir(exist_ok=True)
    cfg = ler(AQUI / "categorias.json", {})
    cache = ler(CACHE_F, {})
    info = {"status": "buscando", "inicio": agora().isoformat(), "fase": "Buscando vídeos novos", "feito": 0, "total": 0}

    ultimo = {"push": 0.0}

    def salvar(forcar_push=False):
        gravar(CACHE_F, cache)
        gravar(DADOS_F, montar_dados(cache, info, cfg, a))
        if a.publicar and (forcar_push or time.time() - ultimo["push"] > a.publicar * 60):
            publicar()
            ultimo["push"] = time.time()

    salvar()
    achados = {}
    termos = [(cat, v["grupo"], lang, t) for cat, v in cfg.items() for lang in ("pt", "es", "en", "de", "fr")
              for t in v.get(lang, [])]
    for i, (cat, grupo, lang, termo) in enumerate(termos, 1):
        res = buscar(termo, a.por_busca, a.periodo)
        for r in res:
            cid = r.get("channel_id")
            if cid and (r.get("duration") or 0) >= a.min_duracao and cid not in achados:
                achados[cid] = (cat, grupo, termo)
        info.update(fase=f"Buscando vídeos novos ({i}/{len(termos)})", feito=i, total=len(termos))
        if i % 10 == 0:
            salvar()
        log(f"[{lang}] {cat}: “{termo}” → {len(res)} vídeos")

    # novos já conhecidos (para atualizar as views) + canais achados agora que ainda não foram descartados
    fila = [cid for cid, c in cache.items() if c.get("status") == "novo"]
    fila += [cid for cid in achados if cache.get(cid, {}).get("status") not in ("novo", "fora")]
    info.update(fase="Checando canais", feito=0, total=len(fila))
    log(f"{len(achados)} canais nas buscas · {len(fila)} para checar")
    for i, cid in enumerate(fila, 1):
        antigo = cache.get(cid, {})
        if antigo.get("status") == "novo":
            if (dt.date.today() - dt.date.fromisoformat(antigo["criado"])).days > a.dias_canal:
                cache[cid] = {**antigo, "status": "fora", "motivo": "passou de 30 dias"}
            else:
                d = lista_videos(cid, antigo.get("idioma"))
                if d:
                    antigo.update(medir_videos(d, a.min_duracao))
                cache[cid] = antigo
        else:
            cat, grupo, termo = achados[cid]
            cache[cid] = {**checar_novo(cid, a.dias_canal, a.min_duracao), "categoria": cat, "grupo": grupo,
                          "termo": termo, "visto_em": dt.date.today().isoformat()}
        c = cache[cid]
        if c.get("status") == "novo":
            h = c.setdefault("historico", [])
            h.append([agora().isoformat(timespec="minutes"), c.get("views_total") or 0])
            del h[:-60]
        log(f"  {i}/{len(fila)} {c.get('nome') or cid}: {c.get('status')}"
            f"{' — ' + c['motivo'] if c.get('motivo') and c.get('status') != 'novo' else ''}"
            f"{' · ' + str(c.get('views_total')) + ' views' if c.get('status') == 'novo' else ''}")
        info.update(feito=i)
        if i % 5 == 0:
            salvar()
    info.update(status="pronto", fase="Rodada concluída", fim=agora().isoformat())
    salvar(forcar_push=True)
    log("Rodada concluída.")


if __name__ == "__main__":
    main()
