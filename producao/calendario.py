"""Calendário programático do canal (Raj, vídeo 29, 6:20; vídeo 25, 7:09 "árvore editorial").

Junta, para UM canal, as pautas já medidas (docs/pautas/<projeto>.json) e os vídeos do canal de referência
(referencias/<ref>/medidas.json), ordena pelos dados e distribui nas datas de postagem.
Só entra o que tem dado. A ordem é: medidas fortes/boas (pela pontuação) → vídeos do canal de referência que
renderam acima da mediana dele (ainda a MEDIR no nosso idioma). Pautas fracas ou "feitas sem sucesso" ficam fora.

Uso:
  python -I producao/calendario.py <projeto> [--ref econ-in-a-nutshell] [--inicio 2026-11-14] \
      [--dias sab,qua] [--hora 17:00] [--feitos "Geldwäsche-Skandale der Banken"]
Gera producao/calendario-<projeto>.json e docs/calendario.json (aba Produção do site).
"""
import argparse, datetime as dt, json, statistics, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[1]
DIAS = {"seg": 0, "ter": 1, "qua": 2, "qui": 3, "sex": 4, "sab": 5, "dom": 6}


def datas(inicio, dias, n):
    d, out = inicio, []
    while len(out) < n:
        if d.weekday() in dias:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("projeto"); ap.add_argument("--ref", default="")
    ap.add_argument("--inicio", default=dt.date.today().isoformat())
    ap.add_argument("--dias", default="sab,qua"); ap.add_argument("--hora", default="17:00")
    ap.add_argument("--feitos", default="", help="temas com vídeo pronto (ainda não postado), separados por ';'")
    a = ap.parse_args()
    p = json.loads((RAIZ / "docs" / "pautas" / f"{a.projeto}.json").read_text(encoding="utf-8"))
    feitos = {x.strip().lower() for x in a.feitos.split(";") if x.strip()}
    itens = []
    for x in sorted([x for x in p["pautas"] if x.get("grupo") == "pauta"], key=lambda x: -x.get("pontos", 0)):
        if x.get("veredito") not in ("forte", "boa"):
            continue
        itens.append({"tema": x["tema"], "tema_pt": x.get("tema_pt"), "titulo": x.get("busca_molde"),
                      "status": "pronto" if x["tema"].lower() in feitos else "validado",
                      "dado": f"{x['veredito']} · {x.get('pontos')} pts · melhor vídeo do tema {x.get('demanda_max'):,} views · {x.get('concorrentes', 0)} concorrentes no molde".replace(",", "."),
                      "evidencia": x.get("evidencia"), "onde": x.get("onde")})
    if a.ref:
        m = RAIZ / "referencias" / a.ref / "medidas.json"
        if m.exists():
            ref = json.loads(m.read_text(encoding="utf-8"))
            lst = [v for v in ref.get("lista", []) if v.get("views")]
            med = statistics.median([v["views"] for v in lst]) if lst else 0
            for v in sorted(lst, key=lambda v: -v["views"]):
                if v["views"] > med:
                    itens.append({"tema": v["titulo"], "tema_pt": None, "titulo": None, "status": "a medir",
                                  "dado": f"canal de referência: {v['views']:,} views (mediana do canal {int(med):,})".replace(",", "."),
                                  "evidencia": f"https://youtu.be/{v['id']}", "onde": "adaptar ao idioma e medir com pautas.py"})
    pend = [i for i in itens if i["status"] != "publicado"]
    for i, d in zip(pend, datas(dt.date.fromisoformat(a.inicio), {DIAS[x] for x in a.dias.split(",")}, len(pend))):
        i["data"] = d.isoformat(); i["hora_de"] = a.hora
    out = {"projeto": a.projeto, "idioma": p.get("idioma"), "molde": p.get("molde_alvo"), "gerado": dt.date.today().isoformat(),
           "regra": f"Postar {a.dias.replace(',', ' e ')} às {a.hora} (Alemanha). Ordem pelos dados; 'a medir' só vira vídeo depois de medido.",
           "itens": itens}
    (RAIZ / "producao" / f"calendario-{a.projeto}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (RAIZ / "docs" / "calendario.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    for i in itens:
        print(f"{i.get('data', '—'):>10}  {i['status']:<9} {i['tema'][:60]:<60} {i['dado']}")


if __name__ == "__main__":
    main()
