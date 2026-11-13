"""Estudo de estilo de edição de UM vídeo de referência e comparação com o nosso (Raj, vídeo 29: "bíblia visual").

Reaproveita a LUPA da skill /estudar (estudos-de-mercado/ferramentas/estudo.py lupa): cortes, tipo de transição,
punches de zoom, câmera, efeitos sonoros (voz separada com Demucs) e música. Aqui ela roda em 3 trechos do vídeo
(gancho, meio e final) e os números viram uma RECEITA; depois o nosso vídeo é medido do mesmo jeito e comparado.

Uso:
  python -I producao/estilo.py estudar  <link ou arquivo> <slug>          (~2 min por minuto analisado; 9 min)
  python -I producao/estilo.py comparar <slug> <nosso.mp4>               (mede o nosso e escreve a comparação)
Saída: referencias/<slug>/estilo/receita.json, RECEITA.md (números) e, no comparar, COMPARACAO.md.
O agente .claude/agents/estudo-estilo.md abre as tiras e espectrogramas e escreve a parte de juízo.
"""
import json, re, statistics, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[1]
E = Path.home() / "Documents" / "estudos-de-mercado"
JAN = 180  # cada trecho: 3 min


def duracao(src):
    if Path(src).exists():
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)], capture_output=True, text=True)
        return float(r.stdout.strip() or 0)
    b = Path.home() / ".watch-skill" / "bin" / "yt-dlp.exe"
    r = subprocess.run([str(b) if b.exists() else "yt-dlp", "--no-warnings", "--print", "%(duration)s", src], capture_output=True, text=True)
    return float((r.stdout.strip().splitlines() or ["0"])[0] or 0)


def lupa(src, ini, fim):
    env = {**__import__("os").environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, str(E / "ferramentas" / "estudo.py"), "lupa", str(src), "--inicio", str(ini), "--fim", str(fim)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    m = re.findall(r"Pronto:\s*(.+lupa\.md)", r.stdout)
    if not m:
        print(r.stdout[-800:], r.stderr[-800:])
        sys.exit("a lupa falhou")
    return Path(m[-1].strip()).parent


def resumo(pasta):
    d = json.loads((pasta / "lupa_dados.json").read_text(encoding="utf-8"))
    dur = d["duracao"] or 1
    ts = sorted(c["t"] for c in d["cortes"])
    planos = [b - a for a, b in zip([0] + ts, ts + [dur])]
    tipos = {}
    for c in d["cortes"]:
        tipos[c["tipo"]] = tipos.get(c["tipo"], 0) + 1
    efe = {}
    for e in d.get("efeitos", []):
        efe[e["tipo"]] = efe.get(e["tipo"], 0) + 1
    hits = d.get("audio", {}).get("hits", [])
    sons = {}
    for h in hits:
        sons[h["tipo"]] = sons.get(h["tipo"], 0) + 1
    q = statistics.quantiles(planos, n=4) if len(planos) >= 4 else [None] * 3
    return {
        "pasta": str(pasta), "duracao": round(dur, 1),
        "cortes_por_min": round(len(ts) / (dur / 60), 1),
        "plano": {"medio": round(statistics.mean(planos), 2), "p25": q[0] and round(q[0], 2), "mediana": round(statistics.median(planos), 2), "p75": q[2] and round(q[2], 2), "maior": round(max(planos), 1)},
        "transicoes": {k: round(v / max(1, len(ts)), 2) for k, v in sorted(tipos.items(), key=lambda x: -x[1])},
        "efeitos_camera_por_min": round(len(d.get("efeitos", [])) / (dur / 60), 1), "efeitos_camera": efe,
        "camera_tempo": {k: round(v, 2) for k, v in d.get("tempo", {}).items()},
        "sons_por_min": round(len(hits) / (dur / 60), 1), "sons": sons,
        "cortes_com_som": round(sum(1 for c in d["cortes"] if c.get("som")) / max(1, len(ts)), 2),
        "musica": ({"bpm": d["audio"].get("bpm"), "confianca": round(d["audio"].get("bpm_conf") or 0, 2)} if d.get("audio") else None),
    }


def trechos(dur):
    if dur <= JAN * 1.2:
        return {"inteiro": (0, dur)}
    meio = max(JAN, dur / 2 - JAN / 2)
    return {"gancho": (0, JAN), "meio": (meio, meio + JAN), "final": (max(meio + JAN, dur - JAN), dur)}


def local(src, pasta):
    """Arquivo local do vídeo (baixa em 360p se for link) para o medidor de ritmo quadro a quadro."""
    if Path(src).exists():
        return Path(src)
    pasta.mkdir(parents=True, exist_ok=True)
    b = Path.home() / ".watch-skill" / "bin" / "yt-dlp.exe"
    dest = pasta / "video.mp4"
    if not dest.exists():
        subprocess.run([str(b) if b.exists() else "yt-dlp", "--no-warnings", "-f", "bv*[height<=360][ext=mp4]/bv*[height<=360]/worst", "-o", str(dest), src])
    return dest


def medir(src, pasta_videos):
    import ritmo
    dur = duracao(src)
    print("ritmo quadro a quadro do vídeo inteiro…", flush=True)
    rt = ritmo.analisar(local(src, pasta_videos))
    out = {"fonte": str(src), "duracao": round(dur, 1), "ritmo": {k: v for k, v in rt.items() if k not in ("cenas", "transicoes_lista")}, "trechos": {}}
    out["_ritmo_completo"] = rt
    for nome, (a, b) in trechos(dur).items():
        print(f"lupa {nome}: {a:.0f}–{b:.0f} s …", flush=True)
        out["trechos"][nome] = resumo(lupa(src, round(a, 1), round(b, 1)))
    return out


def tabela_ritmo(r):
    x = r["ritmo"]; d = x["duracao_cena"]
    tr = ", ".join(f"{k} {int(v['fracao']*100)}% ({v['quadros_medio']} q)" for k, v in x["transicoes"].items())
    return [f"- **Vídeo inteiro (quadro a quadro):** {x['cenas_total']} cenas · {x['trocas_por_min']} trocas/min · cena média {d['media']} s · "
            f"mediana {d['mediana']} s · metade entre {d['p25']} e {d['p75']} s · variação {int(d['cv']*100)}% · tendência {x['tendencia_seg_por_min']:+} s/min",
            f"- **Transições:** {tr}", f"- **Trocas a cada 30 s:** {x['curva_trocas_por_30s']}", ""]


def tabela(r):
    L = tabela_ritmo(r) + ["| trecho | trocas/min | plano médio | mediana (p25–p75) | maior plano | punches+câmera/min | sons/min | cortes com som | transição mais usada |",
         "|---|---|---|---|---|---|---|---|---|"]
    for n, t in r["trechos"].items():
        tr = next(iter(t["transicoes"].items()), ("—", 0))
        L.append(f"| {n} | {t['cortes_por_min']} | {t['plano']['medio']} s | {t['plano']['mediana']} s ({t['plano']['p25']}–{t['plano']['p75']}) | {t['plano']['maior']} s | "
                 f"{t['efeitos_camera_por_min']} | {t['sons_por_min']} | {int(t['cortes_com_som']*100)}% | {tr[0]} ({int(tr[1]*100)}%) |")
    return L


def main():
    cmd = sys.argv[1]
    if cmd == "estudar":
        src, slug = sys.argv[2], sys.argv[3]
        pasta = RAIZ / "referencias" / slug / "estilo"
        pasta.mkdir(parents=True, exist_ok=True)
        r = medir(src, RAIZ / "referencias" / slug / "_videos")
        rt = r.pop("_ritmo_completo")
        (pasta / "ritmo.json").write_text(json.dumps(rt, ensure_ascii=False, indent=1), encoding="utf-8")
        import ritmo
        (pasta / "RITMO.md").write_text(ritmo.relatorio(rt), encoding="utf-8")
        (pasta / "receita.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        L = [f"# Receita de edição (números): {src}", "", "Medido com a lupa da /estudar. Tipos de transição e contagem de sons são PALPITES: conferir nas tiras e espectrogramas de cada pasta.", ""]
        L += tabela(r) + ["", "## Detalhe por trecho", ""]
        for n, t in r["trechos"].items():
            L += [f"### {n}", f"- pasta da lupa: `{t['pasta']}`", f"- transições: {t['transicoes']}", f"- câmera (fração do tempo): {t['camera_tempo']}",
                  f"- efeitos de câmera: {t['efeitos_camera']}", f"- sons: {t['sons']}", f"- música: {t['musica']}", ""]
        (pasta / "RECEITA.md").write_text("\n".join(L), encoding="utf-8")
        print(f"pronto: {pasta / 'RECEITA.md'}")
    elif cmd == "comparar":
        slug, nosso = sys.argv[2], sys.argv[3]
        pasta = RAIZ / "referencias" / slug / "estilo"
        ref = json.loads((pasta / "receita.json").read_text(encoding="utf-8"))
        r = medir(nosso, pasta)
        rt = r.pop("_ritmo_completo")
        import ritmo
        (pasta / "RITMO-NOSSO.md").write_text(ritmo.relatorio(rt), encoding="utf-8")
        (pasta / "nosso.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        L = [f"# Comparação de estilo: nosso × referência ({slug})", "", "## Referência", ""] + tabela(ref) + ["", "## Nosso", ""] + tabela(r) + ["", "## Diferenças (nosso ÷ referência, por trecho)", ""]
        ra, rb = ref["ritmo"], r["ritmo"]
        def y(va, vb): return f"{vb} × {va}" + (f" ({vb/va:.1f}×)" if va else "")
        L += [f"- **vídeo inteiro:** trocas/min {y(ra['trocas_por_min'], rb['trocas_por_min'])} · cena média {y(ra['duracao_cena']['media'], rb['duracao_cena']['media'])} s · "
              f"mediana {y(ra['duracao_cena']['mediana'], rb['duracao_cena']['mediana'])} s · variação {y(ra['duracao_cena']['cv'], rb['duracao_cena']['cv'])}"]
        for n in ref["trechos"]:
            a, b = ref["trechos"][n], r["trechos"].get(n)
            if not b:
                continue
            def x(k, sub=None):
                va = a[k][sub] if sub else a[k]; vb = b[k][sub] if sub else b[k]
                return f"{vb} × {va}" + (f" ({vb/va:.1f}×)" if va else "")
            L += [f"- **{n}:** trocas/min {x('cortes_por_min')} · plano médio {x('plano', 'medio')} s · efeitos de câmera/min {x('efeitos_camera_por_min')} · sons/min {x('sons_por_min')}"]
        L += ["", "Regra de leitura (critério nosso): diferença de mais de 1,5× em trocas/min, plano médio ou sons/min = **médio**; mais de 3× = **alto**."]
        (pasta / "COMPARACAO.md").write_text("\n".join(L), encoding="utf-8")
        print(f"pronto: {pasta / 'COMPARACAO.md'}")


if __name__ == "__main__":
    main()
