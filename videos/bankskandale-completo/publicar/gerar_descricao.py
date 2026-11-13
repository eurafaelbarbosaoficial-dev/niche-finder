"""Gera publicar/DESCRICAO.txt (título, descrição em alemão com capítulos, fontes e créditos) e TAGS.txt.
Os tempos dos capítulos vêm das durações reais das partes renderizadas."""
import json, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).parent.parent
ROT = json.load(open(AQUI.parent.parent / "roteiros" / "bankskandale-de" / "roteiro.json", encoding="utf-8"))


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)


def mmss(s):
    s = int(s)
    return f"{s // 60}:{s % 60:02d}"


# capítulo 1 = 16,95 + k1b + 11,35 + k1d
d1 = 16.95 + dur(AQUI / "k1b/renders/k1b.mp4") + (28.3 - 16.95) + dur(AQUI / "k1d/renders/k1d.mp4")
nomes = ["Razzia bei der Deutschen Bank", "Ebene 1: Die Bank auf deinem Handy (N26)", "Ebene 2: Banken, die wegschauen (ING, Commerzbank)",
         "Ebene 3: Die Maschine (Deutsche Bank)", "Ebene 4: Die Bank der Kartelle (HSBC, TD Bank)", "Ebene 5: Eine Filiale, 200 Milliarden (Danske Bank)",
         "Der Grund: Die Bank, die das Verbrechen war (BCCI)", "Strafe zahlen, weitermachen"]
inicios, t = [0.0], d1
for n in range(2, 9):
    inicios.append(t)
    t += dur(AQUI / f"k{n}/renders/k{n}.mp4")

fontes = []
for b in ROT["blocos"]:
    for f in b.get("fontes", []):
        if f not in fontes:
            fontes.append(f)

titulo = ROT["titulo"]
desc = f"""Die meisten denken bei Geldwäsche an Dönerläden und Koffer voller Bargeld. Aber am Ende landet jeder schmutzige Euro an demselben Ort: auf einem Bankkonto. Wir gehen den Eisberg der größten Geldwäsche-Skandale der Banken durch – von der Smartphone-Bank bis zu der Bank, die selbst das Verbrechen war.

Kapitel:
""" + "\n".join(f"{mmss(s)} {n}" for s, n in zip(inicios, nomes)) + """

Wichtig: Eine Verdachtsmeldung ist kein Beweis für ein Verbrechen. Alle Zahlen stammen aus Behördenmitteilungen, Gerichtsdokumenten und Medienberichten – die Quellen stehen unten.

Quellen:
""" + "\n".join(fontes) + """

Soundeffekte:
"Deep Cinematic Impact" von MeijstroAudio (CC BY 4.0) – https://freesound.org/people/MeijstroAudio/sounds/377303
"Gold coin clink (100 Rubles Witte)" von Walking.With.Microphones (CC BY 4.0) – https://freesound.org/people/Walking.With.Microphones/sounds/557223
Weitere Effekte: CC0 (Freesound: Breviceps, kermite607, Rizzard, MaoDin204, chriskalos).

#Geldwäsche #Banken #DeutscheBank
"""
(AQUI / "publicar" / "DESCRICAO.txt").write_text(f"TÍTULO:\n{titulo}\n\nDESCRIÇÃO:\n{desc}", encoding="utf-8")
tags = ["Geldwäsche", "Geldwäsche erklärt", "Banken Skandal", "Deutsche Bank", "Deutsche Bank Razzia", "Danske Bank", "HSBC Kartell", "N26 BaFin",
        "ING Geldwäsche", "Commerzbank", "BCCI", "FinCEN Files", "Spiegelgeschäfte", "TD Bank", "Eisberg", "Finanzskandal", "Wirtschaft erklärt", "Doku"]
(AQUI / "publicar" / "TAGS.txt").write_text(", ".join(tags), encoding="utf-8")
print((AQUI / "publicar" / "DESCRICAO.txt").read_text(encoding="utf-8")[:1500])
