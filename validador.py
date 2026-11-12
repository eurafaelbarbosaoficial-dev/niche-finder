"""Validador de dobras — pega um título/molde que estourou e faz a pesquisa de mercado dele em vários idiomas
(e em dobras para outros nichos), para dizer onde é OPORTUNIDADE e onde já tem gente fazendo.

Uso:  python -I validador.py validacoes/pedidos/<nome>.json [--n 20] [--conferir 8] [--publicar]

O pedido (escrito pelo Claude quando o dono pede "valide este título") tem:
{
  "slug": "every-money-laundering",
  "origem": {"titulo": "...", "canal": "...", "id": "<id do vídeo>", "views": 1100000, "idioma": "en"},
  "molde": "Every [X] Technique Explained",
  "buscas": {"pt": ["como um nativo buscaria", "..."], "es": [...], "en": [...], "de": [...], "fr": [...]},
  "dobras": [{"nome": "Golpes", "nota": "por que faz sentido", "idioma": "en", "buscas": ["every scam explained"]}]
}
As traduções NÃO são literais: são o que um nativo digitaria. O script só mede; não inventa nada.
Saída: docs/validacoes/<slug>.json e docs/validacoes/index.json (o site lê em docs/validador.html).
"""
import argparse, datetime as dt, json, re, statistics, subprocess, sys, unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I não põe a pasta do script no caminho
from cacador import buscar, idioma_titulo, autocompletar, PARE  # noqa: E402

BASE = Path(__file__).resolve().parent
SAIDA = BASE / "docs" / "validacoes"
NOMES = {"pt": "Português", "es": "Espanhol", "en": "Inglês", "de": "Alemão", "fr": "Francês"}
BOM = 50_000      # um vídeo do formato com isso ou mais = "já validado ali"
FRACO = 10_000    # o melhor do formato abaixo disso = "feito, mas sem sucesso"


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", (s or "").lower()) if unicodedata.category(c) != "Mn")


def chaves(q):
    return [w for w in re.findall(r"\w+", sem_acento(q)) if w not in PARE and len(w) > 2]


def parecido(titulo, q):
    """O título usa a mesma ideia da busca? (≥ 60% das palavras importantes da busca aparecem no título)."""
    k = chaves(q)
    if not k:
        return False
    t = sem_acento(titulo)
    return sum(1 for w in k if w in t) / len(k) >= 0.6


def num(n):
    return f"{n:,}".replace(",", ".")


def lingua(cod):
    return (cod or "").split("-")[0].lower() or None


def resumir(b, idioma, molde, excluir):
    """Recalcula os números de uma busca a partir dos vídeos já conferidos.
    molde=True: é a busca do formato (conta concorrentes). molde=False: é a busca do tema (mede a procura)."""
    itens = [x for x in b["itens"] if x["conferido"] and x["idioma_real"] == idioma
             and x["id"] not in excluir and x.get("canal_id") not in excluir and x.get("canal") not in excluir]
    conc = [x for x in itens if molde and x["mesmo_formato"] and (x["dur"] or 0) >= 240]
    outros = [x for x in itens if x not in conc]
    vc = sorted((x["views"] or 0 for x in conc), reverse=True)
    vo = sorted((x["views"] or 0 for x in outros), reverse=True)
    b.update({"tipo": "molde" if molde else "tema", "concorrentes": len(conc),
              "canais_concorrentes": len({x["canal"] for x in conc}),
              "melhor_concorrente": vc[0] if vc else None,
              "mediana_concorrentes": int(statistics.median(vc)) if vc else None,
              "copias_fracas": sum(1 for v in vc if v < 1000),
              "adjacentes_views": int(statistics.median(vo)) if vo else None,
              "adjacentes_max": vo[0] if vo else None})
    return b


def medir_busca(q, idioma, n, conferir):
    res = buscar(q, n, "qualquer")
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(4) as ex:  # conferir o idioma real é lento (~8 s por vídeo): 4 de cada vez
        reais = list(ex.map(idioma_titulo, [r.get("id") for r in res[:conferir]]))
    print(f"   · {q}: {len(res)} resultados", flush=True)
    itens = []
    for i, r in enumerate(res):
        vid = r.get("id")
        real, titulo = reais[i] if i < conferir else (None, None)
        titulo = titulo or r.get("title") or ""
        d = r.get("duration")
        itens.append({"id": vid, "titulo": titulo, "canal": r.get("channel"), "canal_id": r.get("channel_id"),
                      "views": r.get("view_count"), "dur": int(d) if d else None,
                      "idioma_real": lingua(real), "conferido": i < conferir,
                      "mesmo_formato": parecido(titulo, q)})
    procura = len(autocompletar(" ".join(q.split()[:3]) + " ", idioma))
    return {"busca": q, "procura": procura, "itens": itens}


def avaliar(buscas, idioma, excluir, todas_molde=False):
    """1ª busca = o MOLDE (formato) → conta concorrentes; as outras = o TEMA → medem a procura.
    Nas dobras todas as buscas são o molde no nicho novo (todas_molde=True)."""
    for i, b in enumerate(buscas):
        resumir(b, idioma, todas_molde or i == 0, excluir)
    mol = [b for b in buscas if b["tipo"] == "molde"]
    conc = sum(b["concorrentes"] for b in mol)
    melhor = max([b["melhor_concorrente"] or 0 for b in mol] or [0])
    copias = sum(b["copias_fracas"] for b in mol)
    demanda = max([b["adjacentes_max"] or 0 for b in buscas] or [0])
    procura = max([b["procura"] for b in buscas] or [0])
    sat = (f" Atenção: {copias} cópia(s) com menos de mil views — o formato está ficando cheio de cópias."
           if copias >= 3 else "")
    if conc == 0:
        if demanda >= BOM or procura >= 5:
            return "oportunidade", (f"Ninguém faz esse formato neste idioma, e o tema tem procura (vídeo de outro "
                                    f"formato com {num(demanda)} views; autocompletar {procura}/10).")
        return "oportunidade_fraca", ("Ninguém faz esse formato neste idioma, mas não achei sinal forte de procura. "
                                      "Pode ser tema pequeno aqui.")
    if melhor < FRACO:
        return "feito_sem_sucesso", ("Já fizeram neste idioma e foi mal (alerta, não prova): ver se a execução era "
                                     "fraca." + sat)
    if melhor >= BOM:
        return "validado_concorrencia", (f"Já fazem e funciona ({conc} vídeo(s), o melhor com {num(melhor)} views): o tema "
                                        "está validado. Para entrar: subnichar, micronichar, mudar o público ou o jeito "
                                        "de fazer." + sat)
    return "validado_morno", (f"Já fazem, com resultado médio (melhor: {num(melhor)} views). Espaço para fazer melhor ou "
                              "com outro ângulo." + sat)


def gravar(out):
    slug = out["slug"]
    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / f"{slug}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    idx_p = SAIDA / "index.json"
    idx = json.loads(idx_p.read_text(encoding="utf-8")) if idx_p.exists() else []
    idx = [x for x in idx if x["slug"] != slug]
    idx.insert(0, {"slug": slug, "data": out["data"], "titulo": out["origem"].get("titulo"), "molde": out["molde"],
                   "resumo": {i["idioma"]: i["veredito"] for i in out["idiomas"]},
                   "dobras": [{"nome": d["nome"], "veredito": d["veredito"]} for d in out["dobras"]]})
    idx_p.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Pronto: {SAIDA / (slug + '.json')}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pedido"); ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--conferir", type=int, default=8, help="quantos resultados por busca têm o idioma conferido")
    ap.add_argument("--refazer", action="store_true", help="só recalcula os vereditos com as buscas já gravadas")
    ap.add_argument("--publicar", action="store_true")
    a = ap.parse_args()
    ped = json.loads(Path(a.pedido).read_text(encoding="utf-8"))
    slug, o = ped["slug"], ped.get("origem", {})
    excluir = {x for x in (o.get("id"), o.get("canal_id"), o.get("canal")) if x}
    antigo = json.loads((SAIDA / f"{slug}.json").read_text(encoding="utf-8")) if a.refazer else None
    out = {"slug": slug, "data": antigo["data"] if antigo else dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
           "origem": o, "molde": ped.get("molde"),
           "criterios": {"bom": BOM, "fraco": FRACO, "n": a.n, "conferir": a.conferir}, "idiomas": [], "dobras": []}
    velho = {("i", x["idioma"]): x["buscas"] for x in (antigo or {}).get("idiomas", [])}
    velho.update({("d", x["nome"]): x["buscas"] for x in (antigo or {}).get("dobras", [])})
    for idioma, qs in ped.get("buscas", {}).items():
        print(f"[{idioma}] {len(qs)} busca(s)", flush=True)
        bs = velho.get(("i", idioma)) or [medir_busca(q, idioma, a.n, a.conferir) for q in qs]
        v, txt = avaliar(bs, idioma, excluir)
        out["idiomas"].append({"idioma": idioma, "nome": NOMES.get(idioma, idioma), "veredito": v, "explica": txt,
                               "buscas": bs})
        print(f"   → {v}", flush=True)
    for d in ped.get("dobras", []):
        idioma = d.get("idioma", "en")
        print(f"[dobra] {d['nome']} ({idioma})", flush=True)
        bs = velho.get(("d", d["nome"])) or [medir_busca(q, idioma, a.n, a.conferir) for q in d.get("buscas", [])]
        v, txt = avaliar(bs, idioma, excluir, todas_molde=True)
        out["dobras"].append({**{k: d.get(k) for k in ("nome", "nota", "idioma")}, "veredito": v, "explica": txt,
                              "buscas": bs})
        print(f"   → {v}", flush=True)
    gravar(out)
    if a.publicar:
        subprocess.run(["git", "add", "docs/validacoes", "validacoes"], cwd=BASE)
        subprocess.run(["git", "commit", "-q", "-m", f"Validação: {slug}"], cwd=BASE)
        subprocess.run(["git", "push", "-q"], cwd=BASE)


if __name__ == "__main__":
    main()
