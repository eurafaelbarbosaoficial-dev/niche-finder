"""Esteira de produção (Raj, vídeo 29, 14:20): ideia → roteiro → revisão do roteiro → voz → montagem →
revisão do vídeo → pronto → publicado.

Lê o que EXISTE nas pastas (não depende de ninguém marcar à mão) e escreve docs/esteira.json para a aba Produção.
Fontes:
- ideias: issues abertas no GitHub com o rótulo "ideia" (botão "Nova ideia" do site) + itens do calendário;
- cada vídeo: producao/projetos.json liga o roteiro (roteiros/<slug>) à pasta do vídeo (videos/<pasta>).
  O status sai dos arquivos: roteiro.json, REVISAO-ROTEIRO.md com veredito, voz/*.mp3, renders/*.mp4,
  publicar/REVISAO.md, thumbnail + DESCRICAO, e "publicado_em" no projetos.json (o dono avisa quando postou).

Uso: python -I producao/esteira.py
"""
import json, re, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[1]
REPO = "eurafaelbarbosaoficial-dev/niche-finder"
ETAPAS = ["ideia", "roteiro", "revisao_roteiro", "voz", "montagem", "revisao_video", "pronto", "publicado"]


def estagio(pj):
    rt = RAIZ / "roteiros" / pj["roteiro"] if pj.get("roteiro") else None
    vd = RAIZ / "videos" / pj["video"] if pj.get("video") else None
    passos = {e: False for e in ETAPAS}
    passos["ideia"] = True
    if rt and (rt / "roteiro.json").exists():
        passos["roteiro"] = True
        rr = rt / "REVISAO-ROTEIRO.md"
        passos["revisao_roteiro"] = rr.exists() and "Veredito:" in rr.read_text(encoding="utf-8")
    if vd and vd.exists():
        passos["voz"] = any(vd.glob("voz/*.mp3"))
        passos["montagem"] = any(vd.glob("renders/*.mp4"))
        pub = vd / "publicar"
        passos["revisao_video"] = (pub / "REVISAO.md").exists()
        passos["pronto"] = (pub / "thumbnail.jpg").exists() and (pub / "DESCRICAO.txt").exists() and passos["revisao_video"]
    passos["publicado"] = bool(pj.get("publicado_em"))
    atual = max((i for i, e in enumerate(ETAPAS) if passos[e]), default=0)
    return ETAPAS[atual], passos


def ideias_github():
    try:
        out = subprocess.run(["gh", "issue", "list", "--repo", REPO, "--label", "ideia", "--state", "open", "--json", "number,title,body,createdAt,url"],
                             capture_output=True, text=True, encoding="utf-8", timeout=60).stdout
        return json.loads(out or "[]")
    except Exception:
        return []


def main():
    pjs = json.loads((RAIZ / "producao" / "projetos.json").read_text(encoding="utf-8"))
    cal = {}
    cf = RAIZ / "docs" / "calendario.json"
    if cf.exists():
        c = json.loads(cf.read_text(encoding="utf-8"))
        cal = {i["tema"].lower(): i for i in c.get("itens", [])}
    cards = []
    temas = set()
    for pj in pjs:
        e, passos = estagio(pj)
        ci = cal.get((pj.get("tema") or "").lower(), {})
        temas.add((pj.get("tema") or "").lower())
        cards.append({"titulo": pj["titulo"], "tema": pj.get("tema"), "etapa": e, "passos": passos,
                      "data": pj.get("publicado_em") or ci.get("data"), "hora": ci.get("hora_de"),
                      "roteiro": pj.get("roteiro"), "url": pj.get("url"), "obs": pj.get("obs")})
    for t, i in cal.items():
        if t not in temas:
            cards.append({"titulo": i.get("titulo") or i["tema"], "tema": i["tema"], "tema_pt": i.get("tema_pt"), "etapa": "ideia",
                          "origem": "calendário", "status": i["status"], "dado": i.get("dado"), "data": i.get("data"), "hora": i.get("hora_de")})
    for g in ideias_github():
        cards.append({"titulo": g["title"].removeprefix("Ideia: "), "etapa": "ideia", "origem": "ideia do dono",
                      "issue": g["url"], "obs": (g.get("body") or "")[:300], "data": None})
    out = {"etapas": ETAPAS, "cards": cards}
    (RAIZ / "docs" / "esteira.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    for c in cards:
        print(f"{c['etapa']:<16} {c['titulo'][:70]}")


if __name__ == "__main__":
    main()
