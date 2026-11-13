"""Gera producao/modelo-video/CATALOGO.md: cada modelo de cena do motor, os campos que ele lê e um exemplo REAL
já usado num vídeo (cenas.py). O diretor de cenas consulta este catálogo para escrever o cenas.py sem errar campo.
Uso: python -I producao/catalogo.py"""
import ast, json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
R = Path(__file__).resolve().parents[1]
js = (R / "producao/modelo-video/comum/js/motor.js").read_text(encoding="utf-8")
blocos = re.split(r"\n  T\.(\w+) = \(ctx, c, lt, t, f\) => \{", js)
campos = {}
for i in range(1, len(blocos), 2):
    nome, corpo = blocos[i], blocos[i + 1].split("\n  };")[0]
    campos[nome] = sorted(set(re.findall(r"\bc\.(\w+)", corpo)) - {"t0", "t1", "dur"})
exemplos = {}
for f in sorted((R / "videos").glob("*/cenas.py")):
    arv = ast.parse(f.read_text(encoding="utf-8"))
    for n in ast.walk(arv):
        if isinstance(n, ast.Dict):
            try:
                d = ast.literal_eval(n)
            except Exception:
                continue
            if isinstance(d, dict) and "tipo" in d and d["tipo"] not in exemplos:
                exemplos[d["tipo"]] = (d, f.parent.name)
L = ["# Catálogo de modelos de cena (gerado por producao/catalogo.py — não editar à mão)", "",
     "Campos comuns a todos: `tipo`, `em` (palavras da narração onde a cena começa; None = início do capítulo),",
     "`passos` (quando cada elemento entra: segundos desde o início da cena OU palavras da narração; 99 = nunca/fim),",
     "`detetive` (pose: neutro, pensa, desconfia, surpreso, preocupado, bravo, aponta), `fundo` (papel|noite|agua), `foco` [x,y], `semFade`.",
     "Texto com *asteriscos* = destaque em itálico terracota.", ""]
for nome, cs in campos.items():
    L += [f"## {nome}", f"- campos lidos: {', '.join('`'+c+'`' for c in cs) or '—'}"]
    if nome in exemplos:
        L += [f"- exemplo real ({exemplos[nome][1]}):", "```python", json.dumps(exemplos[nome][0], ensure_ascii=False), "```"]
    L.append("")
(R / "producao/modelo-video/CATALOGO.md").write_text("\n".join(L), encoding="utf-8")
print(len(campos), "modelos;", len(exemplos), "com exemplo")
