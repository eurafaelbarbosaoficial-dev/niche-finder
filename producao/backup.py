"""Backup privado semanal (toda segunda-feira, tarefa "Niche Finder - Backup").

O repositório do Niche Finder é PÚBLICO, então o que é privado vai para o repositório PRIVADO estudos-de-mercado,
pasta backup-niche-finder/:
  - estado/youtube-api.txt (chave da API do YouTube)
  - estado/meus-canais.json e estado/desempenho.json (histórico dos nossos canais)
  - prints-studio/ (prints do YouTube Studio)
Arquivos acima de 95 MB (o GitHub recusa > 100 MB), como o vídeo final, ficam só no zip local:
  Documents/Backup Niche Finder/backup-privado-AAAA-MM-DD.zip (guarda os 3 mais recentes).
Uso: python -I producao/backup.py
"""
import datetime as dt, shutil, subprocess, sys, zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(__file__).resolve().parents[1]
E = Path.home() / "Documents" / "estudos-de-mercado"
DST = E / "backup-niche-finder"
LIMITE = 95 * 1024 * 1024
ITENS = ["estado/youtube-api.txt", "estado/meus-canais.json", "estado/desempenho.json", "prints-studio"]


def main():
    arqs = []
    for it in ITENS:
        p = R / it
        arqs += [x for x in p.rglob("*") if x.is_file()] if p.is_dir() else ([p] if p.exists() else [])
    # 1) GitHub privado (só o que cabe)
    if (E / ".git").exists():
        subprocess.run(["git", "-C", str(E), "pull", "-q", "--rebase", "--autostash"])
        for f in arqs:
            if f.stat().st_size <= LIMITE:
                alvo = DST / f.relative_to(R)
                alvo.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, alvo)
        (DST / "LEIA-ME.txt").write_text("Backup automático do Niche Finder (producao/backup.py, toda segunda-feira).\n"
                                         "Em máquina nova: copie o conteúdo desta pasta para dentro de Documents/Niche Finder.\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(E), "add", "backup-niche-finder"])
        r = subprocess.run(["git", "-C", str(E), "commit", "-qm", f"Backup Niche Finder {dt.date.today()}"], capture_output=True, text=True)
        subprocess.run(["git", "-C", str(E), "push", "-q"])
        print("GitHub privado:", "atualizado" if r.returncode == 0 else "nada mudou")
    else:
        print("Repositório estudos-de-mercado não encontrado: só o zip local.")
    # 2) zip local completo (com o vídeo final)
    pasta = Path.home() / "Documents" / "Backup Niche Finder"
    pasta.mkdir(exist_ok=True)
    z = pasta / f"backup-privado-{dt.date.today()}.zip"
    with zipfile.ZipFile(z, "w") as f:
        for a in arqs + list(R.glob("videos/*/publicar/*.mp4")):
            f.write(a, a.relative_to(R), compress_type=zipfile.ZIP_STORED if a.suffix == ".mp4" else zipfile.ZIP_DEFLATED)
    for velho in sorted(pasta.glob("backup-privado-*.zip"))[:-3]:
        velho.unlink()
    print(f"zip local: {z} ({z.stat().st_size // 1_000_000} MB)")


if __name__ == "__main__":
    main()
