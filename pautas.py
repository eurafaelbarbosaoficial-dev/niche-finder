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
    ks = [w[:max(6, len(w) - 2)] for w in re.findall(r"\w+", sem_acento(q)) if len(w) > 2]
    tws = re.findall(r"\w+", sem_acento(titulo))
    if not ks:
        return False
    # cada palavra da busca precisa ser o COMEÇO de uma palavra do título (radical quase inteiro: 'finanzage' ≠ 'finanzisch')
    achou = sum(1 for w in ks if any(tw.startswith(w) or w in tw for tw in tws if len(tw) >= len(w)))
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
    try:
        mapa_dobras(ped["slug"])
    except Exception as e:
        print(f"mapa de dobras: {e}")
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


if __name__ == "__main__" and not (len(sys.argv) > 1 and sys.argv[1] == "mapa"):
    main()


# ---------- mapa de dobras: os 5 caminhos do Raj, com o que os dados já mostram ----------
FORCA = {"oportunidade": 5, "forte": 5, "boa": 3, "oportunidade_fraca": 2, "validado_morno": 2, "disputada": 1,
         "validado_concorrencia": 1, "fraca": 0, "feito_sem_sucesso": 0, "feita_fraca": 0}


def mapa_dobras(slug):
    val = json.loads((BASE / "docs" / "validacoes" / f"{slug}.json").read_text(encoding="utf-8"))
    pp = BASE / "docs" / "pautas" / f"{slug}.json"
    pau = json.loads(pp.read_text(encoding="utf-8"))
    cand_p = BASE / "validacoes" / "candidatos" / f"{slug}.json"
    cand = json.loads(cand_p.read_text(encoding="utf-8")) if cand_p.exists() else {}
    o, alvo = val.get("origem", {}), pau["idioma"]
    nomes = {"pt": "Português", "es": "Espanhol", "en": "Inglês", "de": "Alemão", "fr": "Francês"}
    caminhos = []
    # 1) mesmo nicho + mesmo formato → outro idioma
    ops = sorted(val["idiomas"], key=lambda l: -FORCA.get(l["veredito"], 0))
    melhor = ops[0] if ops else None
    caminhos.append({"n": 1, "nome": "Outro idioma", "mantem": "nicho + formato", "muda": "idioma",
                     "melhor": f"{nomes.get(melhor['idioma'], melhor['idioma'])}: {melhor['explica']}" if melhor else "—",
                     "veredito": melhor["veredito"] if melhor else None,
                     "opcoes": [{"nome": nomes.get(l["idioma"]), "veredito": l["veredito"]} for l in val["idiomas"]],
                     "fonte": "Validador: o molde pesquisado nos 5 idiomas"})
    # 2) mesmo formato + mesmo idioma de origem → outro nicho
    orig = o.get("idioma", "en")
    ex2 = [x for x in cand.get("A_molde_no_mundo", []) if x["idioma_busca"] == orig][:5]
    caminhos.append({"n": 2, "nome": "Outro nicho, mesmo idioma", "mantem": f"formato + idioma ({nomes.get(orig, orig)})",
                     "muda": "nicho", "veredito": "disputada" if ex2 else None,
                     "melhor": (f"Os assuntos achados já existem em {nomes.get(orig, orig)} (é de lá que eles vêm): "
                                + "; ".join(f"{x['titulo']} ({num(x['views'])})" for x in ex2[:3])) if ex2 else "Sem dado.",
                     "opcoes": [{"nome": x["titulo"], "veredito": "disputada"} for x in ex2],
                     "fonte": "Coleta A: o molde pesquisado no idioma de origem"})
    # 3) mesmo formato → outro nicho + outro idioma
    dob = [x for x in pau["pautas"] if x.get("grupo") == "dobra"]
    dob.sort(key=lambda x: (-FORCA.get(x["veredito"], 0), -x["demanda_max"]))
    caminhos.append({"n": 3, "nome": f"Outro nicho em {nomes.get(alvo, alvo)} (canal novo)", "mantem": "formato",
                     "muda": "nicho + idioma", "veredito": dob[0]["veredito"] if dob else None,
                     "melhor": f"{dob[0]['tema']}: {dob[0]['explica']}" if dob else "Sem dado.",
                     "opcoes": [{"nome": x["tema"], "veredito": x["veredito"]} for x in dob],
                     "fonte": "Pautas: dobras medidas no idioma alvo"})
    # 4) mesmo nicho + idioma alvo → outro formato
    lg = next((l for l in val["idiomas"] if l["idioma"] == alvo), None)
    outros = []
    for b in (lg or {}).get("buscas", []):
        for it in b.get("itens", []):
            if it.get("conferido") and it.get("idioma_real") == alvo and not it.get("mesmo_formato"):
                outros.append(it)
    outros = sorted({x["id"]: x for x in outros}.values(), key=lambda x: -(x["views"] or 0))[:5]
    caminhos.append({"n": 4, "nome": "Outro formato, mesmo nicho", "mantem": f"nicho + idioma ({nomes.get(alvo, alvo)})",
                     "muda": "formato (iceberg, documentário, ascensão e queda, passo a passo)",
                     "veredito": "disputada" if outros and (outros[0]["views"] or 0) >= 50_000 else ("boa" if outros else None),
                     "melhor": ("Já existem vídeos do tema em outros formatos no idioma: " + "; ".join(
                         f"{x['titulo']} ({num(x['views'] or 0)})" for x in outros[:3]) +
                                ". Use as 5 estruturas para variar, não como caminho principal.") if outros else "Sem dado.",
                     "opcoes": [{"nome": x["titulo"], "veredito": "disputada"} for x in outros],
                     "fonte": "Validador: vídeos do tema no idioma alvo que NÃO são do molde"})
    # 5) outro público
    caminhos.append({"n": 5, "nome": "Outro público", "mantem": "nicho + formato", "muda": "público (gênero, idade)",
                     "veredito": None, "melhor": "Ainda sem dado medido para este tema. Para medir: buscar o molde com o "
                     "público no título (ex.: 'para mulheres', 'für Senioren') no idioma alvo.", "opcoes": [],
                     "fonte": "—"})
    onde = {1: "canal novo no idioma (é o 1º canal deste projeto)", 2: "canal novo (outro nicho não entra no mesmo canal)",
            3: "canal novo (outro nicho não entra no mesmo canal)", 4: "mesmo canal (só varia o jeito de contar)",
            5: "mesmo canal ou canal novo, conforme o público"}
    for c in caminhos:
        c["onde"] = onde[c["n"]]
    rec = max([c for c in caminhos if c["veredito"]], key=lambda c: (FORCA.get(c["veredito"], 0), -c["n"]))
    # ficha do projeto: nicho (categoria do finder), subnicho (assunto do vídeo que estourou), micronicho (molde + idioma)
    dados = json.loads((BASE / "docs" / "dados.json").read_text(encoding="utf-8"))
    canal = next((c for c in dados.get("canais", []) if c.get("id") == o.get("canal_id")), {})
    ped = json.loads((BASE / "validacoes" / "pedidos" / f"{slug}.json").read_text(encoding="utf-8"))
    pau["projeto"] = {
        "nicho": canal.get("categoria") or "?", "nicho_fonte": "categoria em que o finder achou o canal de origem",
        "subnicho": ped.get("pautas", {}).get("subnicho") or pau.get("tema"), "subnicho_fonte": "assunto do vídeo que estourou",
        "micronicho": f"{pau.get('molde_alvo')} · {nomes.get(alvo, alvo)}", "micronicho_fonte": "o molde do título no idioma do canal",
        "canal_de_origem": {"nome": o.get("canal"), "temas": [x["termo"] for x in canal.get("palavras", [])[:4]]}}
    rel = {"B": ("mesmo subnicho", "mesmo canal"), "C": ("mesmo nicho, subnicho vizinho", "mesmo canal (novo bloco temático)"),
           "A": ("outro nicho", "canal novo")}
    for x in pau["pautas"]:
        x["relacao"], x["onde"] = rel.get(x.get("fonte"), ("?", "?"))
    pau["mapa_dobras"] = {"recomendado": rec["n"], "caminhos": caminhos,
                          "regra": "Recomendado = o caminho com o veredito mais forte nos dados (oportunidade/forte > boa > "
                                   "disputada). Empate: o mais simples (menor número)."}
    pp.write_text(json.dumps(pau, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Mapa de dobras: recomendado = caminho {rec['n']} ({rec['nome']})")


if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "mapa":
    mapa_dobras(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))["slug"])
