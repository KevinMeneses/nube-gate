"""Compara los renders de tests/out con lo que dice la teoría. Sale con código 1 si algo falla."""
import numpy as np, soundfile as sf, pathlib, sys
D = pathlib.Path(__file__).parent / "out"; S = pathlib.Path(__file__).parent / "signals"; SR = 48000
def a(db): return 10 ** (db / 20)
def db(x): return 20 * np.log10(np.abs(x) + 1e-15)
def load(name):
    x, sr = sf.read(D / f"{name}.wav"); assert sr == SR; return x
def sig(name): return sf.read(S / name)[0]
def lvl(name, t0=1.0, t1=1.9, ch=0):
    """nivel de pico de un seno (dBFS) a partir del RMS"""
    x = load(name)[int(t0 * SR):int(t1 * SR), ch]; return db(np.sqrt(np.mean(x ** 2)) * np.sqrt(2))
def env(x, ms=1.0):
    n = int(SR * ms / 1000); m = len(x) // n; return np.abs(x[:m * n]).reshape(m, n).max(1)
def gain(name, src, ms=1.0):
    """ganancia (dB) por ventana de ms = salida / entrada"""
    i = env(sig(src)[:, 0], ms); o = env(load(name)[:, 0], ms); k = min(len(i), len(o))
    return db(o[:k] / np.maximum(i[:k], 1e-12))

fails = 0
def scalar(name, got, want, tol):
    global fails
    ok = abs(got - want) <= tol
    fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:34s} {got:+8.2f}   (esperado {want:+.2f} ± {tol})")
def inrange(name, got, lo, hi):
    global fails
    ok = lo <= got <= hi
    fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:34s} {got:+8.2f}   (entre {lo:+.2f} y {hi:+.2f})")
def exp_gr(L, T, R, W):
    o = T - L; s = R - 1
    return 0 if 2 * o <= -W else s * (o + W / 2) ** 2 / (2 * W) if (W > 0 and 2 * o < W) else s * o

# NaN / explosiones en todo
for p in sorted(D.glob("*.wav")):
    if p.stem.startswith("perf_"): continue
    x = load(p.stem)
    if not np.all(np.isfinite(x)) or np.abs(x).max() > 4:
        fails += 1; print("MAL", p.stem, "tiene NaN o pasa de +12 dBFS")

# curva estática
x = load("open_null"); ref = sig("sine1k_m6.wav")
scalar("abierta = intacta (dB de diferencia)", db(np.abs(x - ref)[4800:-4800].max()), -150, 30)
scalar("cerrada, rango 40", lvl("closed_r40"), -90, 0.1)
scalar("cerrada, rango 15", lvl("closed_r15"), -65, 0.1)
scalar("cerrada, rango inf (pico)", db(np.abs(load("closed_inf")[4800:-4800]).max()), -300, 150)
scalar("expansor 1:2 (-50 bajo -40)", lvl("exp_r2"), -50 - exp_gr(-50, -40, 2, 0), 0.1)
scalar("expansor 1:4 con rango 12", lvl("exp_range"), -62, 0.1)
scalar("expansor rodilla 8", lvl("exp_knee"), -50 - exp_gr(-50, -48, 2, 8), 0.15)
scalar("expansor sobre el umbral = intacto", lvl("exp_above"), -6, 0.02)
scalar("ducker con señal: -10", lvl("duck_on"), -16, 0.1)
scalar("ducker sin señal: intacto", lvl("duck_off"), -50, 0.05)

# histéresis: rampa de 10 dB/s (baja 0-4 s, sube 4-8 s)
for name, close in (("hyst6", -46), ("hyst0", -40)):
    g = gain(name, "ramp.wav")
    tc = np.argmax((np.arange(len(g)) > 100) & (g < -20)) / 1000
    to = np.argmax((np.arange(len(g)) > 4000) & (g > -20)) / 1000
    scalar(f"{name}: cierra en (dB de entrada)", -20 - 10 * tc, close, 0.6)
    scalar(f"{name}: abre en (dB de entrada)", -60 + 10 * (to - 4), -40, 0.6)
    if name == "hyst6":
        ch = np.sum(np.abs(np.diff((g[100:7900] > -20).astype(int))))
        scalar("hyst6: cambios abierta/cerrada", ch, 2, 0)
g = gain("lf_chatter", "sine50_m20.wav", 20)
inrange("50 Hz cerca del umbral: no tiembla", g[10:95].min(), -0.3, 0.1)

# tiempos (escalón -60 → -10 en 1 s, → -60 en 2 s; umbral -40, histéresis 4, rango 40)
g = gain("attack10", "step.wav")
print("    ataque 10 ms: " + " ".join(f"{t}ms:{g[1000 + t]:.1f}" for t in (0, 2, 4, 6, 8, 10, 12)))
inrange("ataque 10 ms: a los 4-5 ms", g[1004], -40 + 4 * 4.75 - 3, -40 + 4 * 4.75 + 3)
inrange("ataque 10 ms: abierta a los 12 ms", g[1012], -0.3, 0.1)
# el detector (máximo de los últimos 12-24 ms) suelta entre 12 y 24 ms después del escalón
g = gain("release100", "step.wav")
tc = 2000 + np.argmax(g[2000:] < -0.3)
print(f"    release 100 ms (empieza a cerrar a los {tc - 2000} ms): " + " ".join(f"{t}ms:{g[2000 + t]:.1f}" for t in (10, 20, 40, 75, 100, 125, 150)))
inrange("release: empieza a cerrar (ms)", tc - 2000, 12, 25)
scalar("release: mitad (-20) a +50 ms", g[tc + 50], -20, 1.5)
scalar("release: cerrada a +105 ms", g[tc + 105], -40, 0.5)
g = gain("hold200", "step.wav")
inrange("hold 200: abierta a los 150 ms", g[2150], -0.5, 0.1)
scalar("hold 200: suelta 200 ms después (ms)", 2000 + np.argmax(g[2000:] < -0.3) - tc, 200, 1)
tcl = tc - 2000

# lookahead
for name in ("la_off", "la_5"):
    x = load(name)[:, 0]
    on = np.argmax(np.abs(x) > 1e-4)
    print(f"    {name}: arranca en la muestra {on} (debe ser ~48000)")
    if abs(on - 48000) > 3: fails += 1; print("MAL", name, "desalineado: la latencia no se compensó")
inrange("sin lookahead: pico 1er ms (ataque 5)", db(np.abs(load("la_off")[48000:48048, 0]).max()), -45, -25)
scalar("lookahead 5 ms: 1er ms intacto", db(np.abs(load("la_5")[48000:48048, 0]).max()), -6, 0.3)

# sidechain y filtros
scalar("SC externo: con ruido abre", lvl("ext_sc", 0.3, 0.95), -10, 0.1)
scalar("SC externo: sin ruido cierra", lvl("ext_sc", 1.3, 1.9), -50, 0.1)
scalar("50 Hz sin filtro SC: abre", lvl("sc_nohp"), -20, 0.1)
scalar("50 Hz con corte grave 300: cierra", lvl("sc_hp300"), -60, 0.1)
scalar("1 kHz con corte agudo 250: cierra", lvl("sc_lp250"), -46, 0.1)
w = 50 / 300; scalar("escuchar SC (corte grave 300)", lvl("sclisten"), -20 + db(w ** 2 / np.sqrt(1 + w ** 4)), 0.3)
scalar("escuchar cambios (cerrada)", lvl("delta"), -50 + db(1 - a(-40)), 0.05)
scalar("mezcla 50 % (cerrada)", lvl("mix50"), -50 + db(0.5 * (1 + a(-40))), 0.05)
scalar("ganancia +6", lvl("gain6"), -44, 0.05)
scalar("enlace 100 %: R sigue a L", lvl("link100", ch=1), -50, 0.05)
scalar("enlace 100 %: L", lvl("link100", ch=0), -6, 0.05)
scalar("enlace 0 %: R se cierra solo", lvl("link0", ch=1), -90, 0.1)
scalar("enlace 0 %: L", lvl("link0", ch=0), -6, 0.05)
scalar("solo Mid (mono, cerrada)", lvl("solo_mid"), -90, 0.1)
scalar("solo Side (mono) intacto", lvl("solo_side"), -50, 0.05)
scalar("RMS: -50 con umbral -51 abre", lvl("rms_open"), -50, 0.1)
scalar("RMS: -50 con umbral -49 cierra", lvl("rms_closed"), -90, 0.1)

# transitorios: 6 golpes en 0.25 + 0.5 k; la cola queda sobre el umbral
ons = [int((0.25 + 0.5 * k) * 1000) for k in range(6)]
g = gain("tr_level", "drums.wav")
inrange("nivel: la cola no se corta (+300 ms)", min(g[o + 300] for o in ons[1:-1]), -1, 0.1)
g = gain("tr_trans", "drums.wav")
inrange("transitorio: golpe intacto (+20 ms)", min(g[o + 20] for o in ons), -1, 0.1)
scalar("transitorio: cola baja 12 (+200 ms)", np.mean([g[o + 200] for o in ons]), -12, 0.5)

# MIDI de salida (la sonda pone L = velocidad/127 y R = ±nota/127)
x = load("midi_out"); on = np.flatnonzero(x[:, 0] > 0); off = np.flatnonzero(x[:, 1] < 0)
scalar("MIDI: notas encendidas", len(on), 6, 0)
scalar("MIDI: notas apagadas", len(off), 6, 0)
if len(on) == 6:
    err = max(abs(on[k] - (0.25 + 0.5 * k) * SR) for k in range(6)) / SR * 1000
    inrange("MIDI: desfase máx. con lookahead 3 (ms)", err, 0, 1)
    scalar("MIDI: velocidad (pico -6 dB)", np.mean(x[on, 0]) * 127, 127 - 6 * 127 / 60, 2)
    scalar("MIDI: número de nota", np.mean(x[on, 1]) * 127, 36, 0.01)
    scalar("MIDI: nota apagada tras el hold (ms)", np.mean((off - on) / SR * 1000), 40, 3)
x = load("midi_out_lvl"); on = np.flatnonzero(x[:, 0] > 0); off = np.flatnonzero(x[:, 1] < 0)
scalar("MIDI por nivel: 1 nota", len(on), 1, 0)
if len(on) == 1:
    scalar("MIDI por nivel: llega 2 ms tarde (ms)", (on[0] - SR) / SR * 1000, 2, 0.3)
    scalar("MIDI por nivel: velocidad (-10 dB)", x[on[0], 0] * 127, round(127 - 10 * 127 / 60), 1)
    scalar("MIDI por nivel: nota 38", x[on[0], 1] * 127, 38, 0.01)
    inrange("MIDI por nivel: nota apagada al cerrar (ms)", (off[0] / SR - 2) * 1000 if len(off) else 0, 12, 25)
# MIDI de entrada: notas en 0.5-0.8 s y 1.5-1.6 s
scalar("MIDI entrada: nota 1 abre", lvl("midi_in", 0.55, 0.75), -6, 0.1)
scalar("MIDI entrada: entre notas cerrada", lvl("midi_in", 1.0, 1.4), -46, 0.1)
scalar("MIDI entrada: nota 2 abre", lvl("midi_in", 1.52, 1.58), -6, 0.1)
scalar("MIDI entrada: después cerrada", lvl("midi_in", 2.0, 2.9), -46, 0.1)

# presets
for p in range(1, 16):
    if p == 11:
        inrange("preset 11 (ducker): baja con SC", -10 - lvl("preset11", 0.4, 0.95), 5, 7)
        scalar("preset 11: vuelve sin SC", lvl("preset11", 1.5, 1.9), -10, 0.2)
    elif p == 12:
        scalar("preset 12 (gate SC): abre con SC", lvl("preset12", 0.4, 0.95), -10, 0.2)
        scalar("preset 12: cierra sin SC", lvl("preset12", 1.5, 1.9), -50, 0.2)
    else:
        loud = lvl(f"preset{p}", 1.5, 1.9); quiet = lvl(f"preset{p}", 2.5, 2.9)
        if p == 8: scalar("preset 8 (transitorio): sostenido baja 12", loud, -22, 0.5)
        else: scalar(f"preset {p}: parte fuerte pasa", loud, -10, 0.3)
        if p == 14: scalar("preset 14 (solo MIDI): intacto", quiet, -60, 0.1)
        else: inrange(f"preset {p}: parte baja se baja", quiet, -400, -66)

# voz real (si está la grabación): las frases pasan intactas y el ruido entre frases baja ~15 dB
V = pathlib.Path.home() / "Music/ClaudeBeats/Media/voz_sola_seca.wav"
if V.exists() and (D / "voz_real.wav").exists():
    xi = sf.read(V)[0]; xo = load("voz_real"); xi = xi if xi.ndim == 1 else xi[:, 0]; xo = xo[:len(xi), 0]
    n = int(0.02 * SR); m = len(xo) // n
    ri = db(np.sqrt(np.mean(xi[:m * n].reshape(m, n) ** 2, 1))); ro = db(np.sqrt(np.mean(xo[:m * n].reshape(m, n) ** 2, 1)))
    print(f"    voz real: {np.sum(ri > -30)} ventanas de voz, {np.sum((ri < -50) & (ri > -120))} de ruido")
    inrange("voz real: frases intactas (mediana dB)", np.median((ro - ri)[ri > -30]), -0.3, 0.1)
    inrange("voz real: ruido entre frases baja (dB)", np.median((ro - ri)[(ri < -50) & (ri > -120)]), -16, -12)
print("\nFALLAS:", fails)
sys.exit(1 if fails else 0)
