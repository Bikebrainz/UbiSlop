# UbiSlop

An experiment in building a **client-side behavioral anti-cheat for Rainbow Six
Siege that runs entirely in user space** — no kernel driver, no DLL injection
into the game. It watches for the observable side effects of cheating (memory
tampering, inhuman mouse kinematics, ESP overlays, ESP-looking pixels on screen)
and writes alerts to a local JSON file that a GUI tails in real time.

Prototype, in Python. Not affiliated with Ubisoft or BattlEye, not a replacement
for either, and not something to run on someone else's machine.

The whole project lives in [`R6SExternalAntiCheat/`](R6SExternalAntiCheat).

## Design premise

Kernel anti-cheat wins the memory-integrity fight and loses on trust, stability,
and the blast radius of a bug. The bet here is that a **detector with no special
privileges** can still catch a meaningful share of cheats, because most cheats
have to surface *somewhere* the user can see — an overlay window, a mouse path no
hand produces, a memory region that changes when it shouldn't.

Everything is offline-first: detectors write to `r6s_alerts.json` on disk, and
cloud escalation is an optional uploader on top.

## Sensors

| Script | Watches for |
|---|---|
| `r6s_guard.py` | Handles opened against the `RainbowSix` process with VM read/write access, plus periodic hashing of fixed memory regions — a hash change flags tampering and grabs a screenshot |
| `r6s_input_tracer.py` | Mouse kinematics at 120 Hz over a 2-second window — speed spikes past 3600 px/s, snap distances, and burst counts that read as aim-assist rather than a human wrist |
| `r6s_overlay_watcher.py` | Top-level windows whose titles match `esp`/`cheat`/`radar`/`hack`/`crosshair`, with a Steam/Discord/NVIDIA/browser exclusion list |
| `r6s_screen_capture.py` | The screen itself — counts pixels at classic ESP colors past a threshold, and OCRs for words like `enemy`, `armor`, `wallhack`, `distance` |
| `r6s_alert_viewer.py` | Nothing — it's the Tk GUI that polls `r6s_alerts.json` every 2s and renders the feed |
| `r6s_local_runner.py` | Supervisor: launches the detector modules as subprocesses, logs each to `r6s_logs/`, and offers one shutdown button |
| `r6s_uploader.py` | Tray shell for the uploader agent, with a file-integrity watch on the alert file |

Every detector shares one alert format — `{type, timestamp, data}` appended to
`r6s_alerts.json` — so a new sensor only has to call `log_alert()` to show up in
the GUI.

## Running it

Windows only (`pywin32`, `ctypes.windll`, `ImageGrab`). Python 3.10+.

```bash
cd R6SExternalAntiCheat
pip install -r requirements.txt
python scripts/r6s_local_runner.py
```

`r6s_screen_capture.py` additionally needs **Tesseract** installed and on PATH
for the OCR pass (`pytesseract` is a binding, not the engine — and note it is
missing from `requirements.txt`).

Artifacts land next to the working directory: `r6s_alerts.json`,
`r6s_snapshots/`, `r6s_logs/`.

## Known gaps

This is a prototype and the wiring shows:

- **The supervisor's module list doesn't match the filenames on disk.**
  `r6s_local_runner.py` launches `r6s_guard_with_snapshot.py` and
  `r6s_input_tracer_with_snap_overlay.py`; the repo has `r6s_guard.py` and
  `r6s_input_tracer.py`. Same for `r6s_uploader.py`, which spawns a
  `r6s_uploader_agent.py` that isn't committed. Rename or fix the constants
  before expecting the one-command launch to work.
- **Upload target and API key are placeholders** (`r6s-acs.example.com`,
  `your-secure-api-key`) in `r6s_overlay_watcher.py` and `r6s_screen_capture.py`.
  There is no server side in this repo.
- **Memory-scan regions are hardcoded** (`0x00400000`, `0x00500000`) and assume a
  fixed image base — ASLR alone will make these meaningless on a real run.
- **No calibration data**, so every threshold (speed, pixel count, OCR terms) is
  a guess. False-positive rate is unmeasured.
- Screen-capture and OCR sensors are inherently privacy-heavy: they screenshot
  the whole desktop, not just the game.

## Packaging

`packaging/` and `installer/` carry a PyInstaller + NSIS plan and a checklist for
producing a Windows installer. Neither is built by CI.

## License

MIT — see [`R6SExternalAntiCheat/LICENSE`](R6SExternalAntiCheat/LICENSE).

Run it on your own machine, for your own account. Detection heuristics this
broad on someone else's system is surveillance, not anti-cheat.
