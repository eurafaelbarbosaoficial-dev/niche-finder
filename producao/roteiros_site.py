"""Publica a aba Roteiro organizada POR CANAL (pedido do dono em 13/11).

Lê producao/canais.json (cada canal: idioma, tema, molde, referência, estruturas e adaptações dele) e escreve:
  docs/canais.json                      os canais (com contagem de roteiros)
  docs/roteiros/index.json              cada item com "tipo" (roteiro | estrutura) e "projeto" (canal)
  docs/roteiros/adaptacoes/<nome>.json  a adaptação cultural de cada canal (para mostrar no site)
Canal novo: acrescente uma entrada em producao/canais.json e rode este script (o roteiro.py publicar também roda).
Uso: python -I producao/roteiros_site.py
"""
import json, shutil, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(__file__).resolve().parents[1]
D = R / "docs" / "roteiros"


def main():
    canais = json.loads((R / "producao" / "canais.json").read_text(encoding="utf-8"))
    idx = json.loads((D / "index.json").read_text(encoding="utf-8")) if (D / "index.json").exists() else []
    novo = []
    for x in idx:
        f = D / f"{x['slug']}.json"
        d = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        rot = d.get("roteiro") or {}
        x["tipo"] = "roteiro" if rot else "estrutura"
        x["projeto"] = (rot.get("pauta") or {}).get("projeto") if rot else None
        x["estrutura"] = rot.get("estrutura")
        x["canais_que_usam"] = [c["id"] for c in canais if x["slug"] in c.get("estruturas", [])]
        novo.append(x)
    (D / "index.json").write_text(json.dumps(novo, ensure_ascii=False, indent=1), encoding="utf-8")
    (D / "adaptacoes").mkdir(exist_ok=True)
    for c in canais:
        for a in c.get("adaptacoes", []):
            src = R / "roteiros" / f"{a}.json"
            if src.exists():
                shutil.copy(src, D / "adaptacoes" / f"{a}.json")
        c["n_roteiros"] = sum(1 for x in novo if x["tipo"] == "roteiro" and x["projeto"] == c["id"])
    (R / "docs" / "canais.json").write_text(json.dumps(canais, ensure_ascii=False, indent=1), encoding="utf-8")
    for c in canais:
        print(f"{c['nome']} ({c['idioma']}): {c['n_roteiros']} roteiro(s), {len(c['estruturas'])} estruturas, {len(c['adaptacoes'])} adaptações")
    print(f"banco: {sum(1 for x in novo if x['tipo'] == 'estrutura')} estruturas")


if __name__ == "__main__":
    main()
