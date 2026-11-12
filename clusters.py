"""Clusters de título (método do Raj: quebrar os títulos em estruturas e ver quais performam).

Para cada outlier de docs/dados.json: baixa TODOS os títulos de vídeos longos do canal, troca as palavras de
assunto por [X] e os números por [N] (sobra o "esqueleto": every/how/why/explicado/em N minutos…), junta os títulos
de mesmo esqueleto num cluster e mede views médias e máximas de cada um.
Também junta canais DIFERENTES que usam o mesmo esqueleto = "moldes em alta" no mercado.

Uso: python -I clusters.py  → grava docs/clusters.json (o site lê).
É uma aproximação automática (por palavras); a ficha DNA com o Claude refina.
"""
import json, re, statistics, sys, unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cacador import yt  # noqa: E402

BASE = Path(__file__).resolve().parent
MIN_DUR = 240

# palavras que formam a ESTRUTURA do título (o resto é assunto → [X])
ESTRUTURA = set("""
every all each how why what when who if vs versus explained explaining minutes minute hours hour seconds ranked
tier top best worst secrets secret truth you your i my history story level levels types
todo todos toda todas cada como porque quando quem se explicado explicada explicados explicadas minutos horas
historia segredos segredo verdade voce seu sua niveis nivel tipos
cuando quien si explicadas segundos secretos verdad tu tus historia niveles
tout tous toute toutes chaque comment pourquoi quand qui si explique expliquee expliques expliquees heures
secrets verite vous votre tu histoire niveaux
alle jede jeder jedes wie warum was wann wer wenn erklart erklaert minuten stunden geheimnisse wahrheit du dein
ich geschichte stufen
""".split())
LIGA = {"in": "in", "em": "em", "en": "en", "dans": "en", "im": "in"}  # "em N minutos": só conta antes de [N]


def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", (s or "").lower()) if unicodedata.category(c) != "Mn")
    return s


def esqueleto(titulo):
    """'Every Money Laundering Technique Explained in 12 Minutes' → 'every [X] explained in [N] minutes'"""
    toks = re.findall(r"[a-z0-9']+|[?!:|]", norm(titulo).replace("’", "'"))
    out = []
    for t in toks:
        t2 = t.replace("'", "")
        if not t2 and t not in "?!:|":
            continue
        if t2.isdigit():
            w = "[N]"
            if out and out[-1] in ("[X]",) and len(out) >= 2 and out[-2] in LIGA:
                pass
        elif t2 in ESTRUTURA or t in "?!:":
            w = t2 if t2 else t
        else:
            w = "[X]"
        if w in ("[X]", "[N]") and out and out[-1] == w:
            continue
        if t == "|":
            break  # o que vem depois do | costuma ser o nome do canal
        out.append(w)
    # tira artigos/ligações sobrando nas pontas e colapsa "[X] de [X]" → "[X]"
    s = " ".join(out)
    for _ in range(3):
        s = re.sub(r"\[X\] (?:of|de|do|da|dos|das|del|du|des|the|la|le|el|der|die|das|and|e|y|et|und) \[X\]", "[X]", s)
    s = re.sub(r"^(?:the|a|an|o|a|el|la|le|der|die|das) ", "", s).strip()
    s = re.sub(r"(?:\[X\] )?\[N\] (?:minutes|minute|minutos|minuten|heures|hours|hour|horas|stunden)", "em [N] min", s)
    s = re.sub(r" ?[!?:]", "", s).strip()
    s = re.sub(r"(?:\[X\] )+\[X\]", "[X]", s)
    return s if "[X]" in s else s + " [X]"


def titulos_do_canal(cid):
    out = yt(["-J", "--flat-playlist", "--playlist-end", "61", f"https://www.youtube.com/channel/{cid}/videos"])
    try:
        d = json.loads(out)
    except Exception:
        return []
    return [{"id": e["id"], "titulo": e.get("title"), "views": e.get("view_count") or 0}
            for e in d.get("entries") or [] if e.get("id") and (e.get("duration") or 0) >= MIN_DUR]


def agrupar(videos):
    g = {}
    for v in videos:
        g.setdefault(esqueleto(v["titulo"]), []).append(v)
    cl = []
    for k, vs in g.items():
        vv = [v["views"] for v in vs]
        cl.append({"molde": k, "n": len(vs), "media": int(statistics.mean(vv)), "max": max(vv),
                   "exemplos": sorted(vs, key=lambda v: -v["views"])[:3]})
    media_canal = statistics.mean([v["views"] for v in videos]) if videos else 0
    for c in cl:  # quanto o cluster rende comparado à média do canal
        c["indice"] = round(c["media"] / media_canal, 2) if media_canal else None
    return sorted(cl, key=lambda c: (-c["media"]))


def main():
    dados = json.loads((BASE / "docs" / "dados.json").read_text(encoding="utf-8"))
    bom = (dados.get("criterios") or {}).get("bom_video", 50000)
    outs = [c for c in dados.get("canais", []) if ((c.get("melhor") or {}).get("views") or 0) >= bom]
    print(f"{len(outs)} outliers", flush=True)
    with ThreadPoolExecutor(4) as ex:
        listas = list(ex.map(lambda c: titulos_do_canal(c["id"]), outs))
    canais, mercado = {}, {}
    for c, vids in zip(outs, listas):
        vids = vids or [{"id": v["id"], "titulo": v["titulo"], "views": v.get("views") or 0} for v in c.get("videos", [])]
        cl = agrupar(vids)
        canais[c["id"]] = {"nome": c["nome"], "n_videos": len(vids), "clusters": cl}
        for k in cl:
            fam = k["molde"].replace(" em [N] min", "")  # mesma família com ou sem "em N minutos"
            m = mercado.setdefault(fam, {"molde": fam, "canais": [], "videos": 0, "max": 0})
            m["canais"].append({"id": c["id"], "nome": c["nome"], "idioma": c.get("idioma"), "max": k["max"]})
            m["videos"] += k["n"]
            m["max"] = max(m["max"], k["max"])
        print(f"  {c['nome']}: {len(vids)} vídeos, {len(cl)} clusters · top: {cl[0]['molde'] if cl else '-'}", flush=True)
    def tem_estrutura(m):  # pelo menos uma palavra de formato (não só [X], [N], "em N min")
        return any(w not in ("[X]", "[N]", "em", "min") for w in m.split())
    em_alta = sorted([m for m in mercado.values() if len({x["id"] for x in m["canais"]}) >= 2 and tem_estrutura(m["molde"])],
                     key=lambda m: (-len(m["canais"]), -m["max"]))
    out = {"atualizado": dados.get("atualizado"), "canais": canais, "em_alta": em_alta[:30]}
    (BASE / "docs" / "clusters.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Pronto: {len(canais)} canais, {len(em_alta)} moldes usados por 2+ canais", flush=True)


if __name__ == "__main__":
    main()
