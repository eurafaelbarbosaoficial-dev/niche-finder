"""Converte as legendas json3 em texto com o minuto a cada ~30 s. Uso: python -I limpar.py"""
import json, sys, glob, os
sys.stdout.reconfigure(encoding="utf-8")
base = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(base, "texto"), exist_ok=True)
info = {}
for l in open(os.path.join(base, "info.tsv"), encoding="utf-8"):
    p = l.rstrip("\n").split("\t")
    if len(p) >= 6: info[p[0]] = p
ordem = [l.strip() for l in open(os.path.join(base, "links.txt")) if l.strip()]
for n, vid in enumerate(ordem, 1):
    arqs = sorted(glob.glob(os.path.join(base, "legendas", vid + ".*.json3")), key=lambda a: ("orig" not in a, a))
    if not arqs:
        print(f"{n:02d} {vid}: SEM LEGENDA"); continue
    ev = json.load(open(arqs[0], encoding="utf-8")).get("events", [])
    blocos, atual, t0 = [], [], None
    for e in ev:
        txt = "".join(s.get("utf8", "") for s in e.get("segs", []) or []).replace("\n", " ").strip()
        if not txt: continue
        t = e.get("tStartMs", 0) // 1000
        if t0 is None: t0 = t
        if t - t0 >= 30 and atual:
            blocos.append((t0, " ".join(atual))); atual, t0 = [], t
        atual.append(txt)
    if atual: blocos.append((t0, " ".join(atual)))
    i = info.get(vid, [vid, "?", "?", "?", "?", "?"])
    cab = f"# {i[5]}\nid {vid} · canal {i[4]} · publicado {i[1]} · {int(i[2])//60 if i[2].isdigit() else '?'} min · {i[3]} views\n\n"
    corpo = "\n".join(f"[{t//60}:{t%60:02d}] {x}" for t, x in blocos)
    nome = f"{n:02d}_{vid}.txt"
    open(os.path.join(base, "texto", nome), "w", encoding="utf-8").write(cab + corpo)
    print(f"{n:02d} {vid}: {len(corpo.split())} palavras · {i[5][:70]}")
