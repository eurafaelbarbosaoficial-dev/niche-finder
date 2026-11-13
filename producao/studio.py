"""Números do YouTube Studio que o dono manda em PRINT (a API pública não mostra retenção, cliques na thumb etc.).

Os prints ficam numa pasta PRIVADA do notebook (o repositório do site é público):
  Documents/Niche Finder/prints-studio/<id-do-canal>/   (ex.: prints-studio/every-money-laundering/)
O vigia (a cada 10 min) acha prints novos e pede ao Claude para ler cada imagem e gravar os números com:
  python -I producao/studio.py adicionar <id-do-canal> '<json>'
json = {"data": "AAAA-MM-DD", "arquivo": "nome.png", "video": "título ou id (ou 'canal')", "periodo": "48 horas",
        "metricas": {"ctr_pct": 4.8, "impressoes": 12000, "retencao_media_pct": 41, "duracao_media": "4:55",
                     "views": 1500, "horas_assistidas": 120, "inscritos_ganhos": 35,
                     "origens": {"Pesquisa": 30, "Sugeridos": 45}, "quedas": ["0:30 = -25%"]},
        "leitura": "2–3 frases: o que os números mostram (dado) e o que fazer (hipótese, marcada)"}
Só o que aparece no print entra; o que não aparece fica fora (nada estimado).
Uso: python -I producao/studio.py adicionar <canal> '<json>'   |   python -I producao/studio.py pendentes
"""
import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(__file__).resolve().parents[1]
ARQ = R / "producao" / "studio.json"
PASTA = R / "prints-studio"
FEITOS = R / "estado" / "prints-processados.json"
IMG = {".png", ".jpg", ".jpeg", ".webp"}


def pendentes():
    feitos = set(json.loads(FEITOS.read_text(encoding="utf-8"))) if FEITOS.exists() else set()
    out = []
    for f in sorted(PASTA.glob("*/*")):
        if f.suffix.lower() in IMG and str(f.relative_to(PASTA)) not in feitos:
            out.append(f)
    return out


def marcar(arqs):
    feitos = set(json.loads(FEITOS.read_text(encoding="utf-8"))) if FEITOS.exists() else set()
    feitos |= {str(Path(a).resolve().relative_to(PASTA.resolve())) for a in arqs}
    FEITOS.parent.mkdir(exist_ok=True)
    FEITOS.write_text(json.dumps(sorted(feitos), ensure_ascii=False), encoding="utf-8")


def adicionar(canal, dado):
    d = json.loads(ARQ.read_text(encoding="utf-8")) if ARQ.exists() else {}
    d.setdefault(canal, []).append(dado)
    d[canal].sort(key=lambda x: x.get("data", ""))
    ARQ.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print("gravado:", canal, dado.get("data"), dado.get("video"))


if __name__ == "__main__":
    PASTA.mkdir(exist_ok=True)
    if sys.argv[1:2] == ["adicionar"]:
        adicionar(sys.argv[2], json.loads(sys.argv[3]))
    elif sys.argv[1:2] == ["marcar"]:
        marcar(sys.argv[2:])
    else:
        for f in pendentes():
            print(f)
