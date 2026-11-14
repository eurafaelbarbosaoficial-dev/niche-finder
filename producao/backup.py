"""Backup privado semanal (toda segunda-feira, tarefa "Niche Finder - Backup"). TUDO dentro da pasta Niche Finder.

O repositório do site (niche-finder) é PÚBLICO; o que é privado vai para a pasta `privado/`, que é outro repositório,
PRIVADO (eurafaelbarbosaoficial-dev/niche-finder-privado), fora do git do site:
  privado/backup/          chave da API do YouTube, histórico dos nossos canais, prints do YouTube Studio
  privado/skills/          skills do dono (canal-dark, estudar, novela-americana, claude-youtube)
  privado/memoria-claude/  memória do Claude
  privado/zips/            zip completo COM o vídeo final (só no notebook: o GitHub recusa arquivo > 100 MB; guarda 3)
Uso: python -I producao/backup.py
"""
import datetime as dt, shutil, subprocess, sys, zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(__file__).resolve().parents[1]
P = R / "privado"
LIMITE = 95 * 1024 * 1024
ITENS = ["estado/youtube-api.txt", "estado/meus-canais.json", "estado/desempenho.json", "prints-studio"]
SKILLS = ["canal-dark", "estudar", "novela-americana", "claude-youtube"]
MEMORIA = Path.home() / ".claude" / "projects" / "C--Users-Vaio-Documents-Niche-Finder" / "memory"


def main():
    arqs = []
    for it in ITENS:
        p = R / it
        arqs += [x for x in p.rglob("*") if x.is_file()] if p.is_dir() else ([p] if p.exists() else [])
    for f in arqs:
        if f.stat().st_size <= LIMITE:
            alvo = P / "backup" / f.relative_to(R)
            alvo.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, alvo)
    sk = Path.home() / ".claude" / "skills"
    for s in SKILLS:
        if (sk / s).exists():
            shutil.copytree(sk / s, P / "skills" / s, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    if MEMORIA.exists():
        (P / "memoria-claude").mkdir(exist_ok=True)
        for m in MEMORIA.glob("*.md"):
            shutil.copy2(m, P / "memoria-claude" / m.name)
    if (P / ".git").exists():
        subprocess.run(["git", "-C", str(P), "add", "-A"])
        r = subprocess.run(["git", "-C", str(P), "commit", "-qm", f"Backup {dt.date.today()}"], capture_output=True, text=True)
        subprocess.run(["git", "-C", str(P), "push", "-q", "-u", "origin", "main"])
        print("GitHub privado:", "atualizado" if r.returncode == 0 else "nada mudou")
    else:
        print("Falta o repositório privado em privado/ (o instalar.ps1 clona): só o zip local.")
    z = P / "zips" / f"backup-privado-{dt.date.today()}.zip"
    z.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(z, "w") as f:
        for a in arqs + list(R.glob("videos/*/publicar/*.mp4")):
            f.write(a, a.relative_to(R), compress_type=zipfile.ZIP_STORED if a.suffix == ".mp4" else zipfile.ZIP_DEFLATED)
    for velho in sorted(z.parent.glob("backup-privado-*.zip"))[:-3]:
        velho.unlink()
    print(f"zip local: {z} ({z.stat().st_size // 1_000_000} MB)")


if __name__ == "__main__":
    main()
