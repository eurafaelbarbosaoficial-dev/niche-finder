"""Vigia de pedidos de roteiro.

O botão "Fazer roteiro" do site abre uma issue no GitHub com o rótulo "roteiro" e o pedido no corpo.
Este vigia (tarefa do Windows a cada 10 min) pega o pedido mais antigo em aberto, roda o Claude Code sozinho
(sem janela) na pasta do projeto para escrever e publicar o roteiro, comenta o resultado e fecha a issue.

Uso: python -I vigia.py            (faz no máximo 1 pedido por vez)
Precisa: gh logado no GitHub e o Claude Code de linha de comando logado (o dono faz o login uma vez: `claude`, /login).
"""
import datetime as dt, glob, json, os, shutil, subprocess, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).resolve().parent
ESTADO = AQUI / "estado"
LOG = ESTADO / "vigia.txt"
TRAVA = ESTADO / "vigia.lock"
REPO = "eurafaelbarbosaoficial-dev/niche-finder"


def log(m):
    ESTADO.mkdir(exist_ok=True)
    linha = f"{dt.datetime.now():%d/%m %H:%M:%S} {m}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def achar_claude():
    for c in (shutil.which("claude"), str(Path.home() / ".local" / "bin" / "claude.exe")):
        if c and Path(c).exists():
            return c
    cands = glob.glob(str(Path(os.environ.get("LOCALAPPDATA", "")) / "Claude-Data" / "*" / "claude-code" / "*" / "*" / "claude.exe"))
    return max(cands, key=os.path.getmtime) if cands else None


def gh(*args):
    p = subprocess.run(["gh", *args, "--repo", REPO], capture_output=True, text=True, encoding="utf-8", cwd=AQUI)
    return p.stdout


def main():
    if TRAVA.exists() and time.time() - TRAVA.stat().st_mtime < 90 * 60:
        return  # outro roteiro em andamento
    pedidos = json.loads(gh("issue", "list", "--label", "roteiro", "--state", "open", "--json", "number,title,body,createdAt") or "[]")
    if not pedidos:
        return
    claude = achar_claude()
    if not claude:
        log("Não achei o Claude Code de linha de comando.")
        return
    p = sorted(pedidos, key=lambda x: x["createdAt"])[0]
    n = p["number"]
    TRAVA.write_text(str(n))
    try:
        log(f"Pedido #{n}: {p['title']}")
        gh("issue", "comment", str(n), "--body", "🤖 Comecei o roteiro. Aparece na aba Roteiro do site quando terminar (~15–30 min).")
        instr = (p["body"] or "") + (
            "\n\nVocê está rodando SOZINHO (sem o dono olhando): não faça perguntas; decida pelas regras do CONTEXTO.md "
            "e do CLAUDE.md (dados reais, nada inventado, fatos com fonte). Ao terminar, publique com "
            "`python -I roteiro.py publicar <slug>` e responda só com o slug publicado e um resumo de 3 linhas.")
        cmd = [claude, "-p", instr, "--permission-mode", "acceptEdits",
               "--allowedTools", "Read,Write,Edit,Glob,Grep,WebSearch,WebFetch,Bash(python:*),Bash(git:*),Bash(ls:*),Bash(cat:*)"]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=AQUI, timeout=80 * 60)
        saida = (r.stdout or r.stderr or "").strip()[-1500:]
        if r.returncode == 0 and "Not logged in" not in saida:
            gh("issue", "comment", str(n), "--body", "✅ Roteiro pronto.\n\n" + saida +
               "\n\nVeja em https://eurafaelbarbosaoficial-dev.github.io/niche-finder/roteiro.html")
            gh("issue", "close", str(n))
            log(f"Pedido #{n} pronto.")
        else:
            gh("issue", "comment", str(n), "--body", "⚠️ Não consegui terminar:\n\n```\n" + saida + "\n```\n"
               "Se diz 'Not logged in', abra um terminal, rode `claude` e faça /login uma vez. O pedido fica aberto e eu tento de novo.")
            log(f"Pedido #{n} falhou: {saida[:200]}")
    finally:
        TRAVA.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
