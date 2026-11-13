"""Ritmo do vídeo INTEIRO, cena por cena, com precisão de quadro (matemática, sem palpite).

Para cada quadro t (cinza, 96x54) calcula:
  d1[t]  = diferença média |f[t] - f[t-1]|            (mudança de um quadro para o seguinte)
  dK[t]  = diferença média |f[t] - f[t-K]|  (K=8)     (mudança acumulada em ~1/4 s)
  L[t]   = luz média do quadro
Regras:
- CORTE SECO: d1[t] é um pico isolado: d1[t] >= LIM_CORTE e >= 3x a mediana local, e os vizinhos d1[t±1] < 40% dele.
- TRANSIÇÃO GRADUAL: trecho em que dK fica alto (>= LIM_GRAD) sem pico isolado. Começo e fim = onde dK cruza o
  limite. Tipo, pela matemática:
    * fade para preto/branco: a luz mínima (máxima) dentro do trecho cai abaixo de 18 (sobe acima de 235) e é
      bem menor (maior) que a luz das duas pontas;
    * fusão (dissolve): o quadro do meio é uma MISTURA das pontas: f_meio ≈ a·f_ini + (1-a)·f_fim. Resolve 'a'
      por mínimos quadrados; se o erro que sobra é < 35% do erro de usar só uma ponta, é fusão;
    * senão: movimento (zoom/pan/deslize) — conta como transição em movimento se as pontas são cenas diferentes
      (diferença entre as pontas >= LIM_GRAD), ou como movimento de câmera dentro da cena.
- CENA = intervalo entre duas transições (a transição gradual divide no meio).
Saída: lista de cenas (início, fim, duração em s e em quadros, transição de entrada e sua duração em quadros),
estatística (média, mediana, desvio, coeficiente de variação, percentis, histograma), curva de ritmo (trocas a cada
30 s) e tendência (inclinação da duração da cena ao longo do vídeo, em s por minuto).

Uso: python -I producao/ritmo.py <video> [--saida pasta] [--inicio S --fim S]
"""
import argparse, json, statistics, subprocess, sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
W, H, K = 96, 54, 8
LIM_CORTE, LIM_GRAD = 14.0, 16.0
AREA_CENA = 0.25   # troca de cena = pelo menos 25% da tela muda muito (critério nosso)   # níveis de cinza (0–255); calibrados no nosso vídeo (critério nosso)


def fps_de(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=avg_frame_rate", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True).stdout.strip()
    a, b = (r.split("/") + ["1"])[:2]
    return float(a) / float(b or 1)


def quadros(video, ini=0, fim=None):
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", str(ini)] + (["-to", str(fim)] if fim else []) + ["-i", str(video), "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"]
    b = subprocess.run(cmd, capture_output=True).stdout
    f = np.frombuffer(b, dtype=np.uint8)
    return f[: len(f) // (W * H) * W * H].reshape(-1, H, W).astype(np.float32)


def analisar(video, ini=0, fim=None):
    fps = fps_de(video)
    F = quadros(video, ini, fim)
    n = len(F)
    L = F.mean(axis=(1, 2))
    dif = np.abs(np.diff(F, axis=0))
    d1 = np.zeros(n); d1[1:] = dif.mean(axis=(1, 2))
    area = np.zeros(n); area[1:] = (dif > 30).mean(axis=(1, 2))   # fração da tela que mudou muito
    lisura = F.std(axis=(1, 2))                                     # quadro de uma cor só = desvio baixo
    del dif
    dK = np.zeros(n); dK[K:] = np.abs(F[K:] - F[:-K]).mean(axis=(1, 2))
    trans = []
    # 1) cortes secos
    for t in range(1, n - 1):
        loc = np.median(d1[max(1, t - 15): t + 15]) + 1e-6
        if d1[t] >= LIM_CORTE and d1[t] >= 3 * loc and d1[t - 1] < 0.4 * d1[t] and d1[t + 1] < 0.4 * d1[t]:
            tipo = "corte seco" if area[t] >= AREA_CENA else "elemento entrou (mesma cena)"
            trans.append({"q_ini": t, "q_fim": t, "tipo": tipo, "quadros": 1, "forca": round(float(d1[t]), 1), "area": round(float(area[t]), 2)})
    secos = {x["q_ini"] for x in trans if x["tipo"] == "corte seco"}
    # 2) graduais
    alto = dK >= LIM_GRAD
    t = 0
    while t < n:
        if alto[t]:
            a = t
            while t < n and alto[t]:
                t += 1
            b = t - 1
            q0, q1 = max(0, a - K), b          # dK[t] compara t com t-K: a transição começa ~K quadros antes
            if any(q0 <= s <= q1 for s in secos) and (q1 - q0) <= K + 2:
                continue                       # é só o rastro de um corte seco
            if any(q0 <= s <= q1 for s in secos):
                q0 = max(q0, max(s for s in secos if q0 <= s <= q1) + 1)
            # junta com a transição gradual anterior se encostam (mesmo evento medido duas vezes)
            if trans and trans[-1].get("gradual") and q0 - trans[-1]["q_fim"] <= K:
                q0 = trans.pop()["q_ini"]
            fa, fb = F[q0], F[q1]
            pontas = float(np.abs(fa - fb).mean())
            area_p = float((np.abs(fa - fb) > 30).mean())
            seg = L[q0: q1 + 1]
            mliso = int(q0 + np.argmin(lisura[q0: q1 + 1]))
            if lisura[mliso] < 10 and lisura[mliso] < 0.5 * min(lisura[q0], lisura[q1]) and 18 <= L[mliso] <= 235:
                tipo = f"fade para cor lisa (dip, luz {int(L[mliso])})"
            elif seg.min() < 18 and seg.min() < min(L[q0], L[q1]) - 25:
                tipo = "fade para preto"
            elif seg.max() > 235 and seg.max() > max(L[q0], L[q1]) + 25:
                tipo = "fade para branco"
            else:
                m = (q0 + q1) // 2
                x, y = (fa - fb).ravel(), (F[m] - fb).ravel()
                al = float(np.clip(np.dot(x, y) / (np.dot(x, x) + 1e-6), 0, 1))
                resto = np.abs(F[m] - (al * fa + (1 - al) * fb)).mean()
                so_uma = min(np.abs(F[m] - fa).mean(), np.abs(F[m] - fb).mean()) + 1e-6
                if area_p < AREA_CENA:
                    tipo = "movimento de câmera (mesma cena)"
                elif pontas >= LIM_GRAD and resto < 0.35 * so_uma:
                    tipo = "fusão"
                elif pontas >= LIM_GRAD:
                    tipo = "transição em movimento"
                else:
                    tipo = "movimento de câmera (mesma cena)"
            trans.append({"q_ini": int(q0), "q_fim": int(q1), "tipo": tipo, "quadros": int(q1 - q0 + 1), "forca": round(pontas, 1), "area": round(area_p, 2), "gradual": True})
        else:
            t += 1
    trans.sort(key=lambda x: x["q_ini"])
    trocas = [x for x in trans if "mesma cena" not in x["tipo"]]
    # cenas
    cortes_q = [ (x["q_ini"] + x["q_fim"]) / 2 for x in trocas]
    bordas = [0] + cortes_q + [n]
    cenas = []
    for i in range(len(bordas) - 1):
        a, b = bordas[i], bordas[i + 1]
        tr = trocas[i - 1] if i > 0 else None
        cenas.append({"n": i + 1, "ini": round(ini + a / fps, 3), "fim": round(ini + b / fps, 3), "dur": round((b - a) / fps, 3),
                      "quadros": int(round(b - a)), "entrada": tr["tipo"] if tr else "início",
                      "entrada_quadros": tr["quadros"] if tr else 0})
    durs = [c["dur"] for c in cenas]
    tot = n / fps
    q = np.percentile(durs, [10, 25, 50, 75, 90]) if durs else [0] * 5
    hist_lim = [0, 1, 2, 3, 4, 5, 7, 10, 15, 30, 1e9]
    hist = {f"{hist_lim[i]}–{hist_lim[i+1] if hist_lim[i+1] < 1e9 else '+'} s": int(sum(hist_lim[i] <= d < hist_lim[i + 1] for d in durs)) for i in range(len(hist_lim) - 1)}
    meios = np.array([(c["ini"] + c["fim"]) / 2 for c in cenas]); dd = np.array(durs)
    incl = float(np.polyfit(meios / 60, dd, 1)[0]) if len(cenas) > 2 else 0.0
    curva = [int(sum(1 for x in trocas if k * 30 <= (x["q_ini"] / fps) < (k + 1) * 30)) for k in range(int(np.ceil(tot / 30)))]
    tipos = {}
    for x in trocas:
        tipos[x["tipo"]] = tipos.get(x["tipo"], 0) + 1
    return {
        "video": str(video), "fps": round(fps, 3), "inicio": ini, "duracao": round(tot, 2), "cenas_total": len(cenas),
        "trocas_por_min": round(len(trocas) / (tot / 60), 2),
        "duracao_cena": {"media": round(statistics.mean(durs), 2), "mediana": round(float(q[2]), 2),
                         "desvio": round(statistics.pstdev(durs), 2), "cv": round(statistics.pstdev(durs) / statistics.mean(durs), 2),
                         "p10": round(float(q[0]), 2), "p25": round(float(q[1]), 2), "p75": round(float(q[3]), 2), "p90": round(float(q[4]), 2),
                         "min": round(min(durs), 2), "max": round(max(durs), 2)},
        "histograma": hist,
        "transicoes": {k: {"n": v, "fracao": round(v / max(1, len(trocas)), 3),
                           "quadros_medio": round(statistics.mean([x["quadros"] for x in trocas if x["tipo"] == k]), 1)} for k, v in sorted(tipos.items(), key=lambda z: -z[1])},
        "movimentos_de_camera": sum(1 for x in trans if x["tipo"] == "movimento de câmera (mesma cena)"),
        "elementos_entrando": sum(1 for x in trans if x["tipo"] == "elemento entrou (mesma cena)"),
        "tendencia_seg_por_min": round(incl, 3),
        "curva_trocas_por_30s": curva,
        "cenas": cenas,
        "transicoes_lista": [{**x, "t": round(ini + x["q_ini"] / fps, 3)} for x in trocas],
    }


def relatorio(r):
    d = r["duracao_cena"]
    L = [f"# Ritmo cena por cena: {Path(r['video']).name}", "",
         f"- {r['duracao']} s · {r['fps']} quadros/s · **{r['cenas_total']} cenas** · **{r['trocas_por_min']} trocas/min**",
         f"- Duração da cena: média **{d['media']} s** · mediana **{d['mediana']} s** · desvio {d['desvio']} s (variação {int(d['cv']*100)}%)",
         f"- Faixa: 10% das cenas < {d['p10']} s · metade entre {d['p25']} e {d['p75']} s · 10% > {d['p90']} s · menor {d['min']} s · maior {d['max']} s",
         f"- Tendência: a cena {'encurta' if r['tendencia_seg_por_min'] < 0 else 'alonga'} {abs(r['tendencia_seg_por_min'])} s a cada minuto de vídeo",
         f"- Dentro da mesma cena (não contam como troca): {r['movimentos_de_camera']} movimentos de câmera · {r['elementos_entrando']} elementos entrando de uma vez", "",
         "## Transições", "", "| tipo | quantas | % | duração média |", "|---|---|---|---|"]
    L += [f"| {k} | {v['n']} | {int(v['fracao']*100)}% | {v['quadros_medio']} quadros ({v['quadros_medio']/r['fps']:.2f} s) |" for k, v in r["transicoes"].items()]
    L += ["", "## Histograma da duração das cenas", "", "| faixa | cenas |", "|---|---|"] + [f"| {k} | {v} |" for k, v in r["histograma"].items()]
    L += ["", "## Ritmo ao longo do vídeo (trocas a cada 30 s)", "", " ".join(f"{i*30//60}:{i*30%60:02d}={c}" for i, c in enumerate(r["curva_trocas_por_30s"])), "",
          "## Todas as cenas", "", "| # | início | fim | duração | quadros | entrou por |", "|---|---|---|---|---|---|"]
    def mm(s): return f"{int(s//60)}:{s%60:05.2f}"
    L += [f"| {c['n']} | {mm(c['ini'])} | {mm(c['fim'])} | {c['dur']} s | {c['quadros']} | {c['entrada']}{f' ({c[chr(101)+'ntrada_quadros']} q)' if c['entrada_quadros'] > 1 else ''} |" for c in r["cenas"]]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--saida"); ap.add_argument("--inicio", type=float, default=0); ap.add_argument("--fim", type=float)
    a = ap.parse_args()
    r = analisar(a.video, a.inicio, a.fim)
    pasta = Path(a.saida) if a.saida else Path(a.video).with_suffix("")
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "ritmo.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    (pasta / "RITMO.md").write_text(relatorio(r), encoding="utf-8")
    d = r["duracao_cena"]
    print(f"{r['cenas_total']} cenas · {r['trocas_por_min']} trocas/min · média {d['media']} s · mediana {d['mediana']} s · {dict((k, v['n']) for k, v in r['transicoes'].items())}")
    print(f"pronto: {pasta / 'RITMO.md'}")
