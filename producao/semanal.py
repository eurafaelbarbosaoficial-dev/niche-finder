"""Pautas semanais (sugestão 3 da revisão de 13/11): toda semana o calendário de cada canal ganha temas novos MEDIDOS.

Roda o Claude Code sozinho (como o vigia) com a tarefa:
  1. coletar candidatos de dado (pautas.py coletar: molde no mundo, autocompletar do idioma, canal de referência);
  2. traduzir e gravar os candidatos (só os que vieram dos dados), medir (pautas.py medir);
  3. dar a nota da MATRIZ DE VALIDAÇÃO (Raj, vídeo 25) a cada pauta forte/boa e atualizar a ÁRVORE EDITORIAL;
  4. refazer o calendário e a esteira; commit e push.
A tarefa do Windows "Niche Finder - Pautas semanais" chama este arquivo (domingo de madrugada).
Uso: python -I producao/semanal.py [projeto ...]   (padrão: todos os projetos de producao/projetos.json)
"""
import json, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R))
from vigia import achar_claude, log  # noqa: E402

TAREFA = """Leia o CONTEXTO.md e o CLAUDE.md. Tarefa SEMANAL de pautas do projeto "{p}" (você está SOZINHO: não pergunte nada;
regra do dono: só dado real, nada inventado).
1. python -I pautas.py coletar validacoes/pedidos/{p}.json  → leia validacoes/candidatos/{p}.json e grave em pautas.candidatos
   SÓ itens que vieram dali (fonte A/B/C + evidência), traduzidos para o idioma do canal, sem repetir temas já medidos.
2. python -I pautas.py medir validacoes/pedidos/{p}.json --publicar
3. Para cada pauta forte ou boa sem "matriz" em docs/pautas/{p}.json, acrescente "matriz": notas 0–5 em demanda, assuntos (quantos
   vídeos o tema rende), completude ("dá para explicar tudo"), hipoteticos ("e se…"), visual, evergreen — cada nota com 1 frase de
   motivo apoiada nos números da pauta — e "matriz_total" (soma). Marque "matriz_fonte": "nota do Claude (opinião, Raj vídeo 25)".
4. Atualize "arvore" em docs/pautas/{p}.json: a árvore editorial do canal (tema → subtemas → pautas), só com pautas medidas.
5. python -I producao/calendario.py {p} --ref {ref} --feitos "{feitos}"  e  python -I producao/esteira.py
6. git add docs/pautas validacoes producao docs/calendario.json docs/esteira.json; commit "Pautas semanais: {p}"; push.
Responda com: quantas pautas novas, quantas fortes/boas e as 3 melhores pela matriz."""


def main():
    pjs = json.loads((R / "producao" / "projetos.json").read_text(encoding="utf-8"))
    projetos = sys.argv[1:] or sorted({p["projeto"] for p in pjs if p.get("projeto")})
    claude = achar_claude()
    if not claude:
        log("semanal: não achei o Claude Code de linha de comando"); return
    for p in projetos:
        feitos = ";".join(x["tema"] for x in pjs if x.get("projeto") == p and x.get("tema"))
        ref = next((json.loads((R / "videos" / x["video"] / "projeto.json").read_text(encoding="utf-8")).get("referencia")
                    for x in pjs if x.get("projeto") == p and (R / "videos" / x["video"] / "projeto.json").exists()), None) or "econ-in-a-nutshell"
        log(f"semanal: pautas de {p}")
        r = subprocess.run([claude, "-p", TAREFA.format(p=p, ref=ref, feitos=feitos), "--permission-mode", "acceptEdits",
                            "--allowedTools", "Read,Write,Edit,Glob,Grep,WebSearch,WebFetch,Bash(python:*),Bash(git:*),Bash(ls:*),Bash(cat:*)"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=R, timeout=3 * 3600)
        log(f"semanal {p}: {(r.stdout or r.stderr or '').strip()[-400:]}")


if __name__ == "__main__":
    main()
