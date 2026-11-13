"""Caçador de canais novos (o "niche finder" do vídeo) e checagem de "já modelaram?".

Sem API do YouTube: usa o yt-dlp que a Watch Skill instalou (~/.watch-skill/bin/yt-dlp.exe).

  cacar   — busca vídeos recentes por termos (em vários idiomas), junta os canais, mede cada um e guarda só os
            canais cujo PRIMEIRO vídeo longo saiu há N semanas ou menos. Gera canais.json, canais.md e canais.html
            (cards). Vai gravando a cada canal medido, então dá para abrir o HTML enquanto roda.
  checar  — procura uma ideia/título adaptado no YouTube e lista quem já fez (canal, views, data), para saber se
            alguém já modelou no idioma/país de destino.
  escada  — nicho → subnichos → micronichos NO IDIOMA DE DESTINO, a partir do autocompletar do YouTube daquele
            país, medindo procura, consumo (views) e se está vivo (último mês). Ideias só com dado.
  python cacador.py escada "<tema>" --idioma de --saida <pasta> [--sub 10 --abrir 3 --micro 6]

Uso:
  python cacador.py cacar  --buscas buscas.json --saida <pasta> [--semanas 3] [--periodo mes] [--por-busca 25]
                           [--max-videos 60] [--min-duracao 240] [--bom-melhor 10000] [--bom-total 0]
  python cacador.py checar "<título ou ideia>" [--n 15] [--periodo qualquer|ano|mes|semana] --saida <pasta>

buscas.json: {"pt": ["história de games", ...], "es": [...], "en": [...], "de": [...], "fr": [...]}
Nada aqui é inventado: o que não vier do YouTube fica vazio e aparece como "?".
"""
import argparse, base64, datetime as dt, html, json, os, statistics, subprocess, sys, time
from pathlib import Path

BIN = Path.home() / ".watch-skill" / "bin"
import shutil
if (BIN / "yt-dlp.exe").exists():
    YTDLP_CMD = [str(BIN / "yt-dlp.exe")]
elif shutil.which("yt-dlp"):
    YTDLP_CMD = [shutil.which("yt-dlp")]
else:  # outra máquina: usa o yt-dlp instalado no Python (python -m pip install yt-dlp)
    YTDLP_CMD = [sys.executable, "-m", "yt_dlp"]
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PATH=str(BIN) + os.pathsep + os.environ.get("PATH", ""))
HOJE = dt.date.today()
PAUSA = 1.5  # segundos entre chamadas, para o YouTube não bloquear (erro 429)

PERIODOS = {"hora": 1, "hoje": 2, "semana": 3, "mes": 4, "ano": 5}


def sp_filtro(periodo, ordem=None):
    """Filtro de busca do YouTube: tipo = vídeo + data de envio (protobuf em base64).
    ordem="views" = ordenar pelos mais vistos (pega quem está explodindo agora, não só os canais grandes)."""
    f = b"\x10\x01"  # tipo: vídeo
    if periodo in PERIODOS:
        f = bytes([0x08, PERIODOS[periodo]]) + f
    pre = b"\x08\x03" if ordem == "views" else b""
    return base64.urlsafe_b64encode(pre + b"\x12" + bytes([len(f)]) + f).decode()


def yt(args, tentativas=3):
    for i in range(tentativas):
        p = subprocess.run([*YTDLP_CMD, "--no-warnings", *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=ENV)
        if p.returncode == 0 or p.stdout.strip():
            time.sleep(PAUSA)
            return p.stdout
        err = (p.stderr.strip().splitlines() or [""])[-1]
        if "429" in err or "Too Many" in err:
            espera = 60 * (i + 1)
            print(f"  YouTube pediu calma (429). Esperando {espera}s…", flush=True)
            time.sleep(espera)
            continue
        print(f"  yt-dlp: {err[:200]}", flush=True)
        return ""
    return ""


def linhas_json(out):
    return [json.loads(l) for l in out.splitlines() if l.strip().startswith("{")]


def buscar(termo, n, periodo, ordem=None):
    q = termo.replace(" ", "+")
    url = f"https://www.youtube.com/results?search_query={q}&sp={sp_filtro(periodo, ordem)}"
    return linhas_json(yt(["-j", "--flat-playlist", "--playlist-end", str(n), url]))


def data_video(vid):
    """Data de envio e idioma ORIGINAL do vídeo (a página do vídeo traz o idioma real; títulos de listas/buscas
    podem vir traduzidos automaticamente pelo YouTube)."""
    out = yt(["--skip-download", "--print", "%(upload_date)s\t%(language)s", f"https://www.youtube.com/watch?v={vid}"]).strip()
    try:
        data, idioma = out.splitlines()[-1].split("\t")
        return dt.datetime.strptime(data, "%Y%m%d").date(), (None if idioma in ("NA", "None", "") else idioma)
    except Exception:
        return None, None


PARE = set("""a o as os de da do das dos e em no na nos nas um uma para por com sem que se ao à é the a an and or of to in on
for with you your is are was this that it its how why what my i we de la le les des du un une et en au aux pour par avec
sur est ce qui que der die das und ein eine zu im in mit von den dem ist du ihr wie was el los las del y con por para es
qué cómo vs""".split())


def palavras_canal(titulos):
    """Palavras e pares de palavras que se repetem nos títulos e em quantos % dos vídeos aparecem (base para dizer se
    o canal é nicho, subnicho ou micronicho com dado, e não com opinião)."""
    import re
    conj = []
    for t in titulos:
        w = [x for x in re.findall(r"[\wÀ-ÿ]+", (t or "").lower()) if x not in PARE and (len(x) > 1 or x.isdigit())]
        conj.append(set(w) | {f"{a} {b}" for a, b in zip(w, w[1:])})
    cont = {}
    for s in conj:
        for x in s:
            cont[x] = cont.get(x, 0) + 1
    n = max(len(titulos), 1)
    top = sorted(((k, v) for k, v in cont.items() if v >= 2), key=lambda kv: (-kv[1], -len(kv[0])))
    res = []
    for k, v in top:
        # pula a palavra solta quando um par que a contém aparece no mesmo número de vídeos ("gta" x "gta 6")
        if " " not in k and any(k in o.split() and v == cont[o] for o, _ in top if " " in o):
            continue
        res.append({"termo": k, "videos": v, "pct": round(100 * v / n)})
        if len(res) == 8:
            break
    return res


def medir_canal(cid, max_videos, min_dur):
    out = yt(["-J", "--flat-playlist", "--playlist-end", str(max_videos + 1),
              f"https://www.youtube.com/channel/{cid}/videos"])
    if not out.strip():
        return {"erro": "não abriu a aba de vídeos"}
    d = json.loads(out)
    ents = [e for e in d.get("entries") or [] if e.get("id")]
    base = {"id": cid, "nome": d.get("channel") or d.get("uploader"), "inscritos": d.get("channel_follower_count"),
            "url": f"https://www.youtube.com/channel/{cid}", "descricao": (d.get("description") or "")[:300]}
    if len(ents) > max_videos:
        return {**base, "descartado": f"mais de {max_videos} vídeos longos (não é canal novo)"}
    if not ents:
        return {**base, "descartado": "sem vídeos longos"}
    primeiro, idioma = data_video(ents[-1]["id"])  # a aba vem do mais novo para o mais velho
    if idioma and not idioma.startswith("en"):
        # pede de novo a lista no idioma do canal para ter os títulos ORIGINAIS (não traduzidos)
        out2 = yt(["-J", "--flat-playlist", "--playlist-end", str(max_videos + 1), "--extractor-args",
                   f"youtube:lang={idioma.split('-')[0]}", f"https://www.youtube.com/channel/{cid}/videos"])
        if out2.strip():
            orig = {e["id"]: e.get("title") for e in json.loads(out2).get("entries") or [] if e.get("id")}
            for e in ents:
                e["title"] = orig.get(e["id"]) or e.get("title")
    base["idioma_real"] = idioma
    vids = [{"id": e["id"], "titulo": e.get("title"), "views": e.get("view_count"), "dur": e.get("duration")}
            for e in ents]
    base["palavras"] = palavras_canal([v["titulo"] for v in vids])
    longos = [v for v in vids if (v["dur"] or 0) >= min_dur]
    views = [v["views"] for v in vids if v["views"] is not None]
    dias = (HOJE - primeiro).days if primeiro else None
    return {**base, "n_videos": len(vids), "n_longos": len(longos), "primeiro_video": str(primeiro) if primeiro else None,
            "dias_desde_primeiro": dias, "views_total": sum(views) if views else None,
            "views_mediana": int(statistics.median(views)) if views else None,
            "melhor": max(vids, key=lambda v: v["views"] or 0),
            "views_por_dia": round(sum(views) / max(dias, 1)) if views and dias is not None else None,
            "videos": sorted(vids, key=lambda v: -(v["views"] or 0))[:6]}


def fmt(n):
    if n is None:
        return "?"
    return f"{n/1e6:.1f} mi" if n >= 1e6 else f"{n/1e3:.1f} mil" if n >= 1e3 else str(n)


def temas(c):
    return ", ".join(f"{p['termo']} {p['pct']}%" for p in (c.get("palavras") or [])[:4]) or "?"


def gravar(saida, canais, info):
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "canais.json").write_text(json.dumps({"info": info, "canais": canais}, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    bons = [c for c in canais if c.get("aprovado")]
    resto = [c for c in canais if c.get("n_videos") and not c.get("aprovado")]
    md = [f"# Canais novos — {info['nicho']}", "",
          f"Gerado em {HOJE:%d/%m/%Y}. Critérios: primeiro vídeo longo há até {info['semanas']} semanas; "
          f"'performando bem' = {info['regra_bom']}. Buscas: {info['n_buscas']} · canais vistos: {info['n_vistos']}.",
          "", "Idioma = idioma real do canal (da página do vídeo), não o da busca. Temas = palavras que se repetem nos "
          "títulos e em quantos % dos vídeos aparecem.", "",
          "| ✔ | Canal | Idioma | Inscritos | Vídeos | 1º vídeo | Views total | Mediana | Views/dia | Temas | Melhor vídeo |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in bons + resto:
        m = c["melhor"]
        md.append(f"| {'✔' if c.get('aprovado') else ''} | [{c['nome']}]({c['url']}) | {c.get('idioma','?')} | "
                  f"{fmt(c['inscritos'])} | {c['n_videos']} | {c['primeiro_video'] or '?'} | {fmt(c['views_total'])} | "
                  f"{fmt(c['views_mediana'])} | {fmt(c['views_por_dia'])} | {temas(c)} | "
                  f"[{(m['titulo'] or '')[:60]}](https://youtu.be/{m['id']}) ({fmt(m['views'])}) |")
    (saida / "canais.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    def card(c):
        vids = "".join(
            f'<li><a href="https://youtu.be/{v["id"]}" target="_blank">{html.escape(v["titulo"] or "?")}</a>'
            f' <b>{fmt(v["views"])}</b></li>' for v in c["videos"])
        m = c["melhor"]
        return f'''<article class="{'ok' if c.get('aprovado') else ''}">
<a href="https://youtu.be/{m['id']}" target="_blank"><img src="https://i.ytimg.com/vi/{m['id']}/mqdefault.jpg" alt=""></a>
<h2><a href="{c['url']}" target="_blank">{html.escape(c['nome'] or '?')}</a> <span>{c.get('idioma','?')}</span></h2>
<p class="n">{fmt(c['inscritos'])} inscritos · {c['n_videos']} vídeos · 1º vídeo {c['primeiro_video'] or '?'}
 ({c['dias_desde_primeiro'] if c['dias_desde_primeiro'] is not None else '?'} dias) · {fmt(c['views_total'])} views · {fmt(c['views_por_dia'])}/dia</p>
<p class="t">Temas nos títulos: {html.escape(temas(c))}</p>
<p class="t">Achado pela busca ({c.get('idioma_busca','?')}): “{html.escape(c.get('termo',''))}”</p><ol>{vids}</ol></article>'''

    pagina = f'''<!doctype html><html lang="pt-br"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Canais novos</title><style>
:root{{--bg:#f6f5f2;--card:#fff;--tx:#1d1d1f;--mut:#6b6b70;--ok:#1f8a4c;--bd:#e3e1dc}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151517;--card:#1f1f22;--tx:#ececef;--mut:#9a9aa1;--ok:#3fbf75;--bd:#2c2c31}}}}
body{{margin:0;background:var(--bg);color:var(--tx);font:15px/1.45 system-ui,sans-serif;padding:16px}}
h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--mut);margin:0 0 16px}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}}
article{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:12px;overflow:hidden}}
article.ok{{border:2px solid var(--ok)}} img{{width:100%;border-radius:8px;display:block}}
h2{{font-size:16px;margin:10px 0 4px}} h2 span{{font-size:12px;color:var(--mut);text-transform:uppercase}}
a{{color:inherit}} .n,.t{{color:var(--mut);font-size:13px;margin:2px 0}} ol{{padding-left:18px;font-size:13px;margin:8px 0 0}}
</style><h1>Canais novos — {html.escape(info['nicho'])}</h1>
<p class="sub">{HOJE:%d/%m/%Y} · primeiro vídeo há até {info['semanas']} semanas · borda verde = {html.escape(info['regra_bom'])}
 · {len(bons)} aprovados de {len(bons)+len(resto)} canais novos ({info['n_vistos']} canais vistos)</p>
<main>{"".join(card(c) for c in bons + resto)}</main></html>'''
    (saida / "canais.html").write_text(pagina, encoding="utf-8")


def cmd_cacar(a):
    buscas = json.loads(Path(a.buscas).read_text(encoding="utf-8"))
    saida = Path(a.saida)
    cache_f = saida / "cache_canais.json"
    cache = json.loads(cache_f.read_text(encoding="utf-8")) if cache_f.exists() else {}
    regra = f"melhor vídeo ≥ {a.bom_melhor:,} views".replace(",", ".") + (
        f" e total ≥ {a.bom_total:,}".replace(",", ".") if a.bom_total else "")
    achados = {}  # canal_id -> (idioma, termo)
    n_buscas = 0
    for idioma, termos in buscas.items():
        for termo in termos:
            n_buscas += 1
            res = buscar(termo, a.por_busca, a.periodo)
            novos = 0
            for r in res:
                cid = r.get("channel_id")
                if cid and (r.get("duration") or 0) >= a.min_duracao and cid not in achados:
                    achados[cid] = (idioma, termo); novos += 1
            print(f"[{idioma}] “{termo}”: {len(res)} vídeos, {novos} canais novos na lista", flush=True)
    print(f"\n{len(achados)} canais para medir…", flush=True)
    canais = []
    info = {"nicho": a.nicho or ", ".join(sum(buscas.values(), [])[:3]), "semanas": a.semanas, "regra_bom": regra,
            "n_buscas": n_buscas, "n_vistos": len(achados), "periodo_busca": a.periodo, "data": str(HOJE)}
    for i, (cid, (idioma, termo)) in enumerate(achados.items(), 1):
        c = cache.get(cid)
        if not c or ("descartado" not in c and "erro" not in c and "palavras" not in c):
            c = medir_canal(cid, a.max_videos, a.min_duracao)  # cache antigo sem idioma real: mede de novo
        cache[cid] = c
        cache_f.parent.mkdir(parents=True, exist_ok=True)
        cache_f.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        motivo = c.get("descartado") or c.get("erro")
        if not motivo and (c["dias_desde_primeiro"] is None or c["dias_desde_primeiro"] > a.semanas * 7):
            motivo = f"primeiro vídeo em {c['primeiro_video'] or '?'} (antigo)"
        if motivo:
            print(f"  {i}/{len(achados)} {c.get('nome') or cid}: fora — {motivo}", flush=True)
            continue
        c = {**c, "idioma_busca": idioma, "termo": termo,
             "idioma": (c.get("idioma_real") or "?").split("-")[0]}
        c["aprovado"] = (c["melhor"]["views"] or 0) >= a.bom_melhor and (c["views_total"] or 0) >= a.bom_total
        canais.append(c)
        canais.sort(key=lambda x: (not x["aprovado"], -(x["views_por_dia"] or 0)))
        gravar(saida, canais, info)
        print(f"  {i}/{len(achados)} {c['nome']}: NOVO ({c['dias_desde_primeiro']} dias, {fmt(c['views_total'])} views)"
              f"{' ✔ performando' if c['aprovado'] else ''}", flush=True)
    gravar(saida, canais, info)
    print(f"\nPronto: {sum(c['aprovado'] for c in canais)} aprovados, {len(canais)} canais novos. "
          f"Abra {saida / 'canais.html'}", flush=True)


def idioma_titulo(vid):
    """Idioma real e título ORIGINAL de um vídeo (a página do vídeo não vem traduzida)."""
    out = yt(["--skip-download", "--print", "%(language)s\t%(title)s", f"https://www.youtube.com/watch?v={vid}"]).strip()
    try:
        idioma, titulo = out.splitlines()[-1].split("\t", 1)
        return (None if idioma in ("NA", "None", "") else idioma), titulo
    except Exception:
        return None, None


def cmd_checar(a):
    res = buscar(a.ideia, a.n, a.periodo)
    conf = a.conferir_idioma
    linhas = [f"# Já modelaram? — “{a.ideia}”", "", f"Busca no YouTube em {HOJE:%d/%m/%Y} (período: {a.periodo}).",
              f"Idioma real e título original conferidos na página dos {conf} primeiros (os da busca podem vir traduzidos)."
              if conf else "Idioma não conferido (os títulos da busca podem vir traduzidos pelo YouTube).", "",
              "| # | Idioma real | Título | Canal | Views | Duração |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(res, 1):
        d = r.get("duration")
        idioma, titulo = idioma_titulo(r.get("id")) if i <= conf else (None, None)
        linhas.append(f"| {i} | {idioma or ('?' if i <= conf else '—')} | [{(titulo or r.get('title') or '?')[:80]}]"
                      f"(https://youtu.be/{r.get('id')}) | {r.get('channel') or '?'} | "
                      f"{fmt(r.get('view_count'))} | {f'{int(d)//60}:{int(d)%60:02d}' if d else '?'} |")
    texto = "\n".join(linhas) + "\n"
    if a.saida:
        p = Path(a.saida); p.mkdir(parents=True, exist_ok=True)
        nome = "".join(ch if ch.isalnum() else "_" for ch in a.ideia.lower())[:50]
        (p / f"checar_{nome}.md").write_text(texto, encoding="utf-8")
    print(texto)


# ---------- escada: nicho → subnichos → micronichos, no idioma de destino, só com dado ----------
LOCAL = {"pt": ("pt-BR", "BR"), "es": ("es", "MX"), "en": ("en", "US"), "fr": ("fr", "FR"), "de": ("de", "DE"),
         "it": ("it", "IT")}
LETRAS = {"pt": "abcdefghijlmnopqrstuv", "es": "abcdefghijlmnopqrstuv", "en": "abcdefghijklmnoprstw",
          "fr": "abcdefghijlmnopqrstuv", "de": "abcdefghijklmnoprstuwz", "it": "abcdefghilmnopqrstuv"}


def autocompletar(q, idioma):
    import urllib.parse, urllib.request
    hl, gl = LOCAL.get(idioma, (idioma, ""))
    u = ("https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&hl=" + hl + "&gl=" + gl +
         "&q=" + urllib.parse.quote(q))
    try:
        r = json.loads(urllib.request.urlopen(u, timeout=15).read().decode("utf-8", "replace"))[1]
        time.sleep(0.3)
        return [s.strip().lower() for s in r]
    except Exception:
        return []


def expandir(tema, idioma, k):
    """O que o povo DAQUELE idioma digita no YouTube em volta do tema (autocompletar). Ordem = mais buscado antes."""
    import re
    base = set(re.findall(r"\w+", tema.lower()))
    vistos, lista = set(), []
    for i, q in enumerate([tema + " "] + [f"{tema} {l}" for l in LETRAS.get(idioma, "abcdefghijlmnopqrstuv")]):
        for pos, s in enumerate(autocompletar(q, idioma), 1):
            chave = frozenset(w for w in re.findall(r"\w+", s) if w not in base)
            if s != tema.lower() and chave and chave not in vistos:
                # top = estava entre as 10 primeiras sugestões do tema puro (as mais buscadas)
                vistos.add(chave); lista.append((s, pos if i == 0 else None))
    return lista[:k]


def medir_termo(termo, idioma):
    """Procura x oferta de um termo, no idioma: procura = quantas buscas o YouTube completa a partir dele (0–10);
    oferta = views dos 10 mais vistos da busca geral; vivo = vídeos enviados no último mês e suas views."""
    # sem "youtube:lang": em outro idioma o YouTube escreve "1,2 k"/"Mio." e as views saem erradas
    lang = []
    procura = len(autocompletar(termo + " ", idioma))
    q = termo.replace(" ", "+")
    geral = linhas_json(yt(["-j", "--flat-playlist", "--playlist-end", "20", *lang,
                            f"https://www.youtube.com/results?search_query={q}&sp={sp_filtro('qualquer')}"]))
    mes = linhas_json(yt(["-j", "--flat-playlist", "--playlist-end", "20", *lang,
                          f"https://www.youtube.com/results?search_query={q}&sp={sp_filtro('mes')}"]))
    tv = sorted((v.get("view_count") or 0 for v in geral), reverse=True)[:10]
    mv = sorted((v.get("view_count") or 0 for v in mes), reverse=True)[:10]
    canais = {}
    for v in geral[:10]:
        canais[v.get("channel") or "?"] = canais.get(v.get("channel") or "?", 0) + (v.get("view_count") or 0)
    dono = max(canais.values()) / max(1, sum(canais.values())) if canais else None
    exemplos = sorted(mes, key=lambda v: -(v.get("view_count") or 0))[:3]
    return {"termo": termo, "procura": procura, "views_tipicas": int(statistics.median(tv)) if tv else None,
            "videos_mes": len(mes), "views_mes_mediana": int(statistics.median(mv)) if mv else None,
            "canais_top10": len(canais), "dono": round(dono, 2) if dono is not None else None,
            "exemplos_mes": [{"titulo": v.get("title"), "views": v.get("view_count"), "canal": v.get("channel"),
                              "id": v.get("id")} for v in exemplos]}


def cmd_escada(a):
    saida = Path(a.saida); saida.mkdir(parents=True, exist_ok=True)
    print(f"Nível 1 (nicho): {a.tema} [{a.idioma}]", flush=True)
    raiz = medir_termo(a.tema, a.idioma)
    subs = []
    for s, pos in expandir(a.tema, a.idioma, a.sub):
        m = medir_termo(s, a.idioma); m["top_autocompletar"] = pos; subs.append(m)
        print(f"  sub: {s} | procura {m['procura']} | típicas {fmt(m['views_tipicas'])} | mês {m['videos_mes']} "
              f"vídeos, mediana {fmt(m['views_mes_mediana'])}", flush=True)
    # micronichos: abre os subnichos com mais procura E consumo no último mês
    # ordem: procura x views do mês x espaço (termo dominado por um canal só — ex.: trailer oficial — cai)
    chave = lambda m: (m["procura"] or 0) * (m["views_mes_mediana"] or 0) * (1.05 - (m["dono"] if m["dono"] is not None else 1))
    micros = {}
    for s in sorted(subs, key=chave, reverse=True)[:a.abrir]:
        micros[s["termo"]] = []
        for t, pos in expandir(s["termo"], a.idioma, a.micro):
            m = medir_termo(t, a.idioma); m["top_autocompletar"] = pos; micros[s["termo"]].append(m)
            print(f"    micro: {t} | procura {m['procura']} | típicas {fmt(m['views_tipicas'])} | mês {m['videos_mes']} "
                  f"vídeos, mediana {fmt(m['views_mes_mediana'])}", flush=True)
    dados = {"tema": a.tema, "idioma": a.idioma, "data": str(HOJE), "nicho": raiz, "subnichos": subs, "micronichos": micros}
    (saida / f"escada_{a.idioma}.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")

    def linha(m):
        ex = m["exemplos_mes"][0] if m["exemplos_mes"] else None
        exs = f"[{(ex['titulo'] or '')[:55]}](https://youtu.be/{ex['id']}) ({fmt(ex['views'])}, {ex['canal']})" if ex else "—"
        top = f"{m['top_autocompletar']}º" if m.get("top_autocompletar") else "—"
        return (f"| {m['termo']} | {top} | {m['procura']} | {fmt(m['views_tipicas'])} | {m['videos_mes']} | "
                f"{fmt(m['views_mes_mediana'])} | {m['canais_top10']} | "
                f"{'?' if m['dono'] is None else str(round(100 * m['dono'])) + '%'} | {exs} |")
    cab = ["| Termo (busca real) | Posição no autocompletar | Procura 0–10 | Views típicas (top 10) | Vídeos no último mês | Mediana do mês | "
           "Canais no top 10 | Dono | Mais visto do mês |", "|---|---|---|---|---|---|---|---|---|"]
    raiz["top_autocompletar"] = None
    md = [f"# Escada de nicho — {a.tema} [{a.idioma}]", "",
          f"Coletado em {HOJE:%d/%m/%Y}. Todos os termos vêm do **autocompletar do YouTube no idioma {a.idioma}** "
          f"(o que as pessoas de lá digitam). Nada foi inventado.", "",
          "**Como ler:** *Posição no autocompletar* = em que lugar o YouTube sugere o termo quando a pessoa digita o tema "
          "(1º = o mais buscado; — = só aparece com mais letras digitadas, procura menor). *Procura* = quantas buscas o YouTube completa a partir do termo (mais = mais gente procura). "
          "*Views típicas* = mediana dos 10 mais vistos da busca (consumo do tema em geral). *Vídeos no último mês* e "
          "*Mediana do mês* = o tema está vivo agora e quanto rende hoje (até 20 vídeos lidos). *Dono* = fatia das views "
          "do top 10 que fica com um canal só (alto = dominado). Os títulos da busca podem vir traduzidos pelo YouTube; "
          "o idioma real dos vídeos não foi conferido aqui (use `checar`).", "",
          "## Nicho", "", *cab, linha(raiz), "", "## Subnichos", "", *cab,
          *[linha(m) for m in sorted(subs, key=chave, reverse=True)]]
    for s, ms in micros.items():
        md += ["", f"## Micronichos de “{s}”", "", *cab, *[linha(m) for m in sorted(ms, key=chave, reverse=True)]]
    md += ["", "## Análise (Claude)", "", "_Para cada ideia: o termo real, os números acima e o exemplo do mês. Sem dado = "
           "não recomendar. Separar dado de hipótese._", ""]
    (saida / f"escada_{a.idioma}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Pronto: {saida / f'escada_{a.idioma}.md'}", flush=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("cacar")
    p.add_argument("--buscas", required=True); p.add_argument("--saida", required=True); p.add_argument("--nicho")
    p.add_argument("--semanas", type=int, default=3); p.add_argument("--periodo", default="mes", choices=list(PERIODOS))
    p.add_argument("--por-busca", type=int, default=25); p.add_argument("--max-videos", type=int, default=60)
    p.add_argument("--min-duracao", type=int, default=240)
    p.add_argument("--bom-melhor", type=int, default=10000); p.add_argument("--bom-total", type=int, default=0)
    p = sp.add_parser("checar")
    p.add_argument("ideia"); p.add_argument("--n", type=int, default=15); p.add_argument("--saida")
    p.add_argument("--periodo", default="qualquer", choices=["qualquer", *PERIODOS])
    p.add_argument("--conferir-idioma", type=int, default=8, help="quantos dos primeiros têm o idioma conferido (0 = nenhum)")
    p = sp.add_parser("escada")
    p.add_argument("tema"); p.add_argument("--idioma", required=True, help="pt, es, en, fr, de, it")
    p.add_argument("--saida", required=True); p.add_argument("--sub", type=int, default=10)
    p.add_argument("--abrir", type=int, default=3, help="quantos subnichos abrir em micronichos")
    p.add_argument("--micro", type=int, default=6)
    a = ap.parse_args()
    {"cacar": cmd_cacar, "checar": cmd_checar, "escada": cmd_escada}[a.cmd](a)


if __name__ == "__main__":
    main()
