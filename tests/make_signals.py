"""Señales de prueba (48 kHz, float32)."""
import numpy as np, soundfile as sf, pathlib
from scipy import signal as sg
D = pathlib.Path(__file__).parent / "signals"; D.mkdir(exist_ok=True)
SR = 48000
def a(db): return 10 ** (db / 20)
def save(name, *ch): sf.write(D / name, np.stack(ch, 1).astype(np.float32), SR, subtype="FLOAT")
n = SR * 2; t = np.arange(n) / SR
s = lambda f, db, tt=t: a(db) * np.sin(2 * np.pi * f * tt)
save("sine1k_m6.wav", s(1000, -6), s(1000, -6))
save("sine1k_m50.wav", s(1000, -50), s(1000, -50))
save("sine50_m20.wav", s(50, -20), s(50, -20))
save("lr.wav", s(1000, -6), s(1000, -50))
# escalon: -60 dBFS 0-1 s, -10 dBFS 1-2 s, -60 dBFS 2-3 s
t3 = np.arange(SR * 3) / SR
lv = np.where((t3 >= 1) & (t3 < 2), a(-10), a(-60))
st = lv * np.sin(2 * np.pi * 1000 * t3); save("step.wav", st, st)
# el mismo escalón en 60 Hz (presets de kick / 808) y en 8 kHz (hi-hat)
st = lv * np.sin(2 * np.pi * 60 * t3); save("step_low.wav", st, st)
st = lv * np.sin(2 * np.pi * 8000 * t3); save("step_high.wav", st, st)
# rampa lenta: 1 kHz de -20 a -60 dB en 0-4 s y de vuelta a -20 en 4-8 s (10 dB/s)
t8 = np.arange(SR * 8) / SR
ld = np.where(t8 < 4, -20 - 10 * t8, -60 + 10 * (t8 - 4))
r = a(ld) * np.sin(2 * np.pi * 1000 * t8); save("ramp.wav", r, r)
# rafaga para el lookahead: silencio y 1 kHz a -6 dBFS desde 1.0 s (empieza en el pico)
b = np.zeros(n); i0 = SR; b[i0:] = a(-6) * np.cos(2 * np.pi * 1000 * (t[i0:] - 1.0)); save("burst.wav", b, b)
# sidechain: 1 kHz -10 dBFS en 1/2 siempre; ruido 300 Hz-4 kHz en 3/4 de 0.2 a 1.0 s
nz = np.random.default_rng(1).standard_normal(n); nz = sg.sosfilt(sg.butter(4, [300, 4000], "band", fs=SR, output="sos"), nz)
nz = 0.3 * nz / np.abs(nz).max(); nz[: int(0.2 * SR)] = 0; nz[int(1.0 * SR):] = 0
save("sidechain4.wav", s(1000, -10), s(1000, -10), nz, nz)
# golpes: 6 golpes cada 0.5 s desde 0.25 s; 200 Hz con caida de 150 ms (la cola queda sobre -40 dB hasta el siguiente)
d = np.zeros(SR * 3)
for k in range(6):
    i = int((0.25 + 0.5 * k) * SR); m = len(d) - i; tt = np.arange(m) / SR
    d[i:] += a(-6) * np.sin(2 * np.pi * 200 * tt) * np.exp(-tt / 0.15)
save("drums.wav", d, d)
# 3 s de 1 kHz a -6 (para las notas MIDI de entrada)
x = a(-6) * np.sin(2 * np.pi * 1000 * t3); save("sine1k_m6_3s.wav", x, x)
print("ok", sorted(p.name for p in D.iterdir()))
