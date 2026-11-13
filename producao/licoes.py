"""Lições do revisor (o "feedback loop" do Raj, vídeo 29, 2:39).

Cada problema que o revisor (de roteiro ou de vídeo) acha vira uma LIÇÃO: o que deu errado, a regra para não
repetir e como conferir. Quem produz lê as lições ANTES de começar; o revisor confere cada uma DEPOIS.
Assim o erro de um vídeo não volta no próximo.

Uso:
  python -I producao/licoes.py listar [--etapa roteiro|voz|montagem|imagem|som|publicar]
  python -I producao/licoes.py adicionar --etapa montagem --problema "..." --regra "..." --conferir "..." \
      [--origem "video X, 17 s"] [--gravidade alto|medio|baixo]
  python -I producao/licoes.py site      (escreve docs/licoes.json para a aba Produção)
"""
import argparse, datetime as dt, json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).resolve().parent
ARQ = AQUI / "licoes.json"
SITE = AQUI.parent / "docs" / "licoes.json"
ETAPAS = ["roteiro", "voz", "montagem", "imagem", "som", "publicar"]


def carregar():
    return json.loads(ARQ.read_text(encoding="utf-8")) if ARQ.exists() else []


def salvar(ls):
    ARQ.write_text(json.dumps(ls, ensure_ascii=False, indent=1), encoding="utf-8")


def listar(etapa=None):
    ls = [l for l in carregar() if not etapa or l["etapa"] == etapa]
    if not ls:
        print("Nenhuma lição" + (f" para '{etapa}'" if etapa else "") + ".")
        return ls
    print(f"LIÇÕES {('— ' + etapa) if etapa else ''} ({len(ls)}): conferir cada uma antes de entregar")
    for l in ls:
        print(f"  [{l['id']}] ({l['gravidade']}) {l['regra']}")
        print(f"       por quê: {l['problema']}  ·  conferir: {l['conferir']}")
    return ls


def adicionar(etapa, problema, regra, conferir, origem="", gravidade="medio"):
    ls = carregar()
    if any(l["regra"].strip().lower() == regra.strip().lower() for l in ls):
        print("Já existe essa lição.")
        return
    n = max([int(l["id"][1:]) for l in ls] or [0]) + 1
    ls.append({"id": f"L{n:03d}", "data": dt.date.today().isoformat(), "etapa": etapa, "gravidade": gravidade,
               "origem": origem, "problema": problema, "regra": regra, "conferir": conferir})
    salvar(ls)
    print(f"Lição L{n:03d} gravada.")


def site():
    SITE.write_text(json.dumps(carregar(), ensure_ascii=False), encoding="utf-8")
    print(f"ok: {SITE}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("listar"); a.add_argument("--etapa", choices=ETAPAS)
    b = sp.add_parser("adicionar")
    b.add_argument("--etapa", choices=ETAPAS, required=True); b.add_argument("--problema", required=True)
    b.add_argument("--regra", required=True); b.add_argument("--conferir", required=True)
    b.add_argument("--origem", default=""); b.add_argument("--gravidade", choices=["alto", "medio", "baixo"], default="medio")
    sp.add_parser("site")
    x = ap.parse_args()
    if x.cmd == "listar": listar(x.etapa)
    elif x.cmd == "adicionar": adicionar(x.etapa, x.problema, x.regra, x.conferir, x.origem, x.gravidade)
    else: site()
