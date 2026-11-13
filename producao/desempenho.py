"""Desempenho dos NOSSOS vídeos depois de postados (sugestão 2 da revisão de 13/11: o sistema aprende com o canal).

Para cada vídeo com "url" em producao/projetos.json, guarda uma foto dos números públicos (views, curtidas,
comentários) a cada execução em estado/desempenho.json e calcula:
  - views com 24 h, 48 h e 7 dias de postado (pela foto mais próxima);
  - comparação com a mediana do canal de referência (referencias/<ref>/medidas.json) — só como régua, não meta.
O que só o YouTube Studio mostra (taxa de clique da thumb, retenção, de onde vem o público) entra à mão:
  python -I producao/desempenho.py studio <pasta> --ctr 5.1 --retencao 38 --duracao-media 4:12 \
      [--queda "0:45=-22%"] [--origem "Pesquisa=40%,Sugeridos=35%"]
Fonte dos números públicos: API do YouTube se houver chave (variável YT_API_KEY ou estado/youtube-api.txt, que NÃO vai
para o git); senão, yt-dlp (mais lento, mesma informação).

Uso: python -I producao/desempenho.py [medir]      → atualiza e escreve docs/desempenho.json (aba Produção)
"""
import argparse, datetime as dt, json, os, re, subprocess, sys, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(__file__).resolve().parents[1]
ARQ = R / "estado" / "desempenho.json"
STUDIO = R / "producao" / "desempenho-studio.json"
YTDLP = Path.home() / ".watch-skill" / "bin" / "yt-dlp.exe"


def chave():
    k = os.environ.get("YT_API_KEY")
    f = R / "estado" / "youtube-api.txt"
    return k or (f.read_text(encoding="utf-8").strip() if f.exists() else None)


def vid_id(url):
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", url or "")
    return m.group(1) if m else None


def numeros(ids):
    k = chave()
    out = {}
    if k:
        for i in range(0, len(ids), 50):
            u = f"https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet&id={','.join(ids[i:i+50])}&key={k}"
            for it in json.loads(urllib.request.urlopen(u, timeout=30).read()).get("items", []):
                s = it["statistics"]
                out[it["id"]] = {"views": int(s.get("viewCount", 0)), "curtidas": int(s.get("likeCount", 0)), "comentarios": int(s.get("commentCount", 0)),
                                 "postado": it["snippet"]["publishedAt"], "fonte": "api"}
        return out
    for v in ids:
        r = subprocess.run([str(YTDLP) if YTDLP.exists() else "yt-dlp", "--no-warnings", "--skip-download", "--print",
                            "%(view_count)s|%(like_count)s|%(comment_count)s|%(timestamp)s", f"https://www.youtube.com/watch?v={v}"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        p = (r.stdout.strip().splitlines() or [""])[-1].split("|")
        if len(p) == 4 and p[0].isdigit():
            n = lambda x: int(x) if x.isdigit() else None
            out[v] = {"views": n(p[0]), "curtidas": n(p[1]), "comentarios": n(p[2]),
                      "postado": dt.datetime.fromtimestamp(int(p[3]), dt.timezone.utc).isoformat() if p[3].isdigit() else None, "fonte": "yt-dlp"}
    return out


def medir():
    pjs = json.loads((R / "producao" / "projetos.json").read_text(encoding="utf-8"))
    hist = json.loads(ARQ.read_text(encoding="utf-8")) if ARQ.exists() else {}
    ids = {vid_id(p.get("url")): p for p in pjs if vid_id(p.get("url"))}
    agora = dt.datetime.now(dt.timezone.utc)
    if ids:
        for v, n in numeros(list(ids)).items():
            hist.setdefault(v, []).append({"quando": agora.isoformat(timespec="minutes"), **n})
        ARQ.parent.mkdir(exist_ok=True)
        ARQ.write_text(json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8")
    studio = json.loads(STUDIO.read_text(encoding="utf-8")) if STUDIO.exists() else {}
    site = []
    for v, p in ids.items():
        fs = hist.get(v, [])
        if not fs:
            continue
        post = dt.datetime.fromisoformat((fs[-1].get("postado") or fs[0]["quando"]).replace("Z", "+00:00"))
        def em(h):
            alvo = post + dt.timedelta(hours=h)
            cands = [f for f in fs if abs(dt.datetime.fromisoformat(f["quando"]) - alvo) <= dt.timedelta(hours=max(6, h * 0.25))]
            return min(cands, key=lambda f: abs(dt.datetime.fromisoformat(f["quando"]) - alvo))["views"] if cands else None
        ref_med = None
        if p.get("referencia") or True:
            for m in (R / "referencias").glob("*/medidas.json"):
                lst = [x["views"] for x in json.loads(m.read_text(encoding="utf-8")).get("lista", []) if x.get("views")]
                if lst:
                    ref_med = sorted(lst)[len(lst) // 2]
                break
        site.append({"titulo": p["titulo"], "url": p["url"], "postado": post.isoformat(timespec="minutes"),
                     "agora": fs[-1], "views_24h": em(24), "views_48h": em(48), "views_7d": em(24 * 7),
                     "horas_no_ar": round((agora - post).total_seconds() / 3600, 1), "mediana_referencia": ref_med,
                     "studio": studio.get(p["video"]), "serie": [[f["quando"], f["views"]] for f in fs]})
    (R / "docs" / "desempenho.json").write_text(json.dumps(site, ensure_ascii=False), encoding="utf-8")
    for s in site:
        print(f"{s['titulo'][:60]}: {s['agora']['views']} views em {s['horas_no_ar']} h · 24h={s['views_24h']} 48h={s['views_48h']} 7d={s['views_7d']}")
    if not site:
        print("Nenhum vídeo com url em producao/projetos.json ainda.")


def studio(a):
    d = json.loads(STUDIO.read_text(encoding="utf-8")) if STUDIO.exists() else {}
    d[a.pasta] = {"data": dt.date.today().isoformat(), "ctr_pct": a.ctr, "retencao_pct": a.retencao, "duracao_media": a.duracao_media,
                  "quedas": a.queda or [], "origem": a.origem}
    STUDIO.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print("gravado:", d[a.pasta])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd")
    sp.add_parser("medir")
    s = sp.add_parser("studio"); s.add_argument("pasta"); s.add_argument("--ctr", type=float); s.add_argument("--retencao", type=float)
    s.add_argument("--duracao-media"); s.add_argument("--queda", action="append"); s.add_argument("--origem")
    a = ap.parse_args()
    studio(a) if a.cmd == "studio" else medir()
