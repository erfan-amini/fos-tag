# FoS TaG: Frontiers of Science tools and games

One Streamlit app for the seminar room, at **fos-tag.streamlit.app**. A Home button at
the top of every page; no side menus.

| Page | What it does |
|---|---|
| **Timer** (`/timer`) | Full-screen countdown for the projector. Presets, +1/−1 minute, reminders at 10, 5 and 1 minute, a chime at the end, optional background music, light and dark screens, keyboard shortcuts (press `?`). The title and note are typed straight onto the screen and remembered in the browser. |
| **Two-Point Threshold** | Start a room; the board shows a 4-letter code and a QR. Pairs scan it, type their names, pick one of 11 symbols and a colour, and enter three thumb and three forearm readings for each participant. The board shows the class dot plots, the means, the 95% intervals (mean ± 2 SE) and whether they overlap, live. Export to Excel any time: raw readings, per-person means, summary numbers and the plot. |
| **Ballooniverse** | Same joining flow. Pairs enter the initial and final distance of three dots and the wavy line; the instructor sets the inflation time when starting the room (default 10 s). Every dot lands on the class graph of velocity against final distance, with a trend line through the origin and its slope. Export to Excel. |
| **Nuclear Diplomacy** | The K=1 Project simulation, moderated from the projector: decision slips, the attack draw with a drumroll and a needle, sanctions, history, debrief. Background music, drumroll and explosion are switches in Settings. |

## How the live rooms work

- Rooms and their data live in the app's memory and in `data/rooms.json`, and are
  cleared 24 hours after their last change. A pair that closes its page gets its entry
  back by scanning again and typing the same names.
- Each symbol can be taken once per room, so every pair is distinguishable on the board.
- The board refreshes every two seconds. Open it in full screen (F11) on the projector.
- Sections 22 and 24 get separate rooms; the room name shows on the board and in the
  export file.

## On Streamlit Community Cloud

The cloud shows the app inside an iframe. Internal links are sent to the top window by a
small script, and the timer page (`static/timer.html`) is embedded by `tag/timer.py`
with its music inlined, since the cloud does not serve static files directly.

## Sounds

Everything in `static/sounds/` is synthesized by `tools/make_sounds.py`, so nothing is
copyrighted. To use your own track, drop an MP3 with the same name in that folder:
`lobby.mp3` (hub, boards, timer), `tension.mp3` (diplomacy game), `drumroll.mp3`,
`explosion.mp3`, `pop.mp3` (a pair joins).

## Keeping the app awake

Streamlit Community Cloud puts an app to sleep after a stretch without visitors, and a
plain web request does not wake it. `.github/workflows/keepalive.yml` opens the app in a
real browser every six hours (`tools/keepalive.py`) and presses the wake-up button if
needed. GitHub switches off scheduled workflows after 60 days without a commit, so the
same job writes a timestamp commit once the last commit is 40 days old.

## Run it yourself

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
python -m pytest -q
```

The join link and QR use the address the browser sees, so they work locally and on the
cloud without configuration.

## Credits

Nuclear Diplomacy: game design, rules and country briefs by the K=1 Project, Columbia
University (k1project.columbia.edu). Flags from Wikimedia Commons (public domain).
Castle Bravo photograph: U.S. Department of Energy (public domain). Campus and reading
room photographs: Columbia University.
