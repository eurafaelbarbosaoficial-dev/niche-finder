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


def novos_canais():
    """Botão "Adicionar canal" da aba Meus canais: issue com rótulo "meu-canal", corpo com 'Projeto: <id>' e o link.
    Grava o link em producao/canais.json (o canal passa a ser medido a cada 3 h) e fecha a issue."""
    import re
    pedidos = json.loads(gh("issue", "list", "--label", "meu-canal", "--state", "open", "--json", "number,title,body") or "[]")
    if not pedidos:
        return
    arq = AQUI / "producao" / "canais.json"
    canais = json.loads(arq.read_text(encoding="utf-8"))
    for p in pedidos:
        txt = (p.get("title") or "") + "\n" + (p.get("body") or "")
        link = re.search(r"(https?://(?:www\.)?youtube\.com/[^\s)]+|@[\w.\-]+|UC[\w-]{22})", txt)
        proj = re.search(r"Projeto:\s*([\w\-]+)", txt)
        alvo = next((c for c in canais if proj and c["id"] == proj.group(1)), None)
        if not link or not alvo:
            gh("issue", "comment", str(p["number"]), "--body", "⚠️ Não achei o link do canal ou o projeto no pedido. Edite e deixe o link do canal no corpo.")
            continue
        alvo["youtube"] = link.group(1)
        alvo.pop("youtube_id", None)
        arq.write_text(json.dumps(canais, ensure_ascii=False, indent=1), encoding="utf-8")
        subprocess.run([sys.executable, "-I", str(AQUI / "producao" / "roteiros_site.py")], capture_output=True, cwd=AQUI, timeout=120)
        subprocess.run([sys.executable, "-I", str(AQUI / "producao" / "meus_canais.py")], capture_output=True, cwd=AQUI, timeout=900)
        gh("issue", "comment", str(p["number"]), "--body", f"✅ Canal ligado ao projeto {alvo['id']}. Ele é medido a cada 3 h na aba Meus canais.")
        gh("issue", "close", str(p["number"]))
        log(f"Canal ligado: {alvo['id']} → {link.group(1)}")


def ler_prints():
    """Prints novos do YouTube Studio na pasta privada prints-studio/<canal>/: o Claude lê e grava os números."""
    sys.path.insert(0, str(AQUI / "producao"))
    import studio
    novos = studio.pendentes()
    if not novos:
        return
    claude = achar_claude()
    if not claude:
        return
    lista = "\n".join(f"- {f} (canal: {f.parent.name})" for f in novos)
    instr = ("Leia o CONTEXTO.md. Prints NOVOS do YouTube Studio do dono (pasta privada; NÃO copie as imagens para o git):\n" + lista +
             "\n\nPara cada imagem: abra com o Read e grave SÓ os números que aparecem no print com "
             "`python -I producao/studio.py adicionar <canal> '<json>'` (formato no topo de producao/studio.py; data = data do arquivo "
             "ou a que aparece no print). Em 'leitura', 2–3 frases: dado primeiro, depois o que fazer (marcado como hipótese). "
             "Se a retenção ou os cliques mostrarem um problema claro (ex.: queda forte nos primeiros 30 s), grave uma lição com "
             "`python -I producao/licoes.py adicionar …`. No fim rode `python -I producao/meus_canais.py` e "
             "`python -I producao/studio.py marcar <arquivos>`. Responda em 3 linhas com o resumo.")
    log(f"prints do Studio: {len(novos)} novo(s)")
    r = subprocess.run([claude, "-p", instr, "--permission-mode", "acceptEdits",
                        "--allowedTools", "Read,Write,Edit,Glob,Grep,Bash(python:*),Bash(ls:*)"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=AQUI, timeout=30 * 60)
    log(f"prints: {(r.stdout or r.stderr or '').strip()[-300:]}")


def atualizar_esteira():
    """Refaz docs/esteira.json (aba Produção) e publica se mudou."""
    try:
        subprocess.run([sys.executable, "-I", str(AQUI / "producao" / "esteira.py")], capture_output=True, cwd=AQUI, timeout=120)
        subprocess.run([sys.executable, "-I", str(AQUI / "producao" / "licoes.py"), "site"], capture_output=True, cwd=AQUI, timeout=60)
        novos_canais()
        # desempenho dos nossos vídeos e canais: no máximo a cada 3 h
        marca = ESTADO / "desempenho.ultima"
        if not marca.exists() or time.time() - marca.stat().st_mtime > 3 * 3600:
            subprocess.run([sys.executable, "-I", str(AQUI / "producao" / "desempenho.py"), "medir"], capture_output=True, cwd=AQUI, timeout=600)
            subprocess.run([sys.executable, "-I", str(AQUI / "producao" / "meus_canais.py")], capture_output=True, cwd=AQUI, timeout=900)
            marca.write_text(str(time.time()))
        ler_prints()
        arqs = ["docs/esteira.json", "docs/licoes.json", "docs/desempenho.json", "docs/meus-canais.json", "producao/studio.json", "producao/canais.json", "docs/canais.json"]
        mud = subprocess.run(["git", "status", "--porcelain", *arqs], capture_output=True, text=True, cwd=AQUI).stdout.strip()
        if mud:
            subprocess.run(["git", "add", *[a for a in arqs if (AQUI / a).exists()]], cwd=AQUI)
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
