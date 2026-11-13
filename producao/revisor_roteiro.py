"""Revisor de roteiro: medições automáticas ANTES de gastar crédito de voz (Raj, vídeo 29, 14:43: revisor em cada etapa).

Uso:  python -I producao/revisor_roteiro.py <slug>        (lê roteiros/<slug>/roteiro.json)

Mede:
- palavras e duração estimada (palavras/min MEDIDAS na nossa voz, por idioma);
- frases longas demais para a voz e para a retenção;
- gancho: quantas palavras até o 1º dado concreto (número, data);
- cada bloco tem fonte? cada link abre?
- cada NÚMERO do texto aparece em alguma fonte do bloco? (se não aparece, é "conferir": pode estar escrito de outro
  jeito na fonte, ex. "1,3 Billionen" × "1.3 trillion");
- palavra repetida demais no mesmo bloco;
- lições de roteiro já aprendidas (producao/licoes.json).
Gera roteiros/<slug>/revisao-roteiro.json e REVISAO-ROTEIRO.md. O agente revisor-roteiro completa a parte de juízo.
"""
import concurrent.futures as cf, json, re, subprocess, sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[1]
# palavras/min medidas na voz que usamos (critério nosso; atualizar quando medir outra voz)
PPM = {"de": 126, "pt": 150, "en": 150, "es": 155, "fr": 150}
FRASE_LONGA = 28   # palavras (critério nosso)
GANCHO_MAX = 20    # palavras até o 1º dado concreto (critério nosso)
NUM = re.compile(r"\d[\d.,]*")
VAZIAS = set("der die das und ist ein eine einer eines den dem des zu von mit auf für im in an es sie er wir ihr du ich nicht sich als auch noch nur so wie was wenn dann aber oder bei aus um hat haben wird werden war waren sind sein dass the a an and of to in is it that for on with as was are be this o a os as de do da e que um uma em no na para com por se não".split())


def baixar(url):
    try:
        r = subprocess.run(["curl", "-s", "-L", "--max-time", "25", "-A", "Mozilla/5.0", "-w", "\n%{http_code}", url],
                           capture_output=True, timeout=40)
        corpo, _, cod = r.stdout.rpartition(b"\n")
        return int(cod or 0), corpo.decode("utf-8", errors="replace")
    except Exception:
        return 0, ""


def so_digitos(s):
    return re.sub(r"\D", "", s)


def main(slug):
    pasta = RAIZ / "roteiros" / slug
    r = json.loads((pasta / "roteiro.json").read_text(encoding="utf-8"))
    idioma = r.get("idioma", "pt")
    achados = []
    def achado(g, bloco, msg): achados.append({"gravidade": g, "bloco": bloco, "msg": msg})

    blocos = r["blocos"]
    texto = " ".join(b["texto"] for b in blocos)
    palavras = len(texto.split())
    ppm = PPM.get(idioma, 140)
    # gancho
    g = blocos[0]["texto"].split()
    ate = next((i for i, w in enumerate(g) if NUM.search(w)), None)
    if ate is None or ate > GANCHO_MAX:
        achado("medio", blocos[0]["bloco"], f"Gancho: {ate if ate is not None else 'nenhum'} palavras até o 1º dado concreto (máx. {GANCHO_MAX}).")
    # fontes (todas de uma vez)
    urls = sorted({u for b in blocos for u in b.get("fontes", [])})
    print(f"abrindo {len(urls)} fontes…", flush=True)
    with cf.ThreadPoolExecutor(8) as ex:
        pags = dict(zip(urls, ex.map(baixar, urls)))
    quebradas = [u for u, (c, _) in pags.items() if not (200 <= c < 400)]
    for u in quebradas:
        c = pags[u][0]
        if c in (403, 429, 503):
            achado("baixo", "fontes", f"O site bloqueia acesso automático (código {c}); abrir no navegador para conferir: {u}")
        else:
            achado("medio", "fontes", f"Link não abriu (código {c}): {u}")
    por_bloco = []
    for b in blocos:
        nome, t = b["bloco"], b["texto"]
        fs = b.get("fontes", [])
        if not fs:
            achado("alto", nome, "Bloco sem nenhuma fonte.")
        # frases longas
        for fr in re.split(r"(?<=[.!?])\s+", t):
            n = len(fr.split())
            if n > FRASE_LONGA:
                achado("baixo", nome, f"Frase de {n} palavras (máx. {FRASE_LONGA}): \"{fr[:90]}…\"")
        # números × fontes
        corpo = " ".join(pags.get(u, (0, ""))[1] for u in fs)
        nums_corpo = {so_digitos(x) for x in NUM.findall(corpo)}
        bloqueadas = [u for u in fs if u in quebradas]
        nao = []
        for m in NUM.finditer(t):
            num = m.group().strip(".,")
            d = so_digitos(num)
            if len(d) < 2 or (len(d) == 4 and 1900 <= int(d) <= 2100):
                continue  # anos e números de 1 dígito: ruído demais para checar automático
            if d not in nums_corpo and d.rstrip("0") not in {x.rstrip("0") for x in nums_corpo}:
                nao.append(num)
        if nao and bloqueadas:
            nao = [n + "*" for n in nao]  # * = alguma fonte do bloco não abriu: pode estar nela
        if nao:
            achado("conferir", nome, f"Números que não achei nas fontes do bloco (podem estar escritos de outro jeito): {', '.join(sorted(set(nao)))}")
        # repetição
        ws = [w.lower().strip(".,:;!?\"'()–-") for w in t.split()]
        rep = [(w, c) for w, c in Counter(w for w in ws if len(w) > 3 and w not in VAZIAS).items() if c >= 5]
        if rep:
            achado("baixo", nome, "Palavras repetidas no bloco: " + ", ".join(f"{w} ×{c}" for w, c in rep))
        por_bloco.append({"bloco": nome, "palavras": len(t.split()), "seg_estimado": round(len(t.split()) / ppm * 60), "fontes": len(fs), "numeros_nao_achados": sorted(set(nao))})

    licoes = []
    arq = RAIZ / "producao" / "licoes.json"
    if arq.exists():
        licoes = [l for l in json.loads(arq.read_text(encoding="utf-8")) if l["etapa"] == "roteiro"]
    R = {"slug": slug, "titulo": r.get("titulo"), "idioma": idioma, "palavras": palavras, "ppm_usado": ppm,
         "duracao_estimada_min": round(palavras / ppm, 1), "fontes": len(urls), "fontes_quebradas": len(quebradas),
         "blocos": por_bloco, "achados": achados, "licoes": licoes}
    (pasta / "revisao-roteiro.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
    L = [f"# Revisão do roteiro: {r.get('titulo')}", "",
         f"- {palavras} palavras ≈ **{R['duracao_estimada_min']} min** a {ppm} palavras/min (voz medida, critério nosso)",
         f"- {len(urls)} fontes, {len(quebradas)} não abriram", "", "## Por bloco", "",
         "| bloco | palavras | ~seg | fontes | números a conferir |", "|---|---|---|---|---|"]
    L += [f"| {b['bloco']} | {b['palavras']} | {b['seg_estimado']} | {b['fontes']} | {', '.join(b['numeros_nao_achados']) or '—'} |" for b in por_bloco]
    L += ["", "## Achados automáticos", ""] + [f"- **{a['gravidade']}** · {a['bloco']}: {a['msg']}" for a in achados] or ["Nenhum."]
    L += ["", "## Lições de roteiro (conferir uma por uma)", ""] + [f"- [ ] **{l['id']}** {l['regra']} — {l['conferir']}" for l in licoes]
    (pasta / "REVISAO-ROTEIRO.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    alto = sum(a["gravidade"] == "alto" for a in achados)
    print(f"pronto: {pasta / 'REVISAO-ROTEIRO.md'}  ·  {palavras} palavras ≈ {R['duracao_estimada_min']} min · {alto} altos · {len(achados)} achados")


if __name__ == "__main__":
    main(sys.argv[1])
