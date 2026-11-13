"""Um comando para produzir um vídeo do roteiro até a pasta publicar/ (sugestão 5 da revisão de 13/11).

  python -I producao/produzir.py novo <slug-do-roteiro> <pasta-do-video> [--ref econ-in-a-nutshell]
      cria videos/<pasta> a partir de producao/modelo-video (motor, efeitos, scripts), um capítulo por bloco do
      roteiro (k1…kN), projeto.json (roteiro, idioma, voz, ritmo alvo da referência) e registra na esteira.
  python -I producao/produzir.py status <pasta>
      mostra em que etapa o vídeo está e o PRÓXIMO comando exato.
  python -I producao/produzir.py rodar <pasta> <etapa>
      roda uma etapa mecânica: palavras | montar | fotos | render | remix | juntar | masterizar | revisar |
      legenda | ritmo | estilo | esteira. ("voz" precisa da chave: ver status; "cenas" é do agente diretor-de-cenas.)

Etapas, na ordem (cada uma confere a anterior):
  1 revisao_roteiro  producao/revisor_roteiro.py + agente revisor-roteiro (antes de gastar voz)
  2 voz              K=<chave> python -I producao/voz.py …   (uma tomada por capítulo)
  3 palavras         tempo de cada palavra (whisper local) + conferência com o roteiro
  4 cenas            agente diretor-de-cenas escreve cenas.py (ritmo da receita, catálogo de modelos)
  5 montar + fotos   index.html de cada capítulo + foto de cada cena (defeito de layout antes do render)
  6 render           todos os capítulos (demora: rodar à noite / em segundo plano)
  7 remix, juntar, masterizar
  8 revisar          revisor.py + agente revisor-video + estilo comparar (ritmo × referência)
  9 legenda, thumbs, descrição → publicar/
"""
import json, shutil, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(__file__).resolve().parents[1]
MODELO = R / "producao" / "modelo-video"
PY = sys.executable


def proj(pasta):
    v = R / "videos" / pasta
    return v, json.loads((v / "projeto.json").read_text(encoding="utf-8"))


def caps(v):
    sys.path.insert(0, str(v))
    import importlib
    import cenas
    importlib.reload(cenas)
    return list(cenas.CAPITULOS)


def novo(slug, pasta, ref=None):
    rot = json.loads((R / "roteiros" / slug / "roteiro.json").read_text(encoding="utf-8"))
    v = R / "videos" / pasta
    if v.exists():
        sys.exit(f"{v} já existe")
    shutil.copytree(MODELO, v, ignore=shutil.ignore_patterns("CATALOGO.md", "__pycache__"))
    alvo = {"cena_media": 4.5, "cena_max": 8.0, "fonte": "padrão (critério nosso)"}
    if ref and (R / "referencias" / ref / "estilo" / "receita.json").exists():
        rr = json.loads((R / "referencias" / ref / "estilo" / "receita.json").read_text(encoding="utf-8"))["ritmo"]["duracao_cena"]
        alvo = {"cena_media": rr["media"], "cena_max": round(max(rr["p90"] * 1.5, rr["media"] * 2), 1), "fonte": f"referencias/{ref} (média e p90 medidos)"}
    pj = {"pasta": pasta, "roteiro": slug, "titulo": rot["titulo"], "idioma": rot.get("idioma", "de"), "referencia": ref,
          "voz": {"provedor": "ai84", "voz_id": "kkJxCnlRCckmfFvzDW5Q"}, "ritmo_alvo": alvo}
    (v / "projeto.json").write_text(json.dumps(pj, ensure_ascii=False, indent=1), encoding="utf-8")
    linhas = ['"""Roteiro visual (escrito pelo agente diretor-de-cenas). Ver producao/modelo-video/CATALOGO.md."""', "", "CAPITULOS = {"]
    for i, b in enumerate(rot["blocos"], 1):
        ab = "" if i == 1 else '"abertura": 2.4, '
        linhas.append(f'    # {b["bloco"]}')
        linhas.append(f'    "k{i}": {{{ab}"voz": "voz/bloco-{i}.mp3", "cenas": []}},')
    linhas.append("}")
    (v / "cenas.py").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    pjs = json.loads((R / "producao" / "projetos.json").read_text(encoding="utf-8"))
    pjs.append({"titulo": rot["titulo"], "tema": (rot.get("pauta") or {}).get("tema"), "projeto": (rot.get("pauta") or {}).get("projeto"),
                "roteiro": slug, "video": pasta, "publicado_em": None, "url": None, "obs": ""})
    (R / "producao" / "projetos.json").write_text(json.dumps(pjs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"criado: {v}  ({len(rot['blocos'])} capítulos; ritmo alvo: cena média {alvo['cena_media']} s)")
    status(pasta)


def status(pasta):
    v, pj = proj(pasta)
    rt = R / "roteiros" / pj["roteiro"]
    ks = caps(v)
    rr = rt / "REVISAO-ROTEIRO.md"
    def tem(*p): return all((v / x).exists() for x in p)
    passos = [
        ("revisão do roteiro", rr.exists() and "Veredito:" in rr.read_text(encoding="utf-8"),
         f"python -I producao/revisor_roteiro.py {pj['roteiro']}   + agente revisor-roteiro (escreve o Veredito)"),
        ("voz", all(tem(f"voz/bloco-{i}.mp3") for i in range(1, len(ks) + 1)),
         f"K=<chave> python -I producao/voz.py roteiros/{pj['roteiro']}/roteiro.json videos/{pasta}/voz"),
        ("palavras", all(tem(f"voz/bloco-{i}.palavras.json") for i in range(1, len(ks) + 1)), f"python -I producao/produzir.py rodar {pasta} palavras"),
        ("cenas", "\"tipo\"" in (v / "cenas.py").read_text(encoding="utf-8"), f"agente diretor-de-cenas para videos/{pasta}"),
        ("montar", all(tem(f"{k}/index.html") for k in ks), f"python -I producao/produzir.py rodar {pasta} montar  (e depois fotos)"),
        ("render", all(tem(f"{k}/renders/{k}.mp4") for k in ks), f"python -I producao/produzir.py rodar {pasta} render   (em segundo plano)"),
        ("juntar e masterizar", tem(f"renders/{pasta}-final.mp4"), f"python -I producao/produzir.py rodar {pasta} remix; … juntar; … masterizar"),
        ("revisão do vídeo", tem("publicar/REVISAO.md"), f"python -I producao/produzir.py rodar {pasta} revisar   + agente revisor-video"),
        ("legenda", tem("publicar/legenda.srt"), f"python -I producao/produzir.py rodar {pasta} legenda"),
        ("thumbs e descrição", tem("publicar/thumbnail.jpg") and tem("publicar/DESCRICAO.txt"), "thumbs (3 versões) + descrição com capítulos e fontes"),
    ]
    print(f"\n{pj['titulo']}  ·  videos/{pasta}")
    prox = None
    for nome, ok, cmd in passos:
        print(f"  {'✔' if ok else '·'} {nome}")
        if not ok and prox is None:
            prox = (nome, cmd)
    print(f"\nPRÓXIMO: {prox[0]}\n  {prox[1]}" if prox else "\nPRONTO PARA POSTAR.")


def rodar(pasta, etapa):
    v, pj = proj(pasta)
    ks = caps(v)
    def run(*a, cwd=v):
        print("→", " ".join(str(x) for x in a), flush=True)
        subprocess.run([str(x) for x in a], cwd=cwd, check=True)
    final = v / "renders" / f"{pasta}-final.mp4"
    if etapa == "palavras":
        run(PY, "-I", "palavras.py", *[f"voz/bloco-{i}.mp3" for i in range(1, len(ks) + 1)])
    elif etapa == "montar":
        for k in ks: run(PY, "-I", "montar.py", k)
    elif etapa == "fotos":
        for k in ks: run(PY, "-I", "fotos.py", k)
    elif etapa == "render":
        run("bash", "renderizar.sh", *ks)
    elif etapa == "remix":
        for k in ks: run(PY, "-I", "remixar.py", k)
    elif etapa == "juntar":
        run(PY, "-I", "juntar.py")
    elif etapa == "masterizar":
        run(PY, "-I", R / "masterizar.py", v / "renders" / f"{pasta}.mp4")
    elif etapa == "revisar":
        run(PY, "-I", R / "revisor.py", "--video", final, "--idioma", pj["idioma"], "--projeto", v)
        if pj.get("referencia"):
            run(PY, "-I", R / "producao" / "estilo.py", "comparar", pj["referencia"], final, cwd=R)
    elif etapa == "legenda":
        run(PY, "-I", R / "producao" / "legenda.py", final, R / "roteiros" / pj["roteiro"] / "roteiro.json", v / "publicar" / "legenda.srt", "--idioma", pj["idioma"])
    elif etapa == "ritmo":
        run(PY, "-I", R / "producao" / "ritmo.py", final, "--saida", v / "renders" / "ritmo")
    elif etapa == "estilo":
        run(PY, "-I", R / "producao" / "estilo.py", "comparar", pj["referencia"], final, cwd=R)
    elif etapa == "esteira":
        run(PY, "-I", R / "producao" / "esteira.py", cwd=R)
    else:
        sys.exit(f"etapa desconhecida: {etapa}")
    status(pasta)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "novo":
        novo(a[1], a[2], a[a.index("--ref") + 1] if "--ref" in a else None)
    elif a[0] == "status":
        status(a[1])
    elif a[0] == "rodar":
        rodar(a[1], a[2])
    else:
        sys.exit(__doc__)
