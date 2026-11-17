"""Pruebas de la interfaz con el mouse. Requiere la demo abierta (tests/reopen.sh, preset 3) y la ventana del FX al frente.
OJO: mueve el mouse de verdad; no correr mientras otra sesión o persona está usando REAPER."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from ui import *
fails = 0
def check(name, got, want):
    global fails
    ok = (want(got) if callable(want) else got == want); fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:44s} {got!r}")

subprocess.run(["osascript", "-e", 'tell application "REAPER" to activate']); time.sleep(0.6)
cc(f"c:{pt(500, 5)}")    # clic neutro: la ventana del FX puede necesitar un clic para activarse
check("arranca con preset 3 (umbral -38)", num(param(1)), -38.0)
cc(f"c:{pt(*MODE(1))}"); check("clic en Expansor", param(7), "Expansor")
cc(f"c:{pt(*MODE(2))}"); check("clic en Ducker", param(7), "Ducker")
cc(f"c:{pt(*MODE(0))}"); check("clic en Gate", param(7), "Gate")
cc(f"c:{pt(*TRANS)}"); check("clic en Transitorio", param(10), "Transitorio")
cc(f"c:{pt(*NIVEL)}"); check("clic en Nivel", param(10), "Nivel")
t0 = num(param(1)); x, y = KNOB(0); drag(x, y, x, y - 40)
check("arrastrar Umbral hacia arriba sube", num(param(1)), lambda v: v > t0 + 1)
cc(f"dc:{pt(x, y)}"); check("doble clic en Umbral = -40", num(param(1)), -40.0)
drag(GRAPH_X, 200, GRAPH_X, 140)
check("arrastrar 60 px arriba en la grafica: +15.7 dB", num(param(1)), lambda v: -26 < v < -22)
t1 = num(param(1)); drag(CURVE[0], CURVE[1], CURVE[0] - 40, CURVE[1])
check("curva: arrastrar a la izquierda baja el umbral", num(param(1)), lambda v: t1 - 12 < v < t1 - 8)
r0 = num(param(3)); drag(CURVE[0], CURVE[1], CURVE[0], CURVE[1] + 30)
check("curva: arrastrar hacia abajo sube el rango", num(param(3)), lambda v: v > r0 + 5)
x, y = KNOB(5); cc(f"m:{pt(x, y)}"); r0 = num(param(6)); wheel(5)
check("rueda sobre Release cambia", num(param(6)), lambda v: v != r0)
x, y = KNOB(1); cc(f"dc:{pt(x, y)}"); check("doble clic en Histeresis = 4", num(param(2)), 4.0)
cc(f"c:{pt(*ESC_SC)}"); check("escuchar SC", param(19), "Encendido")
cc(f"c:{pt(*CAMBIOS)}"); check("escuchar cambios", param(20), lambda v: v.startswith("Solo"))
check("escuchar cambios apaga escuchar SC", param(19), "Apagado")
cc(f"c:{pt(*CAMBIOS)}"); check("escuchar cambios apagado", param(20), "Normal")
print("FALLAS:", fails)
sys.exit(1 if fails else 0)
