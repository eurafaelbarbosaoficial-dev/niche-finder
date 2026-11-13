"""Dados para escrever o título de um vídeo (sugestão 4 da revisão de 13/11). Não escreve o título: junta os DADOS
para o Claude escrever 5–10 opções, cada uma apoiada num deles.

Junta:
  1. o que o público digita sobre o tema, no idioma (autocompletar do YouTube, em ordem de popularidade);
  2. os títulos dos vídeos mais vistos sobre o tema no idioma (busca), com views e tamanho;
  3. os moldes de título que rendem acima da média nos canais em alta do mesmo idioma (docs/clusters.json);
  4. o molde do nosso canal (docs/pautas/<projeto>.json → molde_alvo).
Uso: python -I producao/titulos.py <projeto> "<tema no idioma>" [--idioma de]
Saída: producao/titulos/<projeto>-<tema>.md (e .json)
"""
import argparse, json, re, statistics, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R))
from cacador import autocompletar, buscar  # noqa: E402


def mil(n):
    return f"{n:,}".replace(",", ".")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("projeto"); ap.add_argument("tema"); ap.add_argument("--idioma")
    a = ap.parse_args()
    pa = json.loads((R / "docs" / "pautas" / f"{a.projeto}.json").read_text(encoding="utf-8"))
    idioma = a.idioma or pa.get("idioma", "de")
    sug = autocompletar(a.tema + " ", idioma)
    sug2 = autocompletar(a.tema.split()[0] + " ", idioma) if len(a.tema.split()) > 1 else []
    res = [r for r in buscar(a.tema, 25, "ano", "views") if (r.get("duration") or 0) >= 240]
    tops = [{"titulo": r.get("title"), "views": r.get("view_count"), "canal": r.get("channel"), "letras": len(r.get("title") or "")} for r in res[:15]]
    cl = json.loads((R / "docs" / "clusters.json").read_text(encoding="utf-8"))
    cache = json.loads((R / "estado" / "canais.json").read_text(encoding="utf-8"))
    moldes = []
    for cid, c in cl.get("canais", {}).items():
        if (cache.get(cid) or {}).get("idioma") != idioma:
            continue
        for k in c.get("clusters", []):
            if k.get("n", 0) >= 2 and (k.get("indice") or 0) >= 1.0 and k["molde"] != "[X]":
                moldes.append({"molde": k["molde"], "canal": c["nome"], "n": k["n"], "media": k["media"], "indice": k["indice"],
                               "exemplo": (k.get("exemplos") or [{}])[0].get("titulo")})
    moldes.sort(key=lambda m: -m["media"])
    letras = [t["letras"] for t in tops if t["views"]]
    out = {"projeto": a.projeto, "idioma": idioma, "tema": a.tema, "molde_do_canal": pa.get("molde_alvo"),
           "autocompletar": sug, "autocompletar_amplo": sug2, "mais_vistos": tops, "moldes_em_alta_no_idioma": moldes[:15],
           "tamanho_tipico": int(statistics.median(letras)) if letras else None}
    pasta = R / "producao" / "titulos"; pasta.mkdir(exist_ok=True)
    nome = re.sub(r"[^\w]+", "-", a.tema.lower()).strip("-")
    (pasta / f"{a.projeto}-{nome}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    L = [f"# Dados para o título: {a.tema} ({idioma})", "", f"Molde do canal: **{out['molde_do_canal']}** · tamanho típico dos mais vistos: {out['tamanho_tipico']} letras", "",
         "## O que o público digita (autocompletar, do mais buscado ao menos)", ""] + [f"{i+1}. {s}" for i, s in enumerate(sug)] + [""] + \
        (["Amplo: " + " · ".join(sug2), ""] if sug2 else []) + \
        ["## Mais vistos sobre o tema (último ano, longos)", "", "| views | título | canal |", "|---|---|---|"] + \
        [f"| {mil(t['views'])} | {t['titulo']} | {t['canal']} |" for t in tops if t["views"]] + \
        ["", "Atenção: a busca pode mostrar títulos traduzidos pelo YouTube; confira o original antes de usar como modelo."] + \
        ["", "## Moldes de título que rendem acima da média em canais novos do mesmo idioma", "", "| molde | canal | vídeos | média de views | exemplo |", "|---|---|---|---|---|"] + \
        [f"| {m['molde']} | {m['canal']} | {m['n']} | {mil(m['media'])} | {m['exemplo']} |" for m in moldes[:15]] + \
        ["", "## Opções (o Claude preenche: cada uma diz qual dado usou)", ""]
    (pasta / f"{a.projeto}-{nome}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"pronto: {pasta / (a.projeto + '-' + nome + '.md')} · {len(sug)} buscas do público · {len(tops)} mais vistos · {len(moldes)} moldes no idioma")


if __name__ == "__main__":
    main()
