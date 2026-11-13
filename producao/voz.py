"""Narração de cada bloco do roteiro (uma tomada contínua por capítulo — lição L001).

A CHAVE NUNCA É SALVA: vem só da variável de ambiente K, que o dono manda na sessão (ele troca de app de voz).
Provedor atual: ai84 (ElevenLabs v4). Outro provedor = acrescentar uma função aqui.

Uso (bash):  K=<chave> python -I producao/voz.py <roteiro.json> <pasta voz/> [--blocos 1,3] [--voz ID] [--idioma de]
Mostra o custo de cada bloco. Não regera o que já existe.
"""
import argparse, json, os, sys, time, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
VOZ_PADRAO = "kkJxCnlRCckmfFvzDW5Q"   # "Alexander - Deep TV Narrator" (aprovada pelo dono)
B = "https://api.ai84.pro"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("roteiro"); ap.add_argument("saida")
    ap.add_argument("--blocos"); ap.add_argument("--voz", default=VOZ_PADRAO); ap.add_argument("--idioma")
    a = ap.parse_args()
    K = os.environ.get("K")
    if not K:
        sys.exit("Falta a chave: rode com K=<chave> na frente (ela não é salva em lugar nenhum).")
    H = {"xi-api-key": K, "Content-Type": "application/json", "User-Agent": "curl/8.5.0"}   # o User-Agent do Python leva 403

    def req(url, data=None):
        r = urllib.request.Request(B + url, data=json.dumps(data).encode() if data else None, headers=H, method="POST" if data else "GET")
        return json.loads(urllib.request.urlopen(r, timeout=90).read())

    def baixar(u, f):
        r = urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"})
        open(f, "wb").write(urllib.request.urlopen(r, timeout=180).read())

    rot = json.load(open(a.roteiro, encoding="utf-8"))
    idioma = a.idioma or rot.get("idioma", "de")
    saida = Path(a.saida); saida.mkdir(parents=True, exist_ok=True)
    so = [int(x) for x in a.blocos.split(",")] if a.blocos else None
    total = 0
    for i, b in enumerate(rot["blocos"], 1):
        if so and i not in so:
            continue
        mp3 = saida / f"bloco-{i}.mp3"
        if mp3.exists() and mp3.stat().st_size > 10000:
            print(i, "já existe"); continue
        txt = " ".join(b["texto"].split())
        for _ in range(3):
            try:
                j = req("/v2/text-to-speech/async", {"text": txt, "voice_id": a.voz, "model_id": "eleven_v4", "language_code": idioma, "with_transcript": True,
                                                     "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.25, "speed": 1.0, "use_speaker_boost": True}})
                break
            except Exception as e:
                print(i, "erro ao criar", e); time.sleep(10)
        else:
            sys.exit(1)
        total += j.get("credit_cost") or 0
        print(i, "criado, custo", j.get("credit_cost"), len(txt), "caracteres", flush=True)
        s = {}
        for _ in range(200):
            time.sleep(4)
            try:
                s = req("/v2/text-to-speech/async/" + j["job_id"])["job"]
            except Exception as e:
                print("  erro ao consultar", e); continue
            if s["status"] in ("done", "failed"):
                break
        print(i, s.get("status"), s.get("errorMessage") or "", flush=True)
        if s.get("status") == "done":
            baixar(s["audioUrl"], mp3)
    print("custo total", total)


if __name__ == "__main__":
    main()
