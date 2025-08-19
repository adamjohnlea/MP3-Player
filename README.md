### MP3 Player (Tkinter + Pygame)

A simple cross‑platform MP3 player built with Tkinter for the UI and pygame.mixer for audio playback. It supports creating a playlist from local MP3 files, play/pause/stop, next/previous, volume control, a seek bar with smooth scrubbing, and a status bar showing elapsed/total time.

---

### Features

- Playlist management
  - Add a single MP3 or multiple MP3s via the menu
  - Remove selected track or clear the entire playlist
- Playback controls
  - Play/Pause toggle, Stop, Next, Previous
  - Auto‑advance to the next track when the current one ends; stop at the last track
- Time + seeking
  - Elapsed/total time display in the status bar
  - Seek by dragging the time slider; release to jump smoothly without jitter
  - Cached track lengths (via mutagen) to avoid repeated disk I/O and reduce stutter
- Volume control via a vertical slider (inverted: bottom = mute, top = max)
- Robust asset loading using absolute paths for control button images
- Skinning (Level 2): Switch skins at runtime from the Skins menu; per-skin colors, fonts, images, window size, and optional custom chrome

Limitations
- Playback and duration handling are optimized for MP3 files (file dialogs only offer .mp3).
- Seeking is best‑effort using pygame’s start parameter; sample‑accurate seeking may vary by platform/codec.

---

### Project structure

- player.py — main application (Tkinter window, playlist box, status bar, controls)
- images/
  - back50.png, forward50.png, play50.png, pause50.png, stop50.png — button icons
- skins/
  - default/manifest.json — baseline skin (uses shared images)
  - test/manifest.json — demo skin with different colors/size and optional custom chrome
- SKINNING.md — complete guide to authoring skins and the manifest schema
- .gitignore

Note: Make sure the images directory exists alongside player.py and contains the five files above. Skins are discovered dynamically from the skins/ directory and can be switched at runtime from the Skins menu.

---

### Requirements

- Python 3.8+
- Tkinter (bundled with most Python distributions; on some Linux distros install `python3-tk` via your package manager)
- pygame (audio playback)
- mutagen (read MP3 duration)

Install Python packages:

- pip: `pip install pygame mutagen`
- pipx (optional): `pipx inject your-env pygame mutagen`

Platform‑specific notes
- Linux: You may need SDL_mixer with MP3 support (often included with pygame wheels). If you see MP3 playback errors, ensure system libraries are up to date.
- macOS: If using a python.org or Homebrew Python, Tkinter is typically present; if missing, reinstall Python or add the `tcl-tk` formula (Homebrew) and link against it.
- Windows: Tkinter ships with official Python; simply ensure you installed Python with the “tcl/tk and IDLE” option.

---

### Running the app

1) Install dependencies (see Requirements).
2) Ensure the `images/` folder is present next to `player.py` with the 5 PNGs.
3) From the project directory, run:

- `python player.py`

This opens the MP3 Player window.

---

### Using the app

- Add songs:
  - Menu → “Add Songs” → “Add One Song To Playlist” to choose a single MP3
  - Menu → “Add Songs” → “Add Many Songs To Playlist” to choose multiple MP3s
- Remove songs:
  - Menu → “Remove Songs” → “Delete A Song From Playlist” removes the selected item
  - Menu → “Remove Songs” → “Delete All Songs From Playlist” clears the list
- Control playback:
  - Play/Pause button toggles between play and pause
  - Stop button stops playback and resets the time slider
  - Back/Forward buttons move to previous/next track in the playlist
- Seek within a track:
  - Drag the horizontal slider to preview the time in the status bar
  - Release the mouse to jump to that position (smooth scrubbing)
- Volume:
  - Adjust the vertical slider (0.0–1.0)

Status bar shows “Time Elapsed: mm:ss of mm:ss”.

---

### Current implementation details

- Track length caching: The app uses mutagen to read MP3 length once per file and caches the result to avoid repeated disk access each second.
- Smooth seeking: While dragging the slider, the app previews time without forcing playback to jump; on release, it seeks to the chosen second using `pygame.mixer.music.play(start=...)`, with a fallback to reload the track and seek if needed.
- Navigation buttons are enabled/disabled based on selection and playlist length.
- Image paths are resolved relative to `player.py` so the app can be launched from any working directory.

---

### Troubleshooting

- No audio or MP3 won’t play
  - Confirm `pygame` installed: `python -c "import pygame; print(pygame.__version__)"`
  - Reinstall pygame: `pip install --upgrade --force-reinstall pygame`
  - On Linux, ensure system codecs/SDL libraries are present; try updating your system packages.
- Tkinter missing
  - Linux: `sudo apt-get install python3-tk` (Debian/Ubuntu) or the equivalent for your distro.
- Icons not showing / crash on startup
  - Verify `images/back50.png`, `images/forward50.png`, `images/play50.png`, `images/pause50.png`, `images/stop50.png` exist in an `images/` folder next to `player.py`.
- Can’t seek precisely
  - MP3 seeking precision can vary; consider converting to CBR MP3 for better results or see the proposed improvements below for alternative backends.

---

### Roadmap / Proposed improvements

Core functionality
- Add shuffle and repeat modes (repeat one / repeat all)
- Double‑click playlist item to play immediately; Enter key to play selected
- Persist volume level, last played track, and playlist between sessions
- Keyboard shortcuts (Space = play/pause, S = stop, ←/→ = seek, ± = volume)
- Drag‑and‑drop MP3 files/folders onto the window to add to the playlist
- Display the currently playing track more prominently and auto‑scroll selection

Audio/technical
- Improve seeking accuracy and resilience
  - Consider using a backend with better random access (e.g., `pydub` + ffmpeg/avlib, or `vlc` bindings)
  - Pre‑scan frame index for MP3s to improve seek granularity
- Support additional formats (WAV, OGG, AAC/M4A) with proper duration parsing
- Crossfade or gapless playback options

UX/UI
- Show track metadata (artist, title, album) via ID3 tags (mutagen)
- Show album art (embedded image) if available
- Visual polish: theming (ttk styles), responsive layout, larger touch targets
- Disable buttons more proactively when not applicable and show tooltips
- Fallback to text buttons if images are missing; include bundled default theme

Code quality & packaging
- Refactor into a class‑based structure; separate UI logic, playback control, and model
- Add type hints and docstrings; run linters (flake8/ruff) and formatters (black)
- Add a `requirements.txt` and optionally a `pyproject.toml`
- Add simple tests for non‑GUI logic (e.g., playlist operations, caching)
- Provide a packaged executable (PyInstaller) for Windows/macOS/Linux

Stability & error handling
- Replace broad `except Exception: pass` blocks with user‑visible messages and logging
- Centralize error handling; show non‑blocking dialogs for recoverable issues
- Validate file existence and handle moved/removed files gracefully

Developer experience
- Add CI workflow to lint/test on pushes and PRs
- Add issue templates and contribution guidelines

---

### Contributing

Issues and PRs are welcome. See the Roadmap for ideas. Please discuss significant changes in an issue before opening a PR.

---

### License

Choose a license (e.g., MIT, Apache‑2.0) and add a LICENSE file. Update this section accordingly.


---

### Skinning (Level 2)

This app supports runtime skin switching. Skins are folders under `skins/` containing a `manifest.json` with colors, fonts, images, window size, and optional custom chrome.

- Using skins:
  - Run the app and open the “Skins” menu to switch between available skins (e.g., Default, Test).
  - The window updates immediately; no restart required.
- Custom chrome per skin:
  - Skins can set `window.use_custom_chrome: true` to remove OS title bar/borders and enable click-drag to move the window.
  - Optionally set `window.transparent_color` (best on Windows) to experiment with shaped/transparent regions.
- Authoring skins:
  - See SKINNING.md for the complete manifest schema, examples, and best practices.

