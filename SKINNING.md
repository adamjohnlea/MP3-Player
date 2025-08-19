# Skinning Guide (Level 2)

This project supports Winamp-style, image-based skins you can switch at runtime without modifying playback logic.

A “skin” is a folder under `skins/` containing a `manifest.json` that defines window layout, colors, fonts, images, and some metrics. The `ThemeManager` in `player.py` loads the manifest and applies your choices to the existing UI.

Use this guide to create and test your own skins.


## Quick Start

1) Create a folder for your skin:
- `skins/my_skin/`

2) Add a `manifest.json` file to that folder. Start from this minimal template:
```
{
  "name": "my_skin",
  "window": {
    "width": 700,
    "height": 480,
    "use_custom_chrome": false
  },
  "colors": {
    "root_bg": "#101010",
    "frame_bg": "#101010",
    "playlist_bg": "#000000",
    "playlist_fg": "#00ff66",
    "playlist_select_bg": "#00ff66",
    "playlist_select_fg": "#000000",
    "status_bg": "#181818",
    "status_fg": "#cfcfcf"
  },
  "fonts": {
    "base": ["Helvetica", 10],
    "status": ["Helvetica", 9]
  },
  "images": {
    "back": "../../images/back50.png",
    "forward": "../../images/forward50.png",
    "play": "../../images/play50.png",
    "pause": "../../images/pause50.png",
    "stop": "../../images/stop50.png"
  },
  "metrics": {
    "control_padx": 10,
    "control_pady": 20,
    "playlist_width": 60
  }
}
```

3) Run `player.py`, open the “Skins” menu, and choose your skin by name. The UI updates immediately.

Tip: Duplicate the existing `skins/test/manifest.json` or `skins/default/manifest.json` and tweak it.


## Folder and File Structure

- Project root
  - `player.py` (contains ThemeManager)
  - `images/` (default control images used by built-in skins)
  - `skins/`
    - `default/`
      - `manifest.json`
    - `test/`
      - `manifest.json`
    - `my_skin/`
      - `manifest.json`
      - `images/` (optional — your skin’s own image assets)

Images can be stored either:
- inside your skin (recommended): `skins/my_skin/images/...`
- or reference shared assets in the project’s `images/` folder using relative paths like `../../images/play50.png`.

All image paths in the manifest are resolved relative to the manifest’s location.


## Manifest Schema (v1)

`manifest.json` is standard JSON (no comments). Unknown keys are ignored. Supported keys:

- name: string
  - Skin’s display name/id. Keep it lowercase and filesystem-safe.

- window: object
  - width: integer
    - Initial window width in pixels. Example: 700
  - height: integer
    - Initial window height in pixels. Example: 480
  - use_custom_chrome: boolean (default: false)
    - When true, removes OS title bar and borders (overrideredirect window). The window becomes draggable (click and drag anywhere).
    - When false, uses normal OS chrome.
  - transparent_color: string (optional, e.g., "#00ff00")
    - Attempts to set a color key for transparency. Mostly effective on Windows. On macOS/Linux it may be ignored.
  - background: string (optional, path to PNG)
    - Optional full-window background image. When set, ThemeManager creates a full-size canvas behind the widgets and draws this image.

- colors: object (all optional)
  - root_bg: string (e.g., "#101010"). Background of the root window.
  - frame_bg: string. Background of main frames (main/control/volume frames).
  - playlist_bg: string. Listbox background color.
  - playlist_fg: string. Listbox foreground (text) color.
  - playlist_select_bg: string. Listbox selected item background color.
  - playlist_select_fg: string. Listbox selected item text color.
  - status_bg: string. Status bar background.
  - status_fg: string. Status bar text color.

- fonts: object (optional)
  - base: [family, size]
    - Default font for the application. Example: ["Helvetica", 10]
  - status: [family, size]
    - Font for the status bar. Example: ["Helvetica", 9]

- images: object (paths are relative to this manifest)
  - back: string. PNG for the Previous button.
  - forward: string. PNG for the Next button.
  - play: string. PNG for the Play button (used when paused/stopped).
  - pause: string. PNG for the Pause state (shown while playing).
  - stop: string. PNG for the Stop button.
  - Notes:
    - PNG with alpha is supported by Tk 8.6’s PhotoImage.
    - Keep images roughly similar size (e.g., 32–64 px square) for consistent layout.

- metrics: object (optional)
  - control_padx: integer. Horizontal padding between control buttons.
  - control_pady: integer. Vertical padding around the control row.
  - playlist_width: integer. Width of the playlist listbox in characters (approximate).


## How ThemeManager Applies Your Skin

- Reads `manifest.json` and loads values into `ThemeManager.current_skin`.
- Loads declared images and stores them in `ThemeManager.images` (keeps references to prevent garbage collection).
- Applies window width/height and `root_bg`.
- If `use_custom_chrome` is true:
  - Removes OS chrome (`overrideredirect(True)`).
  - Enables click-drag anywhere to move the window.
  - If `transparent_color` is defined, attempts to set it via `wm_attributes('-transparentcolor', color)` (Windows).
- Configures playlist listbox colors and width.
- Configures frame/status bar colors and fonts.
- Assigns button images to Back/Forward/Play/Stop. Play/Pause images are also switched dynamically during playback.
- If `window.background` is provided, draws it on a canvas behind everything and keeps it at the back.

Unknown or missing values are safely ignored; defaults (hardcoded in the app) remain active.


## Creating and Using Images

- Format: PNG (with alpha). GIF works but PNG is recommended.
- Size: Keep controls consistent (e.g., 32px or 50px square). The project’s defaults are 50px icons.
- Background image: match your chosen `window.width/height`. If the window is resized by the user, the background image won’t scale automatically; it’s drawn at native size at the top-left.
- Paths: All paths are relative to your manifest. For assets in your skin, use `images/play.png`. For shared project assets, use `../../images/play50.png`.
- Avoid extremely large images to keep memory reasonable and UI responsive.


## Step-by-Step: Build Your First Skin

1) Copy the test skin:
- Duplicate `skins/test/manifest.json` to `skins/my_skin/manifest.json`.

2) Adjust colors:
- Change `colors.root_bg`, `colors.frame_bg`, and playlist/status colors to your palette.

3) Set window size:
- Update `window.width` and `window.height`.

4) Try custom chrome (optional):
- Set `window.use_custom_chrome` to `true`.
- Optionally set `window.transparent_color` (Windows) and create a background PNG with that color as the mask for cut-out regions.

5) Use your own icons (optional):
- Create `skins/my_skin/images/`.
- Add `play.png`, `pause.png`, `back.png`, `forward.png`, `stop.png`.
- Update `images` paths in the manifest to `"images/play.png"`, etc.

6) Test in the app:
- Run `player.py` and choose your skin from the “Skins” menu.
- Switch between “Default”, “Test”, and your new skin to compare.


## Platform Notes (Custom Chrome & Transparency)

- Custom chrome (`use_custom_chrome: true`) removes the OS title bar and borders and enables drag-to-move. You will need alternate ways to close/minimize (menu or keyboard). Future skins can add custom close/minimize buttons.
- Transparent color (`transparent_color`) is mainly effective on Windows. On macOS/Linux, per-pixel transparency is not guaranteed with classic Tk; shaped windows may not work as expected.


## Troubleshooting

- The skin does not appear in the Skins menu:
  - Ensure the directory exists under `skins/` and contains `manifest.json`.
  - Directory name is used as the menu label (title-cased). No spaces.

- Images not changing:
  - Check the `images` paths are correct relative to `manifest.json`.
  - Confirm the files exist and are valid PNGs.
  - Look at terminal output for any “Skin load failed” message.

- Colors/fonts don’t change:
  - Ensure the keys are spelled exactly as in the schema.
  - JSON is strict; no comments or trailing commas are allowed.

- Background image not visible:
  - Verify `window.background` path.
  - The background is drawn behind widgets; it will not tile or scale. Match the image to window dimensions.

- Window won’t drag with custom chrome:
  - Ensure `window.use_custom_chrome` is `true`.
  - Drag by clicking inside the window area (drag binding applies to the root when custom chrome is enabled).


## Best Practices

- Keep a consistent icon set (same sizes) to avoid uneven button layout.
- Choose readable color contrasts for playlist and status bar.
- If using custom chrome, consider adding a high-contrast background and leave padding around edges for safe drag areas.
- Save a copy of your working manifest before experimenting.


## Extending the Schema (Future Ideas)

While ThemeManager ignores unknown keys, you may plan for:
- images.slider_trough / images.slider_thumb
- menu/fonts overrides
- coordinates for custom close/minimize buttons when using custom chrome
- per-widget paddings and margins beyond `metrics`

If you add such keys, expect to also extend `ThemeManager.apply()` in `player.py`.


## Examples Included

- `skins/default/manifest.json` — baseline look using shared images.
- `skins/test/manifest.json` — demonstrates custom window size, colors, and custom chrome.

Use these as starting points for your own skins.


## FAQ

- Can I ship just a manifest and reuse all images from the project? Yes — point `images.*` to `../../images/*.png`.
- Can I make a non-rectangular window? Partially — on Windows you can experiment with `transparent_color` and a background image. On macOS/Linux, shaped windows are limited with pure Tk.
- Do I need to restart the app after changing a skin? No — choose a different skin in the Skins menu to reload. If you edit a manifest file, switch to another skin and back to force a reload.


---

Happy skinning! If you run into issues, open the project and check `player.py`’s `ThemeManager.apply()` for the exact keys and behavior implemented in this version.