# Boulder Dash NES Edition — Map & Cave Editor

A full-featured, interactive map editor and physics simulator for the NES edition of **Boulder Dash** (`Boulder Dash (USA) [!].nes`).

---

## Features

- **All 24 Caves Supported:** Seamlessly edit all caves across all 6 worlds (World 1-1 through World 6-4).
- **Pixel-Perfect NES Graphics:** Automatically extracts and renders the authentic 16x16 metatiles and palettes for each of the 6 world themes (Earth/Caves, Waves, Crystals, Pillars, Fire, Alien Organism).
- **Full Drawing Toolset:**
  - ✏️ **Pencil (`B`):** Single-tile placement & continuous brush stroke.
  - 🟩 **Rectangle Fill (`R`):** Fill large areas with a single drag.
  - 🔲 **Rectangle Outline (`O`):** Build hollow wall perimeters.
  - 📏 **Line Tool (`L`):** Crisp Bresenham line drawing.
  - 🪣 **Flood Fill (`F`):** Bucket fill contiguous areas.
  - 🧹 **Eraser (`E`):** Clear tiles to empty space.
  - 💧 **Eyedropper (`I` / `Alt+Click`):** Pick tile directly from canvas into active brush.
  - 🏃 **Rockford Spawn Marker (`S`):** Click any tile to set Rockford's starting coordinate $(X, Y)$.
  - ↩️ / ↪️ **Undo / Redo (`Ctrl+Z` / `Ctrl+Y`):** 50-step action history.
  - ▦ **Grid Toggle (`G`):** Show/hide 16x16 tile boundaries.
  - 🔍 **Dynamic Zoom:** 75% to 400% with mousewheel zoom and fit controls.
- **Level Properties Inspector:**
  - 💎 **Diamonds Needed:** Edit the exact diamond quota required to open the exit (0–99).
  - ⏱️ **Cave Time Limit:** Adjust countdown timer in seconds (0–255).
  - 📍 **Rockford Coordinates ($X, Y$):** Visual and numeric coordinate adjustments.
  - 🔑 **6-Digit Passwords:** View and modify passwords for Caves 1 through 23 directly in the ROM.
- **Real-Time Cave Diagnostics:**
  - Live count of diamonds, boulders, dirt, enemies, and amoebas.
  - Automated warning if diamonds on map are fewer than diamonds required.
  - Missing or unreachable exit door warnings.
- **Interactive In-Browser Playtest Simulator:**
  - Hit **Space** or click **Playtest** to launch the cave simulator.
  - Move Rockford with **Arrow Keys** or **WASD**.
  - Dig dirt, push boulders, collect diamonds, and trigger falling rock physics in real time to verify that your puzzles are solvable before playing on an emulator!
- **Zero-Dependency Dual Mode:**
  - Runs with a lightweight Python backend (`python3 server.py`) saving directly to `Boulder Dash.nes`.
  - Also works 100% offline as a standalone single-page application (`web/index.html`) with in-browser `.nes` export.

---

## Quick Start

### Option 1: Web Server Mode (Recommended)

1. Launch the server from terminal:
   ```bash
   python3 server.py
   ```
2. Open your browser to:
   ```
   http://localhost:8080
   ```
3. Edit any level, test with the in-browser simulator, and click **Save ROM** (`Ctrl+S`) to commit directly to `Boulder Dash.nes` (an automatic backup `Boulder Dash.nes.original.bak` is preserved).
4. Click **Export ROM** to download a patched `.nes` copy.

### Option 2: Standalone Offline Mode

Simply double-click or open [web/index.html](file:///Users/gilbertfulmore/Antigravity%20Projects/Boulder%20Dash%20Map%20Editor/web/index.html) in any modern web browser (Chrome, Safari, Firefox, Edge). All ROM graphics and data are embedded.

---

## Technical Reverse-Engineering Discoveries

During analysis of `Boulder Dash.nes` and classic tools, the exact ROM architecture was reverse-engineered:

1. **Cave Maps Structure:**
   - 24 Caves total (4 caves per world across 6 worlds).
   - Grid size: **40 columns $\times$ 22 rows** ($880$ tiles).
   - Byte format: **Uncompressed 4-bit nibbles** packed into 20 bytes per row = **440 bytes per cave**.
   - Packing: Low nibble = Column $2k$, High nibble = Column $2k+1$.
   - Cave ROM Offsets:
     - World 1: `0x8810` (1-1), `0x89C8` (1-2), `0x8B80` (1-3), `0x8D38` (1-4)
     - World 2: `0x8EF0` (2-1), `0x90A8` (2-2), `0x9260` (2-3), `0x9418` (2-4)
     - World 3: `0xB130` (3-1), `0xB2E8` (3-2), `0xB4A0` (3-3), `0xB658` (3-4)
     - World 4: `0xB810` (4-1), `0xB9C8` (4-2), `0xBB80` (4-3), `0xBD38` (4-4)
     - World 5: `0xF010` (5-1), `0xF1C8` (5-2), `0xF380` (5-3), `0xF538` (5-4)
     - World 6: `0xF6F0` (6-1), `0xF8A8` (6-2), `0xFA60` (6-3), `0xFC18` (6-4)

2. **Properties & Passwords Table:**
   - Level Properties: PRG `0x7250` (diamonds needed, timer, diamond points, Rockford start $X, Y$).
   - Passwords Table: PRG `0x2938` ($0\text{x}2938 + 8 \times i + 1$, 6 digits per cave).

3. **Tile Nibble Codes (0–15):**
   - `0`: Empty Walk-through Space
   - `1`: Empty Cleared Space (transient state that turns into `0`)
   - `2`: Dirt (Diggable soil)
   - `3`: Steel Wall (Indestructible perimeter)
   - `4`: Exit Door (Disguised as Wall until diamond quota is met, then turns into Portal `$F3E0`)
   - `5`: Brick Wall (Destructible wall; boulders roll off edges)
   - `6`: Magic Wall (Disguised as Wall until hit by falling boulder; converts boulders into diamonds)
   - `7`: Boulder / Rock (Falls and rolls)
   - `8`: Diamond (Collectible gem)
   - `9`: Diamond Sparkle (Star explosion frame that turns into a Diamond)
   - `10`: Explosion Sparkle (Star explosion frame that clears to Empty Space)
   - `11`: Firefly (Patrols clockwise; explodes into 3×3 empty space when crushed)
   - `12`: Butterfly (Patrols counter-clockwise; explodes into 9 diamonds when crushed)
   - `13`: Amoeba (Expands; turns into diamonds if trapped, or petrifies into `15` if overgrown)
   - `14`: Rockford Collision Marker (`$E0`) / Amoeba (Alternate)
   - `15`: Petrified Amoeba / Spider (`$F0`)
