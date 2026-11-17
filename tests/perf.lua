-- Peor caso: M/S, lookahead, filtros del sidechain, transitorios, MIDI de salida, mezcla; render de 60 s.
local OUT = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$") .. "/out"
local AUDIO = os.getenv("HOME") .. "/Music/ClaudeBeats/Master/Nube baja (master X20).wav"
local f = io.open(OUT .. "/perf.txt", "w")
reaper.Main_OnCommand(40859, 0)
reaper.InsertTrackAtIndex(0, false); local tr = reaper.GetTrack(0, 0)
local item = reaper.AddMediaItemToTrack(tr); local take = reaper.AddTakeToMediaItem(item)
reaper.SetMediaItemTake_Source(take, reaper.PCM_Source_CreateFromFile(AUDIO))
reaper.SetMediaItemInfo_Value(item, "D_LENGTH", 60)
local function render(name, nfx, setup)
  while reaper.TrackFX_GetCount(tr) > 0 do reaper.TrackFX_Delete(tr, 0) end
  for k = 1, nfx do local fx = reaper.TrackFX_AddByName(tr, "JS:Nube Gate/nube_gate.jsfx", false, -1); setup(fx) end
  os.remove(OUT .. "/" .. name .. ".wav")
  reaper.GetSetProjectInfo(0, "RENDER_SETTINGS", 0, true); reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 1, true)
  reaper.GetSetProjectInfo_String(0, "RENDER_FILE", OUT, true); reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", name, true)
  local t0 = reaper.time_precise(); reaper.Main_OnCommand(42230, 0); return reaper.time_precise() - t0
end
local t_empty = render("perf_vacio", 0, function() end)
local t_full = render("perf_todo", 10, function(fx)
  -- slider N = parámetro N-1: umbral -30, transitorio, lookahead 5, M/S, cortes del SC, mezcla 80, MIDI salida
  for p, v in pairs({[0] = -30, [9] = 1, [11] = 5, [14] = 1, [20] = 80, [22] = 1}) do reaper.TrackFX_SetParam(tr, fx, p, v) end
  reaper.TrackFX_SetParamNormalized(tr, fx, 16, 0.4); reaper.TrackFX_SetParamNormalized(tr, fx, 17, 0.6)
end)
f:write(string.format("sin plugin %.2f s | 10 instancias en el peor caso %.2f s (60 s de audio)\n", t_empty, t_full))
reaper.Main_SaveProjectEx(0, OUT .. "/_tmp_perf.rpp", 0); reaper.Main_openProject("noprompt:" .. OUT .. "/_tmp_perf.rpp"); reaper.Main_OnCommand(40860, 0)
f:write("done\n"); f:close()
