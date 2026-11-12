"""Pautas e dobras com DADOS (nada sai da cabeça de ninguém).

Responde: "fiz o 1º vídeo nesse molde/idioma — quais são os próximos?" e "para que nichos dá para dobrar o molde?".

Passo 1 — coletar (só dados):
  python -I pautas.py coletar validacoes/pedidos/<slug>.json
  Junta temas candidatos de 3 fontes reais e grava validacoes/candidatos/<slug>.json:
    A) o MOLDE pesquisado no YouTube em vários idiomas → assuntos em que o molde JÁ funcionou (com views);
    B) o AUTOCOMPLETAR do YouTube no idioma alvo em volta do tema → o que o povo de lá digita;
    C) os outros vídeos do canal de referência (clusters) → assuntos que o próprio canal já provou.
Passo 2 — o Claude só TRADUZ/normaliza os candidatos para o idioma alvo (não inventa nenhum) e grava em
  pedido["pautas"]["candidatos"] = [{"tema", "busca_tema", "fonte": "A|B|C", "evidencia"}].
Passo 3 — medir:
  python -I pautas.py medir validacoes/pedidos/<slug>.json [--publicar]
  Para cada candidato, no idioma alvo: procura (views dos vídeos sobre o tema + autocompletar) e concorrência no
  molde (alguém já fez "<molde> + tema"?). Ordena e grava docs/pautas/<slug>.json.

Campos do pedido usados aqui:
"pautas": {"idioma": "de", "tema": "geldwäsche",
           "molde_mundo": {"en": "every explained", "es": "todas explicadas", ...},
           "molde_alvo": "alle {X} erklärt", "candidatos": [...]}
"""
import argparse, datetime as dt, json, math, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cacador import buscar, expandir, autocompletar, idioma_titulo  # noqa: E402
from validador import sem_acento, parecido, lingua, num  # noqa: E402
from clusters import ESTRUTURA  # noqa: E402

BASE = Path(__file__).resolve().parent
EXTRA = set("explained explanation explicado explicada explicados explicadas explique expliquees erklart erklaert "
            "minutes minutos minuten heures in en em dans im the la le el der die das los las les".split())


def topico(titulo, molde_q):
    """Tira do título as palavras do molde e de estrutura: o que sobra é o assunto."""
    fora = set(sem_acento(molde_q).split()) | ESTRUTURA | EXTRA
    ws = [w for w in re.findall(r"[a-z0-9]+", sem_acento(titulo)) if w not in fora and not w.isdigit()]
    return " ".join(ws[:6])


def cmd_coletar(a):
    ped = json.loads(Path(a.pedido).read_text(encoding="utf-8"))
    pa, o = ped["pautas"], ped.get("origem", {})
    out = {"slug": ped["slug"], "data": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "idioma": pa["idioma"],
           "A_molde_no_mundo": [], "B_autocompletar": [], "C_canal_referencia": []}
    # A) o molde no mundo
    for lg, q in pa.get("molde_mundo", {}).items():
        res = buscar(q, a.n, "qualquer")
        for r in res:
            t, v = r.get("title") or "", r.get("view_count") or 0
            if parecido(t, q) and v >= a.min_views and (r.get("duration") or 0) >= 240:
                out["A_molde_no_mundo"].append({"idioma_busca": lg, "titulo": t, "views": v, "id": r.get("id"),
                                                "canal": r.get("channel"), "assunto": topico(t, q)})
        print(f"[A] {lg} '{q}': {sum(1 for x in out['A_molde_no_mundo'] if x['idioma_busca'] == lg)} vídeos no molde",
              flush=True)
    out["A_molde_no_mundo"].sort(key=lambda x: -x["views"])
    # B) autocompletar no idioma alvo
    for s, pos in expandir(pa["tema"], pa["idioma"], 40):
        out["B_autocompletar"].append({"sugestao": s, "posicao_top": pos})
    print(f"[B] autocompletar '{pa['tema']}' ({pa['idioma']}): {len(out['B_autocompletar'])} sugestões", flush=True)
    # C) canal de referência
    cl = json.loads((BASE / "docs" / "clusters.json").read_text(encoding="utf-8")) if (BASE / "docs" / "clusters.json").exists() else {}
    c = (cl.get("canais") or {}).get(o.get("canal_id") or "", {})
    for k in c.get("clusters", []):
        for e in k.get("exemplos", []):
            out["C_canal_referencia"].append({"titulo": e["titulo"], "views": e["views"], "molde": k["molde"]})
    out["C_canal_referencia"].sort(key=lambda x: -x["views"])
    print(f"[C] canal de referência: {len(out['C_canal_referencia'])} vídeos", flush=True)
    p = BASE / "validacoes" / "candidatos"; p.mkdir(parents=True, exist_ok=True)
    (p / f"{ped['slug']}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Pronto: {p / (ped['slug'] + '.json')}", flush=True)


def casa(titulo, q):
    """O título fala do tema? Compara pelo radical (6 letras: 'dönerläden' = 'dönerladen').
    Busca de até 2 palavras: precisa de TODAS; 3 ou mais: 60%."""
    ks = [w[:6] for w in re.findall(r"\w+", sem_acento(q)) if len(w) > 2]
    t = sem_acento(titulo)
    if not ks:
        return False
    achou = sum(1 for w in ks if w in t)
    return achou == len(ks) if len(ks) <= 2 else achou / len(ks) >= 0.6


PAL = {"de": "der die das und mit ist ein eine nicht wie warum was so funktioniert für von zu im den dem wird erklärt".split(),
       "en": "the and of to how why what is in a with you your this that explained works".split(),
       "pt": "o a os as e de do da que como por um uma para com não é seu sua explicado".split(),
       "es": "el la los las y de del que como por un una para con no es su explicado".split(),
       "fr": "le la les et de des du que comment pourquoi un une pour avec pas est expliqué".split()}


def idioma_pelo_titulo(t):
    """Plano B quando o YouTube não informa o idioma: conta palavras típicas de cada idioma no título."""
    ws = re.findall(r"\w+", (t or "").lower())
    pts = {k: sum(1 for w in ws if w in v) for k, v in PAL.items()}
    k = max(pts, key=pts.get)
    if pts[k] >= 2 and sorted(pts.values())[-2] < pts[k]:
        return k
    if re.search(r"[äöüß]", (t or "").lower()):  # letras que só o alemão usa
        return "de"
    if re.search(r"[ãõç]", (t or "").lower()):
        return "pt"
    if re.search(r"[ñ¿¡]", (t or "").lower()):
        return "es"
    return None


def idioma_seguro(vid):
    r = idioma_titulo(vid)
    return r if r[0] else idioma_titulo(vid)  # 2ª tentativa quando o YouTube falha


def conferir(res, idioma, k):
    """Idioma real dos k primeiros resultados (os títulos da busca podem vir traduzidos)."""
    with ThreadPoolExecutor(5) as ex:
        reais = list(ex.map(idioma_seguro, [r.get("id") for r in res[:k]]))
    itens = []
    for i, r in enumerate(res[:k]):
        real, tit = reais[i]
        t = tit or r.get("title")
        lg, fonte = lingua(real), "youtube"
        if not lg:
            lg, fonte = idioma_pelo_titulo(t), "titulo"
        itens.append({"id": r.get("id"), "titulo": t, "canal": r.get("channel"), "views": r.get("view_count") or 0,
                      "dur": r.get("duration"), "idioma_real": lg, "idioma_fonte": fonte})
    return [x for x in itens if x["idioma_real"] == idioma]


def medir_um(c, pa, n, k):
    idioma = pa["idioma"]
    q_molde = pa["molde_alvo"].replace("{X}", c["tema"])
    with ThreadPoolExecutor(2) as ex:  # as duas buscas ao mesmo tempo
        r1, r2 = ex.map(lambda q: buscar(q, n, "qualquer"), [c["busca_tema"], q_molde])
    # só conta como demanda do tema o vídeo cujo título tem as palavras da busca (não um vídeo genérico do assunto)
    r1 = [r for r in r1 if casa(r.get("title") or "", c["busca_tema"])]
    tema_res = conferir(r1, idioma, k)
    mol_res = conferir(r2, idioma, k)
    conc = [x for x in mol_res if parecido(x["titulo"], q_molde) and (x["dur"] or 0) >= 240]
    dem = max([x["views"] for x in tema_res] or [0])
    proc = len(autocompletar(c["tema"] + " ", idioma))
    melhor_c = max([x["views"] for x in conc] or [0])
    if conc and melhor_c >= 50_000:
        v, txt = "disputada", f"Já fizeram no molde ({len(conc)} vídeo(s), melhor {num(melhor_c)}). Entrar só com ângulo diferente."
    elif dem >= 50_000 and not conc:
        v, txt = "forte", f"Ninguém fez no molde e o tema tem demanda (vídeo de {num(dem)} views no idioma)."
    elif dem >= 10_000 and not conc:
        v, txt = "boa", f"Ninguém fez no molde; demanda média (melhor vídeo do tema: {num(dem)})."
    elif conc:
        v, txt = "feita_fraca", f"Já fizeram no molde, sem sucesso (melhor {num(melhor_c)}). Alerta."
    else:
        v, txt = "fraca", f"Pouca demanda achada no idioma (melhor vídeo do tema: {num(dem)})."
    pts = (math.log10(dem + 1) * 10 + proc * 2) * (0.3 if v == "disputada" else 1)
    return {**c, "busca_molde": q_molde, "demanda_max": dem, "procura": proc, "concorrentes": len(conc),
            "melhor_concorrente": melhor_c or None, "veredito": v, "explica": txt, "pontos": round(pts, 1),
            "tema_videos": sorted(tema_res, key=lambda x: -x["views"])[:4], "molde_videos": conc[:4]}


def cmd_medir(a):
    ped = json.loads(Path(a.pedido).read_text(encoding="utf-8"))
    pa = ped["pautas"]
    cands = pa.get("candidatos") or []
    print(f"{len(cands)} candidatos em {pa['idioma']}", flush=True)
    res = []
    for i, c in enumerate(cands, 1):
        r = medir_um(c, pa, a.n, a.conferir)
        print(f"  {i:02d}/{len(cands)} [{c.get('fonte')}] {c['tema']}: {r['veredito']} · demanda {num(r['demanda_max'])}",
              flush=True)
        res.append(r)
    ordem = {"forte": 0, "boa": 1, "disputada": 2, "fraca": 3, "feita_fraca": 4}
    res.sort(key=lambda r: (r.get("grupo", "pauta") != "pauta", ordem[r["veredito"]], -r["pontos"]))
    out = {"slug": ped["slug"], "data": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "idioma": pa["idioma"],
           "tema": pa["tema"], "molde_alvo": pa["molde_alvo"], "pautas": res}
    p = BASE / "docs" / "pautas"; p.mkdir(parents=True, exist_ok=True)
    (p / f"{ped['slug']}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Pronto: {p / (ped['slug'] + '.json')}", flush=True)
    if a.publicar:
        subprocess.run(["git", "add", "docs/pautas", "validacoes"], cwd=BASE)
        subprocess.run(["git", "commit", "-q", "-m", f"Pautas: {ped['slug']}"], cwd=BASE)
        subprocess.run(["git", "push", "-q"], cwd=BASE)


def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("coletar"); p.add_argument("pedido"); p.add_argument("--n", type=int, default=40)
    p.add_argument("--min-views", type=int, default=10_000)
    p = sp.add_parser("medir"); p.add_argument("pedido"); p.add_argument("--n", type=int, default=12)
    p.add_argument("--conferir", type=int, default=5); p.add_argument("--publicar", action="store_true")
    a = ap.parse_args()
    {"coletar": cmd_coletar, "medir": cmd_medir}[a.cmd](a)


if __name__ == "__main__":
    main()
