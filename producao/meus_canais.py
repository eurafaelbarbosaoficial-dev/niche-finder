"""Acompanha os NOSSOS canais (pedido do dono em 13/11): a cada 3 h, pela API do YouTube.

Para cada canal de producao/canais.json com o campo "youtube" (link, @handle ou id UC…):
  - canal: inscritos, views totais, nº de vídeos (e a diferença em 24 h);
  - cada vídeo (até 50 mais recentes): views, curtidas, comentários, data, duração, e quanto ganhou em 24 h;
  - comentários mais recentes dos vídeos dos últimos 30 dias (texto e curtidas; o nome do autor NÃO é guardado);
  - os números do YouTube Studio que o dono mandou em print (producao/studio.json).
Histórico em estado/meus-canais.json (fora do site); resumo em docs/meus-canais.json (aba "Meus canais").
Custo na cota da API: ~1 ponto por chamada (cota grátis: 10.000 por dia).
Uso: python -I producao/meus_canais.py
"""
import datetime as dt, json, re, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(__file__).resolve().parents[1]
HIST = R / "estado" / "meus-canais.json"
API = "https://www.googleapis.com/youtube/v3/"


def chave():
    f = R / "estado" / "youtube-api.txt"
    return f.read_text(encoding="utf-8").strip() if f.exists() else None


def api(rec, **p):
    p["key"] = chave()
    return json.loads(urllib.request.urlopen(API + rec + "?" + urllib.parse.urlencode(p), timeout=30).read())


def canal_id(ref):
    ref = ref.strip()
    m = re.search(r"(UC[\w-]{22})", ref)
    if m:
        return m.group(1)
    h = re.search(r"@([\w.\-]+)", ref)
    h = h.group(1) if h else ref.rstrip("/").split("/")[-1]
    it = api("channels", part="id", forHandle="@" + h).get("items", [])
    return it[0]["id"] if it else None


def dur_seg(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    return sum(int(x or 0) * k for x, k in zip(m.groups(), (3600, 60, 1))) if m else None


def medir(c):
    cid = c.get("youtube_id") or canal_id(c["youtube"])
    if not cid:
        return None
    ch = api("channels", part="snippet,statistics,contentDetails", id=cid)["items"][0]
    st, up = ch["statistics"], ch["contentDetails"]["relatedPlaylists"]["uploads"]
    try:  # canal sem vídeo público ainda: o YouTube responde 404 para a lista de envios
        ids = [x["contentDetails"]["videoId"] for x in api("playlistItems", part="contentDetails", playlistId=up, maxResults=50).get("items", [])]
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        ids = []
    vids = []
    if ids:
        for v in api("videos", part="snippet,statistics,contentDetails", id=",".join(ids)).get("items", []):
            s = v["statistics"]
            vids.append({"id": v["id"], "titulo": v["snippet"]["title"], "postado": v["snippet"]["publishedAt"],
                         "dur": dur_seg(v["contentDetails"].get("duration")), "views": int(s.get("viewCount", 0)),
                         "curtidas": int(s.get("likeCount", 0)), "comentarios": int(s.get("commentCount", 0))})
    agora = dt.datetime.now(dt.timezone.utc)
    for v in vids:
        idade = (agora - dt.datetime.fromisoformat(v["postado"].replace("Z", "+00:00"))).days
        if idade <= 30 and v["comentarios"]:
            try:
                cs = api("commentThreads", part="snippet", videoId=v["id"], maxResults=20, order="time", textFormat="plainText").get("items", [])
                v["ultimos_comentarios"] = [{"texto": x["snippet"]["topLevelComment"]["snippet"]["textDisplay"][:400],
                                             "curtidas": x["snippet"]["topLevelComment"]["snippet"].get("likeCount", 0),
                                             "quando": x["snippet"]["topLevelComment"]["snippet"]["publishedAt"]} for x in cs]
            except Exception:
                v["ultimos_comentarios"] = []
    return {"youtube_id": cid, "nome_youtube": ch["snippet"]["title"], "foto": ch["snippet"]["thumbnails"].get("default", {}).get("url"),
            "inscritos": int(st.get("subscriberCount", 0)), "views": int(st.get("viewCount", 0)), "n_videos": int(st.get("videoCount", 0)), "videos": vids}


def delta(serie, h=24):
    """Quanto um número subiu nas últimas h horas (pela foto mais antiga dentro da janela)."""
    if len(serie) < 2:
        return None
    t1, v1 = serie[-1]
    lim = dt.datetime.fromisoformat(t1) - dt.timedelta(hours=h)
    base = next((x for x in serie if dt.datetime.fromisoformat(x[0]) >= lim), serie[0])
    return v1 - base[1] if base is not serie[-1] else None


def main():
    if not chave():
        sys.exit("Sem chave da API em estado/youtube-api.txt")
    canais = json.loads((R / "producao" / "canais.json").read_text(encoding="utf-8"))
    hist = json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else {}
    studio = json.loads((R / "producao" / "studio.json").read_text(encoding="utf-8")) if (R / "producao" / "studio.json").exists() else {}
    quando = dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")
    site = []
    for c in canais:
        base = {"id": c["id"], "nome": c["nome"], "idioma": c.get("idioma"), "youtube": c.get("youtube"), "studio": studio.get(c["id"], [])}
        if not c.get("youtube"):
            site.append({**base, "sem_link": True}); continue
        try:
            m = medir(c)
        except Exception as e:
            site.append({**base, "erro": str(e)[:200]}); continue
        if not m:
            site.append({**base, "erro": "não achei o canal por esse link"}); continue
        h = hist.setdefault(c["id"], {"canal": [], "videos": {}})
        h["canal"].append([quando, m["inscritos"], m["views"]])
        del h["canal"][:-500]
        for v in m["videos"]:
            s = h["videos"].setdefault(v["id"], [])
            s.append([quando, v["views"], v["curtidas"], v["comentarios"]])
            del s[:-500]
            v["views_24h"] = delta([[x[0], x[1]] for x in s])
            v["serie"] = [[x[0], x[1]] for x in s][-60:]
        site.append({**base, **{k: m[k] for k in ("youtube_id", "nome_youtube", "foto", "inscritos", "views", "n_videos", "videos")},
                     "inscritos_24h": delta([[x[0], x[1]] for x in h["canal"]]), "views_24h": delta([[x[0], x[2]] for x in h["canal"]]),
                     "atualizado": quando})
        print(f"{c['nome']}: {m['inscritos']} inscritos · {m['views']} views · {len(m['videos'])} vídeos")
    HIST.parent.mkdir(exist_ok=True)
    HIST.write_text(json.dumps(hist, ensure_ascii=False), encoding="utf-8")
    (R / "docs" / "meus-canais.json").write_text(json.dumps({"atualizado": quando, "canais": site}, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
