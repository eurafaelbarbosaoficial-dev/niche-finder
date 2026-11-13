"""Fotografa cada cena de um capítulo no momento mais completo (85% da cena). Uso: python -I fotos.py k3"""
import json, re, subprocess, sys
from pathlib import Path
cap = sys.argv[1]
html = Path(cap, "index.html").read_text(encoding="utf-8")
cenas = json.loads(re.search(r"const CENAS = (.*?);\n", html, re.S).group(1))
ts = [round(c["t0"] + 0.85 * (c["t1"] - c["t0"]), 2) for c in cenas]
r = subprocess.run(f'npx hyperframes snapshot --at {",".join(map(str, ts))} --json', cwd=cap, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
print("\n".join(re.findall(r'"([^"]*contact-sheet[^"]*)"', r.stdout)))
