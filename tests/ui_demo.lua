-- Abre una pestaña de demo: pista con voz (fader en -inf, no suena), Nube Gate con un preset,
-- ventana del FX flotante y reproducción en loop para ver las gráficas. Cerrar con tests/ui_close.lua.
local ROOT = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$")
-- opciones desde tests/reopen.sh (REAPER no hereda las variables de entorno): "preset t0"
local of = io.open(ROOT .. "/out/demo_opts.txt"); local OPT = of and of:read("*l") or ""; if of then of:close() end
local O_PRESET, O_T0 = OPT:match("^(%S+)%s+(%S+)")
local AUDIO = os.getenv("NUBE_AUDIO") or (os.getenv("HOME") .. "/Music/ClaudeBeats/Media/voz_sola_seca.wav")
reaper.Main_OnCommand(40859, 0)
reaper.InsertTrackAtIndex(0, false); local tr = reaper.GetTrack(0, 0)
reaper.GetSetMediaTrackInfo_String(tr, "P_NAME", "Nube Gate demo", true)
reaper.SetMediaTrackInfo_Value(tr, "D_VOL", 0)
local item = reaper.AddMediaItemToTrack(tr); local take = reaper.AddTakeToMediaItem(item)
local src = reaper.PCM_Source_CreateFromFile(AUDIO); reaper.SetMediaItemTake_Source(take, src)
reaper.SetMediaItemInfo_Value(item, "D_LENGTH", reaper.GetMediaSourceLength(src))
reaper.UpdateArrange()
local fx = reaper.TrackFX_AddByName(tr, "JS:Nube Gate/nube_gate.jsfx", false, -1)
reaper.TrackFX_SetParam(tr, fx, 24, tonumber(O_PRESET or "3"))
reaper.TrackFX_Show(tr, fx, 3)
local t0 = tonumber(O_T0 or "20")
reaper.GetSet_LoopTimeRange(true, true, t0, t0 + 40, false)
reaper.SetEditCurPos(t0, false, false)
reaper.GetSetRepeat(1)
reaper.OnPlayButton()
local f = io.open(ROOT .. "/out/ui.txt", "w"); f:write("done\n"); f:close()
