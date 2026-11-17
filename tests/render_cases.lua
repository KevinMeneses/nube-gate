-- Carga Nube Gate en una pestaña nueva, renderiza cada caso y cierra la pestaña.
-- Uso: REAPER -nonewinst tests/render_cases.lua   (escribe tests/out/*.wav y tests/out/log.txt)
local ROOT = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$")
local OUT = ROOT .. "/out"
os.execute('mkdir -p "' .. OUT .. '"')
local logf = io.open(OUT .. "/log.txt", "w")
local function log(...) local t = {} for _, v in ipairs({...}) do t[#t+1] = tostring(v) end logf:write(table.concat(t, " "), "\n") logf:flush() end

-- slider N (1..25) = parámetro N-1. Los sliders con forma :log=mid van normalizados 0..1
local LOGP = {[4] = {0.01, 100, 2}, [6] = {1, 3000, 150}, [8] = {1, 20, 4}, [17] = {20, 2000, 150}, [18] = {500, 20000, 4000}}
local function to_norm(s, v)
  local mn, mx, mid = table.unpack(LOGP[s])
  local sr = (mx - mn) / (mid - mn) - 1; local r = sr * sr
  return math.log((v - mn) / (mx - mn) * (r - 1) + 1) / math.log(r)
end
-- base: Gate, ataque 0.01 ms, hold 0, release 1 ms, histéresis 4, rango 40
local function P(t)
  local r = {[7] = 0, [4] = 0.01, [5] = 0, [6] = 1, [2] = 4, [3] = 40}
  for k, v in pairs(t) do r[k] = v end
  return r
end

local CASES = {
  {"open_null",   "sine1k_m6.wav",  P{[1] = -40}},
  {"closed_r40",  "sine1k_m50.wav", P{[1] = -40}},
  {"closed_r15",  "sine1k_m50.wav", P{[1] = -40, [3] = 15}},
  {"closed_inf",  "sine1k_m50.wav", P{[1] = -40, [3] = 80}},
  {"exp_r2",      "sine1k_m50.wav", P{[7] = 1, [1] = -40, [8] = 2, [9] = 0}},
  {"exp_range",   "sine1k_m50.wav", P{[7] = 1, [1] = -40, [8] = 4, [9] = 0, [3] = 12}},
  {"exp_knee",    "sine1k_m50.wav", P{[7] = 1, [1] = -48, [8] = 2, [9] = 8}},
  {"exp_above",   "sine1k_m6.wav",  P{[7] = 1, [1] = -40, [8] = 4, [9] = 6}},
  {"duck_on",     "sine1k_m6.wav",  P{[7] = 2, [1] = -40, [3] = 10}},
  {"duck_off",    "sine1k_m50.wav", P{[7] = 2, [1] = -40, [3] = 10}},
  {"hyst6",       "ramp.wav",       P{[1] = -40, [2] = 6}},
  {"hyst0",       "ramp.wav",       P{[1] = -40, [2] = 0}},
  {"lf_chatter",  "sine50_m20.wav", P{[1] = -22, [2] = 0}},
  {"attack10",    "step.wav",       P{[1] = -40, [4] = 10}},
  {"release100",  "step.wav",       P{[1] = -40, [6] = 100}},
  {"hold200",     "step.wav",       P{[1] = -40, [6] = 100, [5] = 200}},
  {"la_off",      "burst.wav",      P{[1] = -40, [4] = 5}},
  {"la_5",        "burst.wav",      P{[1] = -40, [4] = 5, [12] = 5}},
  {"ext_sc",      "sidechain4.wav", P{[1] = -30, [16] = 1}, 4},
  {"sc_nohp",     "sine50_m20.wav", P{[1] = -26}},
  {"sc_hp300",    "sine50_m20.wav", P{[1] = -26, [17] = 300}},
  {"sc_lp250",    "sine1k_m6.wav",  P{[1] = -20, [18] = 250}},
  {"sclisten",    "sine50_m20.wav", P{[1] = -26, [17] = 300, [19] = 1}},
  {"delta",       "sine1k_m50.wav", P{[1] = -40, [20] = 1}},
  {"mix50",       "sine1k_m50.wav", P{[1] = -40, [21] = 50}},
  {"gain6",       "sine1k_m50.wav", P{[1] = -60, [22] = 6}},
  {"link100",     "lr.wav",         P{[1] = -40}},
  {"link0",       "lr.wav",         P{[1] = -40, [14] = 0}},
  {"solo_mid",    "sine1k_m50.wav", P{[1] = -40, [15] = 2}},
  {"solo_side",   "sine1k_m50.wav", P{[1] = -40, [15] = 3}},
  {"rms_open",    "sine1k_m50.wav", P{[1] = -51, [2] = 0, [13] = 1}},
  {"rms_closed",  "sine1k_m50.wav", P{[1] = -49, [2] = 0, [13] = 1}},
  {"tr_level",    "drums.wav",      P{[1] = -40, [5] = 40, [6] = 60, [3] = 12}},
  {"tr_trans",    "drums.wav",      P{[1] = -40, [5] = 40, [6] = 60, [3] = 12, [10] = 1, [11] = 6}},
  {"midi_out",    "drums.wav",      P{[1] = -40, [5] = 40, [6] = 60, [3] = 0, [10] = 1, [12] = 3, [23] = 1, [24] = 36}, 2, "probe"},
  {"midi_out_lvl", "step.wav",      P{[1] = -40, [5] = 0, [3] = 0, [23] = 1, [24] = 38}, 2, "probe"},
  {"midi_in",     "sine1k_m6_3s.wav", P{[1] = -40, [23] = 2}, 2, "midi_in"},
}
for p = 1, 15 do
  local ext = p == 11 or p == 12
  local src = ext and "sidechain4.wav" or (p == 4 or p == 9) and "step_low.wav" or p == 7 and "step_high.wav" or "step.wav"
  CASES[#CASES + 1] = {"preset" .. p, src, {[25] = p}, ext and 4 or 2}
end

-- voz real (grabación propia, no está en el repo): preset 1 sobre la voz seca de Nube baja
local VOZ = os.getenv("HOME") .. "/Music/ClaudeBeats/Media/voz_sola_seca.wav"
if reaper.file_exists(VOZ) then CASES[#CASES + 1] = {"voz_real", VOZ, {[25] = 1}} end

reaper.Main_OnCommand(40859, 0) -- nueva pestaña
reaper.GetSetProjectInfo(0, "PROJECT_SRATE", 48000, true)
reaper.GetSetProjectInfo(0, "PROJECT_SRATE_USE", 1, true)
reaper.InsertTrackAtIndex(0, false); local tr = reaper.GetTrack(0, 0)
local item = reaper.AddMediaItemToTrack(tr)
local take = reaper.AddTakeToMediaItem(item)
reaper.SetMediaItemInfo_Value(item, "D_POSITION", 0)
local only = os.getenv("NUBE_CASE")
local mtr = nil

for _, c in ipairs(CASES) do
  local name, src, params, extra = c[1], c[2], c[3], c[5]
  if not only or name:find(only) then
    reaper.SetMediaTrackInfo_Value(tr, "I_NCHAN", c[4] or 2)
    local s = reaper.PCM_Source_CreateFromFile(src:sub(1, 1) == "/" and src or ROOT .. "/signals/" .. src)
    reaper.SetMediaItemTake_Source(take, s)
    reaper.SetMediaItemInfo_Value(item, "D_LENGTH", (reaper.GetMediaSourceLength(s)))
    reaper.UpdateItemInProject(item)
    while reaper.TrackFX_GetCount(tr) > 0 do reaper.TrackFX_Delete(tr, 0) end
    if mtr then reaper.DeleteTrack(mtr); mtr = nil end
    local fx = reaper.TrackFX_AddByName(tr, "JS:Nube Gate/nube_gate.jsfx", false, -1)
    if fx < 0 then log("ERROR no cargó el FX") break end
    if params[25] then reaper.TrackFX_SetParam(tr, fx, 24, params[25]) end
    for s_, v in pairs(params) do
      if s_ ~= 25 then
        if LOGP[s_] then reaper.TrackFX_SetParamNormalized(tr, fx, s_ - 1, to_norm(s_, v))
        else reaper.TrackFX_SetParam(tr, fx, s_ - 1, v) end
      end
    end
    if extra == "probe" then
      if reaper.TrackFX_AddByName(tr, "JS:Nube Gate/_prueba_midi.jsfx", false, -1) < 0 then log("ERROR no cargó la sonda MIDI") end
    elseif extra == "midi_in" then
      -- pista MIDI que manda solo MIDI a la del gate: notas 0.5-0.8 s y 1.5-1.6 s
      reaper.InsertTrackAtIndex(1, false); mtr = reaper.GetTrack(0, 1)
      local mi = reaper.CreateNewMIDIItemInProj(mtr, 0, 3, false)
      local mt = reaper.GetActiveTake(mi)
      for _, nt in ipairs({{0.5, 0.8}, {1.5, 1.6}}) do
        local p0 = reaper.MIDI_GetPPQPosFromProjTime(mt, nt[1]); local p1 = reaper.MIDI_GetPPQPosFromProjTime(mt, nt[2])
        reaper.MIDI_InsertNote(mt, false, false, p0, p1, 0, 60, 100, true)
      end
      reaper.MIDI_Sort(mt)
      local snd = reaper.CreateTrackSend(mtr, tr)
      reaper.SetTrackSendInfo_Value(mtr, 0, snd, "I_SRCCHAN", -1)
      reaper.SetMediaTrackInfo_Value(mtr, "B_MAINSEND", 0)
    end
    local file = OUT .. "/" .. name .. ".wav"
    os.remove(file)
    reaper.GetSetProjectInfo(0, "RENDER_SETTINGS", 0, true)
    reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 1, true)
    reaper.GetSetProjectInfo(0, "RENDER_SRATE", 48000, true)
    reaper.GetSetProjectInfo(0, "RENDER_CHANNELS", 2, true)
    reaper.GetSetProjectInfo(0, "RENDER_TAILFLAG", 0, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_FILE", OUT, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", name, true)
    reaper.Main_OnCommand(42230, 0)
    local vals = {}
    for _, k in ipairs({1, 2, 3, 4, 5, 6, 7, 10, 12, 23}) do local _, v = reaper.TrackFX_GetFormattedParamValue(tr, fx, k - 1, ""); vals[#vals + 1] = v end
    log("caso", name, table.concat(vals, " | "))
  end
end
if mtr then reaper.DeleteTrack(mtr) end
reaper.Main_SaveProjectEx(0, OUT .. "/_tmp_test.rpp", 0)
reaper.Main_openProject("noprompt:" .. OUT .. "/_tmp_test.rpp")
reaper.Main_OnCommand(40860, 0) -- cerrar pestaña
log("done")
logf:close()
