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


def atualizar_esteira():
    """Refaz docs/esteira.json (aba Produção) e publica se mudou."""
    try:
        subprocess.run([sys.executable, "-I", str(AQUI / "producao" / "esteira.py")], capture_output=True, cwd=AQUI, timeout=120)
        subprocess.run([sys.executable, "-I", str(AQUI / "producao" / "licoes.py"), "site"], capture_output=True, cwd=AQUI, timeout=60)
        # desempenho dos nossos vídeos: no máximo a cada 3 h
        marca = ESTADO / "desempenho.ultima"
        if not marca.exists() or time.time() - marca.stat().st_mtime > 3 * 3600:
            subprocess.run([sys.executable, "-I", str(AQUI / "producao" / "desempenho.py"), "medir"], capture_output=True, cwd=AQUI, timeout=600)
            marca.write_text(str(time.time()))
        mud = subprocess.run(["git", "status", "--porcelain", "docs/esteira.json", "docs/licoes.json", "docs/desempenho.json"], capture_output=True, text=True, cwd=AQUI).stdout.strip()
        if mud:
            subprocess.run(["git", "add", "docs/esteira.json", "docs/licoes.json", "docs/desempenho.json"], cwd=AQUI)
            subprocess.run(["git", "commit", "-qm", "Esteira atualizada"], cwd=AQUI)
            subprocess.run(["git", "pull", "-q", "--rebase"], cwd=AQUI)
            subprocess.run(["git", "push", "-q"], cwd=AQUI)
    except Exception as e:
        log(f"esteira: {e}")


def main():
    if TRAVA.exists() and time.time() - TRAVA.stat().st_mtime < 90 * 60:
        return  # outro roteiro em andamento
    atualizar_esteira()
    pedidos = json.loads(gh("issue", "list", "--label", "roteiro", "--state", "open", "--json", "number,title,body,createdAt") or "[]")
    ideias = json.loads(gh("issue", "list", "--label", "ideia", "--state", "open", "--json", "number,title,body,createdAt") or "[]")
    if not pedidos and ideias:
        # ideia do dono (botão "Nova ideia" da aba Produção): medir com dados antes de entrar no calendário
        for i in ideias:
            i["body"] = (f"O dono deixou esta IDEIA de vídeo na aba Produção: \"{i['title']}\".\n\n{i.get('body') or ''}\n\n"
                         "Leia o CONTEXTO.md. Meça a ideia SÓ com dados (pautas.py: autocompletar e views no idioma do canal; "
                         "nada inventado). Se tiver demanda, acrescente em docs/pautas/<projeto>.json e rode "
                         "`python -I producao/calendario.py <projeto> --ref <referência>` e `python -I producao/esteira.py`; "
                         "faça commit e push. Responda com o veredito (forte/boa/fraca) e os números.")
        for i in ideias:
            i["ideia"] = True
        pedidos = ideias
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
        ideia = p.get("ideia")
        gh("issue", "comment", str(n), "--body", "🤖 Comecei a medir a ideia com dados (~15–30 min)." if ideia else
           "🤖 Comecei o roteiro. Aparece na aba Roteiro do site quando terminar (~15–30 min).")
        fim = ("Responda só com o veredito e os números." if ideia else
               "Antes de publicar, rode `python -I producao/revisor_roteiro.py <slug>` e corrija o que for alto. Ao terminar, publique com "
               "`python -I roteiro.py publicar <slug>` e responda só com o slug publicado e um resumo de 3 linhas.")
        instr = (p["body"] or "") + (
            "\n\nVocê está rodando SOZINHO (sem o dono olhando): não faça perguntas; decida pelas regras do CONTEXTO.md "
            "e do CLAUDE.md (dados reais, nada inventado, fatos com fonte). " + fim)
        cmd = [claude, "-p", instr, "--permission-mode", "acceptEdits",
               "--allowedTools", "Read,Write,Edit,Glob,Grep,WebSearch,WebFetch,Bash(python:*),Bash(git:*),Bash(ls:*),Bash(cat:*)"]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=AQUI, timeout=80 * 60)
        saida = (r.stdout or r.stderr or "").strip()[-1500:]
        if r.returncode == 0 and "Not logged in" not in saida:
            gh("issue", "comment", str(n), "--body", ("✅ Ideia medida.\n\n" if ideia else "✅ Roteiro pronto.\n\n") + saida +
               "\n\nVeja em https://eurafaelbarbosaoficial-dev.github.io/niche-finder/" + ("producao.html" if ideia else "roteiro.html"))
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
