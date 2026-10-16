// Boulder Dash NES Map Editor - Client Engine
(function() {
  'use strict';

  // Constants
  const COLS = 40;
  const ROWS = 22;
  const TILE_SIZE = 16;
  const MAP_W = COLS * TILE_SIZE; // 640
  const MAP_H = ROWS * TILE_SIZE; // 352
  const ROM_SIZE = 65552;

  // App State
  let romBuffer = null; // Uint8Array(65552) - populated when user loads a .nes ROM
  let originalRomBuffer = null; // Backup copy of user-loaded .nes ROM
  let pendingExportAfterLoad = false; // If true, auto-export right after user selects a .nes file
  let allLevels = [];
  let tilesLibrary = {};
  let currentLevelIdx = 0;
  let currentLevel = null;
  let activeTile = 2; // Default Dirt
  let activeTool = 'pencil';
  let zoom = 2.0; // 200% default
  let showGrid = true;
  let isDrawing = false;
  let drawStartX = -1;
  let drawStartY = -1;
  let lastTileX = -1;
  let lastTileY = -1;

  // Undo / Redo
  let undoStack = [];
  let redoStack = [];
  const MAX_HISTORY = 50;

  // Preloaded Tile Images
  let tileImages = {}; // key: `world_tileId`
  let portalImages = {}; // key: `world` -> open portal image for Tile 4
  let rockfordImg = null; // Authentic NES Rockford sprite

  // DOM Elements
  const levelSelect = document.getElementById('levelSelect');
  const paletteGrid = document.getElementById('paletteGrid');
  const themeBadge = document.getElementById('themeBadge');
  const activeTileImg = document.getElementById('activeTileImg');
  const activeTileName = document.getElementById('activeTileName');
  const activeTileDesc = document.getElementById('activeTileDesc');

  const canvasContainer = document.getElementById('canvasContainer');
  const canvasWrapper = document.getElementById('canvasWrapper');
  const mapCanvas = document.getElementById('mapCanvas');
  const mapCtx = mapCanvas.getContext('2d');
  const gridCanvas = document.getElementById('gridCanvas');
  const gridCtx = gridCanvas.getContext('2d');
  const overlayCanvas = document.getElementById('overlayCanvas');
  const overlayCtx = overlayCanvas.getContext('2d');

  const zoomDisplay = document.getElementById('zoomDisplay');
  const statusCoord = document.getElementById('statusCoord');
  const statusTile = document.getElementById('statusTile');
  const saveStatus = document.getElementById('saveStatus');

  const propDiamonds = document.getElementById('propDiamonds');
  const propTime = document.getElementById('propTime');
  const propStartX = document.getElementById('propStartX');
  const propStartY = document.getElementById('propStartY');
  const propPassword = document.getElementById('propPassword');
  const btnApplyProps = document.getElementById('btnApplyProps');

  const statDiamonds = document.getElementById('statDiamonds');
  const statRocks = document.getElementById('statRocks');
  const statDirt = document.getElementById('statDirt');
  const statEnemies = document.getElementById('statEnemies');
  const statAmoeba = document.getElementById('statAmoeba');
  const statExit = document.getElementById('statExit');
  const statAlert = document.getElementById('statAlert');

  const playtestModal = document.getElementById('playtestModal');
  const helpModal = document.getElementById('helpModal');
  const simCanvas = document.getElementById('simCanvas');
  const simCtx = simCanvas.getContext('2d');
  const hudNeed = document.getElementById('hudNeed');
  const hudGot = document.getElementById('hudGot');
  const hudTime = document.getElementById('hudTime');
  const hudPassword = document.getElementById('hudPassword');

  const fileInput = document.getElementById('fileInput');
  const toast = document.getElementById('toast');

  const TILE_DESCRIPTIONS = [
    "Empty walk-through space",
    "Transient cleared space (becomes Empty Space)",
    "Standard diggable earth / soil",
    "Indestructible steel boundary wall",
    "Exit Door — same graphic/palette as a wall until all gems are collected, then turns into a portal",
    "Standard brick wall — boulders & diamonds roll off edges",
    "Magic Wall — looks like a wall until hit by a falling boulder, then turns boulders into diamonds",
    "Heavy round boulder that falls, rolls, and can be pushed",
    "Collectible diamond required to open the Exit Door",
    "Diamond sparkle — star explosion frame that immediately turns into a Diamond",
    "Explosion sparkle — star explosion frame that immediately clears to Empty Space",
    "Firefly enemy — patrols clockwise; explodes into 3×3 space when crushed",
    "Butterfly enemy — patrols counter-clockwise; explodes into 9 diamonds when crushed",
    "Amoeba — expands through dirt/space; turns into diamonds if trapped, or petrifies if overgrown",
    "Internal Rockford collision marker ($E0) / alternate amoeba tile",
    "Petrified Amoeba / Spider ($F0) — static block that overgrown amoebas turn into"
  ];

  // Initialize
  async function init() {
    setupEventListeners();
    await loadData();
    renderGridLines();
    applyZoom();
  }

  function updateRomStatusIndicator() {
    if (romBuffer) {
      saveStatus.textContent = 'ROM: Loaded & Ready';
      saveStatus.style.color = '#55ff55';
    } else {
      saveStatus.textContent = 'ROM: Not Loaded (Use 📂 Load ROM to Export)';
      saveStatus.style.color = '#38bdf8';
    }
  }

  // Load Data
  async function loadData() {
    showToast('Loading Boulder Dash Cave Data...', false);

    // 1. Try Server API first if served over HTTP/HTTPS
    if (window.location.protocol.startsWith('http')) {
      try {
        const [levelsRes, tilesRes] = await Promise.all([
          fetch('/api/levels'),
          fetch('/api/tiles')
        ]);

        if (levelsRes.ok && tilesRes.ok) {
          const levelsData = await levelsRes.json();
          const tilesData = await tilesRes.json();

          allLevels = levelsData.levels;
          tilesLibrary = tilesData.tiles;

          if (levelsData.has_rom) {
            try {
              const romRes = await fetch('/api/rom');
              if (romRes.ok) {
                const ab = await romRes.arrayBuffer();
                romBuffer = new Uint8Array(ab);
                originalRomBuffer = new Uint8Array(romBuffer);
              }
            } catch (e) {}
          }

          await preloadTileImages();
          populateLevelSelect();
          selectLevel(0);
          updateRomStatusIndicator();
          showToast(romBuffer ? 'Boulder Dash ROM & Caves ready!' : 'Cave Editor ready! Load your .nes ROM to export.', true);
          return;
        }
      } catch (err) {
        // Fallback to offline bundled level metadata below
      }
    }

    // 2. Standalone / Offline fallback using pre-bundled level metadata & tile library (no ROM binary included)
    if (window.DEFAULT_LEVELS_DUMP && window.DEFAULT_TILES_LIBRARY) {
      allLevels = JSON.parse(JSON.stringify(window.DEFAULT_LEVELS_DUMP.levels));
      tilesLibrary = window.DEFAULT_TILES_LIBRARY;

      await preloadTileImages();
      populateLevelSelect();
      selectLevel(0);
      updateRomStatusIndicator();
      showToast('Cave Editor ready! Click "📂 Load ROM" to load your Boulder Dash.nes file.', true);
      return;
    }

    showToast('Error loading editor data.', false, true);
  }

  function populateLevelSelect() {
    levelSelect.innerHTML = '';
    allLevels.forEach((lvl, idx) => {
      const opt = document.createElement('option');
      opt.value = idx;
      opt.textContent = `${lvl.name} (World ${lvl.world}-${lvl.cave})`;
      levelSelect.appendChild(opt);
    });
  }

  // Preload Base64 Tile Images
  function preloadTileImages() {
    const promises = [];
    for (let w = 0; w < 6; w++) {
      const worldTiles = tilesLibrary[w] || [];
      worldTiles.forEach(t => {
        const key = `${w}_${t.id}`;
        const img = new Image();
        img.src = t.image;
        tileImages[key] = img;
        promises.push(new Promise(res => img.onload = res));

        if (t.id === 4 && t.portal_image) {
          const pImg = new Image();
          pImg.src = t.portal_image;
          portalImages[w] = pImg;
          promises.push(new Promise(res => pImg.onload = res));
        }
      });
    }
    if (tilesLibrary.rockford) {
      rockfordImg = new Image();
      rockfordImg.src = tilesLibrary.rockford;
      promises.push(new Promise(res => rockfordImg.onload = res));
    }
    return Promise.all(promises);
  }

  // Select Level
  function selectLevel(idx) {
    if (idx < 0 || idx >= allLevels.length) return;
    currentLevelIdx = idx;
    levelSelect.value = idx;
    currentLevel = JSON.parse(JSON.stringify(allLevels[idx]));

    undoStack = [];
    redoStack = [];

    // Update Theme Badge & Palette
    const w = currentLevel.tileset;
    themeBadge.textContent = `World ${currentLevel.world} Theme`;
    renderPalette();

    // Update Properties
    propDiamonds.value = currentLevel.diamonds_needed;
    propTime.value = currentLevel.time_limit;
    propStartX.value = currentLevel.start_x;
    propStartY.value = currentLevel.start_y;
    propPassword.value = currentLevel.password;

    renderMap();
    updateDiagnostics();
    clearOverlay();
  }

  // Render Palette Grid
  function renderPalette() {
    paletteGrid.innerHTML = '';
    const w = currentLevel.tileset;
    const tiles = tilesLibrary[w] || [];

    tiles.forEach(t => {
      const el = document.createElement('div');
      el.className = `tile-choice ${t.id === activeTile ? 'active' : ''}`;
      el.title = `${t.name} (Tile ${t.id}) — ${TILE_DESCRIPTIONS[t.id] || ''}`;

      const img = document.createElement('img');
      img.src = t.image;
      el.appendChild(img);

      // For Exit Door (Tile 4), show a small corner pip of the open Portal graphic
      if (t.id === 4 && t.portal_image) {
        const pip = document.createElement('img');
        pip.className = 'tile-portal-pip';
        pip.src = t.portal_image;
        pip.title = 'Turns into this Portal when all required gems are collected';
        el.appendChild(pip);
      }

      const badge = document.createElement('span');
      badge.className = 'tile-id-badge';
      badge.textContent = t.id;
      el.appendChild(badge);

      const label = document.createElement('span');
      label.className = 'tile-short-label';
      label.textContent = t.short_name || t.name;
      el.appendChild(label);

      el.addEventListener('click', () => {
        setActiveTile(t.id);
      });

      paletteGrid.appendChild(el);
    });

    updateActiveTilePreview();
  }

  // Set Active Tile
  function setActiveTile(id) {
    activeTile = id;
    document.querySelectorAll('.tile-choice').forEach((el, idx) => {
      el.classList.toggle('active', idx === id);
    });
    updateActiveTilePreview();
  }

  function updateActiveTilePreview() {
    const w = currentLevel ? currentLevel.tileset : 0;
    const key = `${w}_${activeTile}`;
    const imgObj = tileImages[key];
    if (imgObj) {
      activeTileImg.src = imgObj.src;
    }
    const worldTiles = tilesLibrary[w] || [];
    const t = worldTiles[activeTile];
    activeTileName.textContent = t ? `${t.id}: ${t.name}` : `Tile ${activeTile}`;
    activeTileDesc.textContent = TILE_DESCRIPTIONS[activeTile] || `Nibble 0x${activeTile.toString(16)}`;
  }

  // Render Main Map Canvas
  function renderMap() {
    if (!currentLevel) return;
    const w = currentLevel.tileset;
    const grid = currentLevel.grid;

    mapCtx.fillStyle = '#000000';
    mapCtx.fillRect(0, 0, MAP_W, MAP_H);

    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const tileId = grid[r][c];
        const key = `${w}_${tileId}`;
        const img = tileImages[key];
        if (img) {
          mapCtx.drawImage(img, c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        }
      }
    }

    // Render Rockford Spawn Marker
    const sx = currentLevel.start_x;
    const sy = currentLevel.start_y;
    if (sx >= 0 && sx < COLS && sy >= 0 && sy < ROWS) {
      mapCtx.save();
      if (rockfordImg && rockfordImg.complete) {
        mapCtx.drawImage(rockfordImg, sx * TILE_SIZE, sy * TILE_SIZE, TILE_SIZE, TILE_SIZE);
      }
      // Golden outline
      mapCtx.strokeStyle = '#ffd700';
      mapCtx.lineWidth = 1.5;
      mapCtx.strokeRect(sx * TILE_SIZE + 0.5, sy * TILE_SIZE + 0.5, TILE_SIZE - 1, TILE_SIZE - 1);

      // Little Rockford 'S' spawn badge
      mapCtx.fillStyle = 'rgba(255, 215, 0, 0.9)';
      mapCtx.fillRect(sx * TILE_SIZE + 1, sy * TILE_SIZE + 1, 6, 6);
      mapCtx.fillStyle = '#000';
      mapCtx.font = 'bold 5px monospace';
      mapCtx.fillText('S', sx * TILE_SIZE + 2, sy * TILE_SIZE + 6);
      mapCtx.restore();
    }

    if (showGrid) {
      renderGridLines();
    }
  }

  // Render Grid Lines & Disguised Wall Badges (Exit Door / Magic Wall)
  function renderGridLines() {
    gridCtx.clearRect(0, 0, MAP_W, MAP_H);
    if (!showGrid) return;

    gridCtx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
    gridCtx.lineWidth = 1;
    gridCtx.beginPath();

    // Vertical lines
    for (let x = 0; x <= MAP_W; x += TILE_SIZE) {
      gridCtx.moveTo(x + 0.5, 0);
      gridCtx.lineTo(x + 0.5, MAP_H);
    }
    // Horizontal lines
    for (let y = 0; y <= MAP_H; y += TILE_SIZE) {
      gridCtx.moveTo(0, y + 0.5);
      gridCtx.lineTo(MAP_W, y + 0.5);
    }
    gridCtx.stroke();

    // When Grid is enabled, show subtle corner indicators on Tile 4 (Exit Door) and Tile 6 (Magic Wall)
    // since they share the exact same NES wall graphic/palette until triggered in gameplay
    if (currentLevel && currentLevel.grid) {
      gridCtx.save();
      gridCtx.font = 'bold 5px monospace';
      for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
          const tid = currentLevel.grid[r][c];
          if (tid === 4) {
            // Exit Door indicator
            gridCtx.strokeStyle = '#00e8d8';
            gridCtx.lineWidth = 1;
            gridCtx.strokeRect(c * TILE_SIZE + 0.5, r * TILE_SIZE + 0.5, TILE_SIZE - 1, TILE_SIZE - 1);
            gridCtx.fillStyle = 'rgba(0, 232, 216, 0.9)';
            gridCtx.fillRect(c * TILE_SIZE + 1, r * TILE_SIZE + 1, 6, 6);
            gridCtx.fillStyle = '#000';
            gridCtx.fillText('E', c * TILE_SIZE + 2, r * TILE_SIZE + 6);
          } else if (tid === 6) {
            // Magic Wall indicator
            gridCtx.strokeStyle = '#f878f8';
            gridCtx.lineWidth = 1;
            gridCtx.strokeRect(c * TILE_SIZE + 0.5, r * TILE_SIZE + 0.5, TILE_SIZE - 1, TILE_SIZE - 1);
            gridCtx.fillStyle = 'rgba(248, 120, 248, 0.9)';
            gridCtx.fillRect(c * TILE_SIZE + 1, r * TILE_SIZE + 1, 6, 6);
            gridCtx.fillStyle = '#000';
            gridCtx.fillText('M', c * TILE_SIZE + 2, r * TILE_SIZE + 6);
          }
        }
      }
      gridCtx.restore();
    }
  }

  // Overlay Management
  function clearOverlay() {
    overlayCtx.clearRect(0, 0, MAP_W, MAP_H);
  }

  function drawCursorPreview(tileX, tileY) {
    clearOverlay();
    if (tileX < 0 || tileX >= COLS || tileY < 0 || tileY >= ROWS) return;

    overlayCtx.save();
    overlayCtx.strokeStyle = '#3cbcfc';
    overlayCtx.lineWidth = 1.5;
    overlayCtx.strokeRect(tileX * TILE_SIZE + 0.5, tileY * TILE_SIZE + 0.5, TILE_SIZE - 1, TILE_SIZE - 1);

    if (activeTool === 'spawn') {
      overlayCtx.fillStyle = 'rgba(255, 215, 0, 0.4)';
      overlayCtx.fillRect(tileX * TILE_SIZE, tileY * TILE_SIZE, TILE_SIZE, TILE_SIZE);
    } else if (activeTool === 'eraser') {
      overlayCtx.strokeStyle = '#ff4444';
      overlayCtx.strokeRect(tileX * TILE_SIZE + 2, tileY * TILE_SIZE + 2, TILE_SIZE - 4, TILE_SIZE - 4);
    }
    overlayCtx.restore();
  }

  function drawShapePreview(startX, startY, endX, endY) {
    clearOverlay();
    overlayCtx.save();
    overlayCtx.strokeStyle = '#f8b800';
    overlayCtx.fillStyle = 'rgba(248, 184, 0, 0.25)';
    overlayCtx.lineWidth = 1;

    const minX = Math.min(startX, endX);
    const maxX = Math.max(startX, endX);
    const minY = Math.min(startY, endY);
    const maxY = Math.max(startY, endY);

    if (activeTool === 'rect-fill') {
      overlayCtx.fillRect(minX * TILE_SIZE, minY * TILE_SIZE, (maxX - minX + 1) * TILE_SIZE, (maxY - minY + 1) * TILE_SIZE);
      overlayCtx.strokeRect(minX * TILE_SIZE + 0.5, minY * TILE_SIZE + 0.5, (maxX - minX + 1) * TILE_SIZE - 1, (maxY - minY + 1) * TILE_SIZE - 1);
    } else if (activeTool === 'rect-outline') {
      overlayCtx.strokeRect(minX * TILE_SIZE + 0.5, minY * TILE_SIZE + 0.5, (maxX - minX + 1) * TILE_SIZE - 1, (maxY - minY + 1) * TILE_SIZE - 1);
    } else if (activeTool === 'line') {
      const pts = getLinePoints(startX, startY, endX, endY);
      pts.forEach(([x, y]) => {
        overlayCtx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        overlayCtx.strokeRect(x * TILE_SIZE + 0.5, y * TILE_SIZE + 0.5, TILE_SIZE - 1, TILE_SIZE - 1);
      });
    }
    overlayCtx.restore();
  }

  // Zoom Handling
  function setZoom(newZoom) {
    zoom = Math.max(0.75, Math.min(4.0, newZoom));
    applyZoom();
  }

  function applyZoom() {
    canvasWrapper.style.transform = `scale(${zoom})`;
    canvasWrapper.style.transformOrigin = 'center center';
    zoomDisplay.textContent = `${Math.round(zoom * 100)}%`;
  }

  // Coordinates Helper
  function getTileCoords(e) {
    const rect = mapCanvas.getBoundingClientRect();
    const clientX = e.clientX;
    const clientY = e.clientY;
    const x = Math.floor((clientX - rect.left) / (rect.width / COLS));
    const y = Math.floor((clientY - rect.top) / (rect.height / ROWS));
    return {
      x: Math.max(0, Math.min(COLS - 1, x)),
      y: Math.max(0, Math.min(ROWS - 1, y))
    };
  }

  // Push Undo State
  function pushUndo() {
    if (!currentLevel) return;
    undoStack.push(JSON.parse(JSON.stringify(currentLevel.grid)));
    if (undoStack.length > MAX_HISTORY) undoStack.shift();
    redoStack = [];
    saveStatus.textContent = 'ROM: Unsaved changes';
    saveStatus.style.color = '#ffaa00';
  }

  function undo() {
    if (undoStack.length === 0) return;
    redoStack.push(JSON.parse(JSON.stringify(currentLevel.grid)));
    currentLevel.grid = undoStack.pop();
    renderMap();
    updateDiagnostics();
    showToast('Undo', false);
  }

  function redo() {
    if (redoStack.length === 0) return;
    undoStack.push(JSON.parse(JSON.stringify(currentLevel.grid)));
    currentLevel.grid = redoStack.pop();
    renderMap();
    updateDiagnostics();
    showToast('Redo', false);
  }

  // Bresenham's Line Algorithm
  function getLinePoints(x0, y0, x1, y1) {
    const pts = [];
    const dx = Math.abs(x1 - x0);
    const dy = Math.abs(y1 - y0);
    const sx = (x0 < x1) ? 1 : -1;
    const sy = (y0 < y1) ? 1 : -1;
    let err = dx - dy;

    let cx = x0;
    let cy = y0;
    while (true) {
      pts.push([cx, cy]);
      if (cx === x1 && cy === y1) break;
      const e2 = 2 * err;
      if (e2 > -dy) { err -= dy; cx += sx; }
      if (e2 < dx) { err += dx; cy += sy; }
    }
    return pts;
  }

  // Flood Fill
  function floodFill(startX, startY, targetTile, replaceTile) {
    if (targetTile === replaceTile) return;
    const grid = currentLevel.grid;
    if (grid[startY][startX] !== targetTile) return;

    pushUndo();
    const queue = [[startX, startY]];
    const visited = new Uint8Array(COLS * ROWS);
    visited[startY * COLS + startX] = 1;

    while (queue.length > 0) {
      const [x, y] = queue.pop();
      grid[y][x] = replaceTile;

      const neighbors = [
        [x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]
      ];

      for (const [nx, ny] of neighbors) {
        if (nx >= 0 && nx < COLS && ny >= 0 && ny < ROWS) {
          const idx = ny * COLS + nx;
          if (!visited[idx] && grid[ny][nx] === targetTile) {
            visited[idx] = 1;
            queue.push([nx, ny]);
          }
        }
      }
    }

    renderMap();
    updateDiagnostics();
  }

  // Apply Shape
  function applyShape(startX, startY, endX, endY) {
    pushUndo();
    const grid = currentLevel.grid;
    const tile = (activeTool === 'eraser') ? 0 : activeTile;

    if (activeTool === 'rect-fill') {
      const minX = Math.min(startX, endX);
      const maxX = Math.max(startX, endX);
      const minY = Math.min(startY, endY);
      const maxY = Math.max(startY, endY);
      for (let r = minY; r <= maxY; r++) {
        for (let c = minX; c <= maxX; c++) {
          grid[r][c] = tile;
        }
      }
    } else if (activeTool === 'rect-outline') {
      const minX = Math.min(startX, endX);
      const maxX = Math.max(startX, endX);
      const minY = Math.min(startY, endY);
      const maxY = Math.max(startY, endY);
      for (let c = minX; c <= maxX; c++) {
        grid[minY][c] = tile;
        grid[maxY][c] = tile;
      }
      for (let r = minY; r <= maxY; r++) {
        grid[r][minX] = tile;
        grid[r][maxX] = tile;
      }
    } else if (activeTool === 'line') {
      const pts = getLinePoints(startX, startY, endX, endY);
      pts.forEach(([c, r]) => {
        grid[r][c] = tile;
      });
    }

    renderMap();
    updateDiagnostics();
  }

  // Update in-memory ROM buffer for a single level
  function syncLevelToRomBuffer(level) {
    if (!romBuffer) return;
    const meta = allLevels[level.index];
    if (!meta) return;

    // Diamonds
    romBuffer[meta.crystal_offset] = Math.max(0, Math.min(255, level.diamonds_needed));
    // Time
    romBuffer[meta.time_offset] = Math.max(0, Math.min(255, level.time_limit));
    // Start X, Y
    romBuffer[meta.start_x_offset] = Math.max(0, Math.min(39, level.start_x));
    romBuffer[meta.start_y_offset] = Math.max(0, Math.min(21, level.start_y));
    // Password (6 digits at 0x2938 + 8*index + 1)
    if (level.password && level.password.length === 6 && /^[0-9]{6}$/.test(level.password)) {
      const pwOff = 0x2938 + 8 * level.index + 1;
      for (let d = 0; d < 6; d++) {
        romBuffer[pwOff + d] = parseInt(level.password[d], 10);
      }
    }
    // Map Grid (440 bytes, low nibble first)
    const lvlOff = meta.level_offset;
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < 20; c++) {
        const t0 = level.grid[r][c * 2] & 0x0f;
        const t1 = level.grid[r][c * 2 + 1] & 0x0f;
        romBuffer[lvlOff + r * 20 + c] = t0 | (t1 << 4);
      }
    }
  }

  // Sync all 24 levels in allLevels into romBuffer
  function syncAllLevelsToRomBuffer() {
    if (!romBuffer) return;
    if (currentLevel) {
      allLevels[currentLevelIdx] = JSON.parse(JSON.stringify(currentLevel));
    }
    allLevels.forEach(lvl => syncLevelToRomBuffer(lvl));
  }

  // Parse all 24 levels from a loaded .nes ROM Uint8Array into allLevels
  function readLevelsFromRomBuffer(buf) {
    if (!buf) return;
    allLevels.forEach((meta, idx) => {
      meta.diamonds_needed = buf[meta.crystal_offset];
      meta.time_limit = buf[meta.time_offset];
      meta.start_x = buf[meta.start_x_offset];
      meta.start_y = buf[meta.start_y_offset];

      const pwOff = 0x2938 + 8 * idx + 1;
      const rawPw = [];
      let validDigits = true;
      for (let d = 0; d < 6; d++) {
        const digit = buf[pwOff + d];
        if (digit > 9) validDigits = false;
        rawPw.push(digit);
      }
      meta.password = validDigits ? rawPw.join('') : 'FINAL';

      const lvlOff = meta.level_offset;
      const grid = [];
      for (let r = 0; r < ROWS; r++) {
        const row = [];
        for (let c = 0; c < 20; c++) {
          const b = buf[lvlOff + r * 20 + c];
          row.push(b & 0x0f);
          row.push((b >> 4) & 0x0f);
        }
        grid.push(row);
      }
      meta.grid = grid;
    });
  }

  function uint8ToBase64(bytes) {
    let binary = '';
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  async function handleRomFileSelected(file) {
    if (!file) return;
    try {
      const ab = await file.arrayBuffer();
      const buf = new Uint8Array(ab);

      // Verify iNES header ("NES\x1a")
      if (buf.length < 32784 || buf[0] !== 0x4E || buf[1] !== 0x45 || buf[2] !== 0x53 || buf[3] !== 0x1A) {
        showToast('Invalid file: Please select a valid NES ROM (.nes) with an iNES header.', false, true);
        pendingExportAfterLoad = false;
        return;
      }

      romBuffer = new Uint8Array(buf);
      originalRomBuffer = new Uint8Array(buf);

      const wasPendingExport = pendingExportAfterLoad;
      pendingExportAfterLoad = false;

      if (wasPendingExport) {
        // User clicked Export ROM and selected their base Boulder Dash.nes to patch & download
        syncAllLevelsToRomBuffer();
        updateRomStatusIndicator();

        // Also upload to local server if running
        if (window.location.protocol.startsWith('http')) {
          fetch('/api/upload_rom', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rom_base64: uint8ToBase64(romBuffer), sync_existing_edits: true })
          }).catch(() => {});
        }

        triggerRomDownload();
      } else {
        // User clicked "Load ROM" — read all 24 caves from the selected ROM
        readLevelsFromRomBuffer(romBuffer);
        selectLevel(currentLevelIdx);
        updateRomStatusIndicator();

        if (window.location.protocol.startsWith('http')) {
          fetch('/api/upload_rom', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rom_base64: uint8ToBase64(romBuffer), sync_existing_edits: false })
          }).catch(() => {});
        }

        showToast(`Loaded "${file.name}" (${buf.length} bytes)!`, true);
      }
    } catch (err) {
      console.error('Error reading ROM file:', err);
      showToast('Failed to read ROM file.', false, true);
      pendingExportAfterLoad = false;
    }
  }

  // Event Listeners
  function setupEventListeners() {
    levelSelect.addEventListener('change', (e) => {
      selectLevel(parseInt(e.target.value, 10));
    });

    document.querySelectorAll('.tool-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const tool = btn.dataset.tool;
        setActiveTool(tool);
      });
    });

    function setActiveTool(tool) {
      activeTool = tool;
      document.querySelectorAll('.tool-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.tool === tool);
      });
    }

    document.getElementById('btnZoomIn').addEventListener('click', () => setZoom(zoom + 0.25));
    document.getElementById('btnZoomOut').addEventListener('click', () => setZoom(zoom - 0.25));
    document.getElementById('btnResetView').addEventListener('click', () => setZoom(2.0));
    document.getElementById('btnToggleGrid').addEventListener('click', () => {
      showGrid = !showGrid;
      renderGridLines();
    });

    document.getElementById('btnUndo').addEventListener('click', undo);
    document.getElementById('btnRedo').addEventListener('click', redo);

    const btnLoadRom = document.getElementById('btnLoadRom');
    if (btnLoadRom) {
      btnLoadRom.addEventListener('click', () => {
        pendingExportAfterLoad = false;
        fileInput.value = '';
        fileInput.click();
      });
    }

    fileInput.addEventListener('change', (e) => {
      const file = e.target.files && e.target.files[0];
      if (file) handleRomFileSelected(file);
    });

    document.getElementById('btnSave').addEventListener('click', saveCurrentLevel);
    document.getElementById('btnExport').addEventListener('click', exportRom);
    document.getElementById('btnRevert').addEventListener('click', revertROM);

    btnApplyProps.addEventListener('click', updateLevelProperties);

    document.getElementById('btnHelp').addEventListener('click', () => {
      helpModal.classList.add('open');
    });
    document.getElementById('btnCloseHelp').addEventListener('click', () => {
      helpModal.classList.remove('open');
    });

    document.getElementById('btnPlaytest').addEventListener('click', openPlaytestSimulator);
    document.getElementById('btnClosePlaytest').addEventListener('click', closePlaytestSimulator);
    document.getElementById('btnRestartSim').addEventListener('click', restartSimulator);
    document.getElementById('btnCopyPassword').addEventListener('click', () => {
      if (currentLevel) {
        navigator.clipboard.writeText(currentLevel.password);
        showToast(`Copied Password: ${currentLevel.password}`);
      }
    });

    // Canvas Interactions
    mapCanvas.addEventListener('mousedown', (e) => {
      if (!currentLevel) return;
      const { x, y } = getTileCoords(e);
      isDrawing = true;
      drawStartX = x;
      drawStartY = y;
      lastTileX = x;
      lastTileY = y;

      if (e.altKey || activeTool === 'picker') {
        const picked = currentLevel.grid[y][x];
        setActiveTile(picked);
        setActiveTool('pencil');
        isDrawing = false;
        return;
      }

      if (activeTool === 'spawn') {
        currentLevel.start_x = x;
        currentLevel.start_y = y;
        propStartX.value = x;
        propStartY.value = y;
        renderMap();
        updateDiagnostics();
        isDrawing = false;
        return;
      }

      if (activeTool === 'bucket') {
        const targetTile = currentLevel.grid[y][x];
        floodFill(x, y, targetTile, activeTile);
        isDrawing = false;
        return;
      }

      if (activeTool === 'pencil' || activeTool === 'eraser') {
        pushUndo();
        const tile = (activeTool === 'eraser') ? 0 : activeTile;
        currentLevel.grid[y][x] = tile;
        renderMap();
        updateDiagnostics();
      }
    });

    window.addEventListener('mousemove', (e) => {
      const rect = mapCanvas.getBoundingClientRect();
      const isOver = (
        e.clientX >= rect.left && e.clientX <= rect.right &&
        e.clientY >= rect.top && e.clientY <= rect.bottom
      );

      if (isOver) {
        const { x, y } = getTileCoords(e);
        statusCoord.textContent = `X: ${x}, Y: ${y}`;
        if (currentLevel) {
          const tId = currentLevel.grid[y][x];
          const worldTiles = tilesLibrary[currentLevel.tileset] || [];
          const tName = worldTiles[tId] ? worldTiles[tId].name : `Tile ${tId}`;
          statusTile.textContent = `Tile: ${tId} (${tName})`;
        }

        if (isDrawing) {
          if (activeTool === 'pencil' || activeTool === 'eraser') {
            if (x !== lastTileX || y !== lastTileY) {
              const tile = (activeTool === 'eraser') ? 0 : activeTile;
              const pts = getLinePoints(lastTileX, lastTileY, x, y);
              pts.forEach(([cx, cy]) => {
                currentLevel.grid[cy][cx] = tile;
              });
              lastTileX = x;
              lastTileY = y;
              renderMap();
              updateDiagnostics();
            }
          } else if (['rect-fill', 'rect-outline', 'line'].includes(activeTool)) {
            drawShapePreview(drawStartX, drawStartY, x, y);
          }
        } else {
          drawCursorPreview(x, y);
        }
      } else {
        if (!isDrawing) clearOverlay();
      }
    });

    window.addEventListener('mouseup', (e) => {
      if (isDrawing) {
        if (['rect-fill', 'rect-outline', 'line'].includes(activeTool)) {
          const { x, y } = getTileCoords(e);
          applyShape(drawStartX, drawStartY, x, y);
        }
        isDrawing = false;
        clearOverlay();
      }
    });

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

      const key = e.key.toLowerCase();

      if (e.ctrlKey || e.metaKey) {
        if (key === 'z') { e.preventDefault(); undo(); }
        else if (key === 'y') { e.preventDefault(); redo(); }
        else if (key === 's') { e.preventDefault(); saveCurrentLevel(); }
        return;
      }

      if (key === 'b') setActiveTool('pencil');
      else if (key === 'r') setActiveTool('rect-fill');
      else if (key === 'o') setActiveTool('rect-outline');
      else if (key === 'l') setActiveTool('line');
      else if (key === 'f') setActiveTool('bucket');
      else if (key === 'e') setActiveTool('eraser');
      else if (key === 'i') setActiveTool('picker');
      else if (key === 's') setActiveTool('spawn');
      else if (key === 'g') { showGrid = !showGrid; renderGridLines(); }
      else if (key === ' ') { e.preventDefault(); openPlaytestSimulator(); }
      else if (key >= '0' && key <= '9') {
        const num = parseInt(key, 10);
        setActiveTile(num);
      }
    });

    canvasContainer.addEventListener('wheel', (e) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        if (e.deltaY < 0) setZoom(zoom + 0.15);
        else setZoom(zoom - 0.15);
      }
    }, { passive: false });
  }

  // Diagnostics
  function updateDiagnostics() {
    if (!currentLevel) return;
    const grid = currentLevel.grid;

    let diamonds = 0;
    let rocks = 0;
    let dirt = 0;
    let fireflies = 0;
    let butterflies = 0;
    let amoebas = 0;
    let magicWalls = 0;
    let exitCount = 0;

    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const t = grid[r][c];
        if (t === 8 || t === 9) diamonds++;
        else if (t === 7) rocks++;
        else if (t === 2) dirt++;
        else if (t === 11) fireflies++;
        else if (t === 12) butterflies++;
        else if (t === 13 || t === 14) amoebas++;
        else if (t === 6) magicWalls++;
        else if (t === 4) exitCount++;
      }
    }

    const enemies = fireflies + butterflies;
    statDiamonds.textContent = diamonds;
    statRocks.textContent = rocks;
    statDirt.textContent = dirt;
    statEnemies.textContent = enemies;
    statAmoeba.textContent = amoebas;
    statExit.textContent = exitCount > 0 ? `${exitCount} Exit(s)` : 'MISSING';

    const needed = currentLevel.diamonds_needed;
    const statDiamondsWrap = document.getElementById('statDiamondsWrap');
    const statExitWrap = document.getElementById('statExitWrap');

    statAlert.style.display = 'none';

    const potentialDiamonds = diamonds + (butterflies * 9) + (amoebas > 0 ? 99 : 0) + (magicWalls > 0 ? rocks : 0);
    if (potentialDiamonds < needed) {
      statDiamondsWrap.classList.add('stat-danger');
      statAlert.style.display = 'block';
      statAlert.style.background = 'rgba(228, 0, 88, 0.2)';
      statAlert.style.color = '#ff6b8b';
      statAlert.style.border = '1px solid var(--accent-red)';
      statAlert.textContent = `⚠️ Warning: Map has only ${diamonds} diamonds, but cave requires ${needed}!`;
    } else {
      statDiamondsWrap.classList.remove('stat-danger');
    }

    if (exitCount === 0) {
      statExitWrap.classList.add('stat-danger');
      statAlert.style.display = 'block';
      statAlert.style.background = 'rgba(228, 0, 88, 0.2)';
      statAlert.style.color = '#ff6b8b';
      statAlert.style.border = '1px solid var(--accent-red)';
      statAlert.textContent = `⚠️ Critical: Cave has no Exit Door! Place Tile 4 (Exit Door) on map.`;
    } else {
      statExitWrap.classList.remove('stat-danger');
    }
  }

  // Update Properties
  function updateLevelProperties() {
    if (!currentLevel) return;
    const diamonds = Math.max(0, Math.min(99, parseInt(propDiamonds.value, 10) || 0));
    const timeLimit = Math.max(0, Math.min(255, parseInt(propTime.value, 10) || 0));
    const sx = Math.max(0, Math.min(COLS - 1, parseInt(propStartX.value, 10) || 0));
    const sy = Math.max(0, Math.min(ROWS - 1, parseInt(propStartY.value, 10) || 0));
    let pw = propPassword.value.trim();

    if (!/^[0-9]{6}$/.test(pw) && !(currentLevel.index === 23 && pw === 'FINAL')) {
      showToast('Password must be exactly 6 digits (0-9)', false, true);
      return;
    }

    currentLevel.diamonds_needed = diamonds;
    currentLevel.time_limit = timeLimit;
    currentLevel.start_x = sx;
    currentLevel.start_y = sy;
    currentLevel.password = pw;

    renderMap();
    updateDiagnostics();
    saveStatus.textContent = 'ROM: Unsaved changes';
    saveStatus.style.color = '#ffaa00';
    showToast('Level properties updated!');
  }

  // Save Level (Syncs ROM buffer and writes to server if available)
  async function saveCurrentLevel() {
    if (!currentLevel) return;
    updateLevelProperties();

    // 1. Sync in-memory level array & ROM buffer
    allLevels[currentLevelIdx] = JSON.parse(JSON.stringify(currentLevel));
    syncLevelToRomBuffer(currentLevel);

    // 2. If running with server, POST to backend
    if (window.location.protocol.startsWith('http')) {
      try {
        const res = await fetch('/api/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(currentLevel)
        });
        if (res.ok) {
          const data = await res.json();
          if (data.has_rom) {
            saveStatus.textContent = 'ROM: Synchronized on Disk';
            saveStatus.style.color = '#55ff55';
            showToast('Level saved to ROM file on disk!', true);
          } else {
            saveStatus.textContent = 'Saved in Session (Load ROM to Export)';
            saveStatus.style.color = '#38bdf8';
            showToast('Cave saved in session! Click "📂 Load ROM" or "⬇️ Export ROM" to patch a .nes file.', true);
          }
          return;
        }
      } catch (e) {}
    }

    if (romBuffer) {
      saveStatus.textContent = 'ROM: Ready (In-Memory)';
      saveStatus.style.color = '#55ff55';
      showToast('Level saved to in-memory ROM! Click Export ROM to download.', true);
    } else {
      saveStatus.textContent = 'Saved in Session (Load ROM to Export)';
      saveStatus.style.color = '#38bdf8';
      showToast('Cave saved in memory! Click "⬇️ Export ROM" and select your base Boulder Dash.nes file.', true);
    }
  }

  function triggerRomDownload() {
    if (!romBuffer) return;
    const blob = new Blob([romBuffer], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Boulder Dash (Edited).nes';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Downloaded Boulder Dash (Edited).nes!', true);
  }

  // Export / Download ROM directly
  function exportRom() {
    if (!currentLevel) return;
    updateLevelProperties();
    allLevels[currentLevelIdx] = JSON.parse(JSON.stringify(currentLevel));

    if (romBuffer) {
      syncAllLevelsToRomBuffer();
      triggerRomDownload();
    } else {
      pendingExportAfterLoad = true;
      showToast('Select your base Boulder Dash.nes ROM file to patch & export...', false);
      fileInput.value = '';
      fileInput.click();
    }
  }

  // Revert ROM to Backup
  async function revertROM() {
    if (!confirm('Revert all caves to original backup? All edits will be undone.')) return;

    if (window.location.protocol.startsWith('http')) {
      try {
        const res = await fetch('/api/revert', { method: 'POST' });
        if (res.ok) {
          const data = await res.json();
          allLevels = data.levels;
          if (originalRomBuffer) {
            romBuffer = new Uint8Array(originalRomBuffer);
          }
          selectLevel(currentLevelIdx);
          updateRomStatusIndicator();
          showToast('Reverted to original caves!', true);
          return;
        }
      } catch (e) {}
    }

    // Fallback in standalone / offline mode
    if (originalRomBuffer) {
      romBuffer = new Uint8Array(originalRomBuffer);
      readLevelsFromRomBuffer(romBuffer);
    } else if (window.DEFAULT_LEVELS_DUMP) {
      allLevels = JSON.parse(JSON.stringify(window.DEFAULT_LEVELS_DUMP.levels));
    }
    selectLevel(currentLevelIdx);
    updateRomStatusIndicator();
    showToast('Reverted to original caves!', true);
  }

  // Toast Helper
  let toastTimer = null;
  function showToast(msg, isSuccess = false, isError = false) {
    if (toastTimer) clearTimeout(toastTimer);
    toast.textContent = msg;
    toast.className = 'toast show';
    if (isSuccess) toast.classList.add('success');
    if (isError) toast.classList.add('error');

    toastTimer = setTimeout(() => {
      toast.className = 'toast';
    }, 2500);
  }

  // ==========================================
  // In-Browser Boulder Dash Physics Simulator
  // ==========================================
  let simRunning = false;
  let simGrid = [];
  let simFalling = [];
  let playerX = 3;
  let playerY = 2;
  let diamondsCollected = 0;
  let simTimeRemaining = 120;
  let simInterval = null;
  let timeInterval = null;
  let exitOpened = false;

  function openPlaytestSimulator() {
    if (!currentLevel) return;
    playtestModal.classList.add('open');
    initSimulator();
    window.addEventListener('keydown', handleSimInput);
  }

  function closePlaytestSimulator() {
    playtestModal.classList.remove('open');
    stopSimulator();
    window.removeEventListener('keydown', handleSimInput);
  }

  function restartSimulator() {
    initSimulator();
  }

  function initSimulator() {
    stopSimulator();
    simGrid = JSON.parse(JSON.stringify(currentLevel.grid));
    simFalling = Array.from({ length: ROWS }, () => new Uint8Array(COLS));
    playerX = currentLevel.start_x;
    playerY = currentLevel.start_y;
    diamondsCollected = 0;
    simTimeRemaining = currentLevel.time_limit;
    exitOpened = (diamondsCollected >= currentLevel.diamonds_needed);

    if (simGrid[playerY] && simGrid[playerY][playerX] !== 0) {
      simGrid[playerY][playerX] = 0;
    }

    hudNeed.textContent = currentLevel.diamonds_needed;
    hudGot.textContent = diamondsCollected;
    hudTime.textContent = simTimeRemaining;
    hudPassword.textContent = currentLevel.password;

    simRunning = true;
    renderSim();

    simInterval = setInterval(simPhysicsTick, 120);
    timeInterval = setInterval(() => {
      if (simTimeRemaining > 0) {
        simTimeRemaining--;
        hudTime.textContent = simTimeRemaining;
        if (simTimeRemaining === 0) {
          showToast('Time Expired! Cave collapsed.', false, true);
        }
      }
    }, 1000);
  }

  function stopSimulator() {
    simRunning = false;
    if (simInterval) clearInterval(simInterval);
    if (timeInterval) clearInterval(timeInterval);
    simInterval = null;
    timeInterval = null;
  }

  function handleSimInput(e) {
    if (!simRunning) return;
    let dx = 0;
    let dy = 0;

    if (e.key === 'ArrowUp' || e.key === 'w' || e.key === 'W') dy = -1;
    else if (e.key === 'ArrowDown' || e.key === 's' || e.key === 'S') dy = 1;
    else if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') dx = -1;
    else if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') dx = 1;
    else if (e.key === 'r' || e.key === 'R') { restartSimulator(); return; }
    else return;

    e.preventDefault();
    movePlayer(dx, dy);
  }

  function movePlayer(dx, dy) {
    const targetX = playerX + dx;
    const targetY = playerY + dy;

    if (targetX < 0 || targetX >= COLS || targetY < 0 || targetY >= ROWS) return;
    const targetTile = simGrid[targetY][targetX];

    // Empty space (0, 1, or 10 sparkle)
    if (targetTile === 0 || targetTile === 1 || targetTile === 10) {
      simGrid[targetY][targetX] = 0;
      simFalling[targetY][targetX] = 0;
      playerX = targetX;
      playerY = targetY;
    }
    // Dirt
    else if (targetTile === 2) {
      simGrid[targetY][targetX] = 0;
      simFalling[targetY][targetX] = 0;
      playerX = targetX;
      playerY = targetY;
    }
    // Diamond (8) or Diamond Sparkle (9)
    else if (targetTile === 8 || targetTile === 9) {
      simGrid[targetY][targetX] = 0;
      simFalling[targetY][targetX] = 0;
      diamondsCollected++;
      hudGot.textContent = diamondsCollected;
      playerX = targetX;
      playerY = targetY;

      if (diamondsCollected >= currentLevel.diamonds_needed && !exitOpened) {
        exitOpened = true;
        showToast('💎 Quota reached! Exit Door wall turned into a Portal!', true);
      }
    }
    // Rock push (Tile 7)
    else if (targetTile === 7 && dy === 0 && !simFalling[targetY][targetX]) {
      const rockDestX = targetX + dx;
      if (rockDestX >= 0 && rockDestX < COLS && simGrid[targetY][rockDestX] === 0) {
        simGrid[targetY][rockDestX] = 7;
        simFalling[targetY][rockDestX] = 0;
        simGrid[targetY][targetX] = 0;
        simFalling[targetY][targetX] = 0;
        playerX = targetX;
        playerY = targetY;
      }
    }
    // Open Exit Door Portal (Tile 4)
    else if (targetTile === 4 && exitOpened) {
      playerX = targetX;
      playerY = targetY;
      stopSimulator();
      showToast('🎉 CAVE COMPLETED! You escaped through the Portal!', true);
    }

    renderSim();
  }

  function triggerExplosion3x3(centerR, centerC, resultTile) {
    for (let dr = -1; dr <= 1; dr++) {
      for (let dc = -1; dc <= 1; dc++) {
        const nr = centerR + dr;
        const nc = centerC + dc;
        if (nr >= 0 && nr < ROWS && nc >= 0 && nc < COLS) {
          const t = simGrid[nr][nc];
          // Steel Wall (3) and Exit Door (4) are indestructible
          if (t !== 3 && t !== 4) {
            simGrid[nr][nc] = resultTile;
            simFalling[nr][nc] = 0;
          }
          if (playerX === nc && playerY === nr) {
            showToast('💥 BOOM! Caught in an explosion.', false, true);
            stopSimulator();
          }
        }
      }
    }
  }

  function simPhysicsTick() {
    if (!simRunning) return;
    let gridChanged = false;

    for (let r = ROWS - 2; r >= 0; r--) {
      for (let c = 0; c < COLS; c++) {
        const item = simGrid[r][c];

        // Sparkle transitions: 9 -> 8 (Diamond), 10 -> 0 (Empty Space)
        if (item === 9) {
          simGrid[r][c] = 8;
          simFalling[r][c] = 0;
          gridChanged = true;
          continue;
        }
        if (item === 10) {
          simGrid[r][c] = 0;
          simFalling[r][c] = 0;
          gridChanged = true;
          continue;
        }

        // Boulders (7) and Diamonds (8)
        if (item === 7 || item === 8) {
          const wasFalling = simFalling[r][c] === 1;
          const below = simGrid[r + 1][c];
          const playerBelow = (playerX === c && playerY === r + 1);

          // 1. Fall directly down
          if (below === 0 || below === 1) {
            if (playerBelow) {
              // Stationary boulders/diamonds stay held up while player stands directly below;
              // only already-falling boulders/diamonds crush the player on impact.
              if (wasFalling) {
                simGrid[r + 1][c] = item;
                simFalling[r + 1][c] = 1;
                simGrid[r][c] = 0;
                simFalling[r][c] = 0;
                gridChanged = true;
                showToast('💥 SQUASHED! A falling rock crushed Rockford.', false, true);
                stopSimulator();
              } else {
                simFalling[r][c] = 0;
              }
            } else {
              simGrid[r + 1][c] = item;
              simFalling[r + 1][c] = 1;
              simGrid[r][c] = 0;
              simFalling[r][c] = 0;
              gridChanged = true;
            }
          }
          // 2. Magic Wall (Tile 6) converts falling Boulders (7) into Diamonds (8)
          else if (item === 7 && below === 6) {
            simGrid[r][c] = 0;
            simFalling[r][c] = 0;
            if (r + 2 < ROWS && simGrid[r + 2][c] === 0) {
              simGrid[r + 2][c] = 8;
              simFalling[r + 2][c] = 1;
              if (playerX === c && playerY === r + 2) {
                showToast('💥 SQUASHED! A falling rock crushed Rockford.', false, true);
                stopSimulator();
              }
            }
            gridChanged = true;
          }
          // 3. Crush Firefly (Tile 11) -> 3x3 Space Explosion (Tile 10)
          else if (below === 11) {
            simGrid[r][c] = 0;
            simFalling[r][c] = 0;
            triggerExplosion3x3(r + 1, c, 10);
            gridChanged = true;
          }
          // 4. Crush Butterfly (Tile 12) -> 3x3 Diamond Explosion (Tile 9 -> 8)
          else if (below === 12) {
            simGrid[r][c] = 0;
            simFalling[r][c] = 0;
            triggerExplosion3x3(r + 1, c, 9);
            gridChanged = true;
          }
          // 5. Roll off rounded objects (only if supporting object is not currently falling)
          else if ((below === 7 || below === 8 || below === 5 || below === 6) && !simFalling[r + 1][c]) {
            const canRollLeft = (
              c > 0 &&
              simGrid[r][c - 1] === 0 &&
              simGrid[r + 1][c - 1] === 0 &&
              !(playerX === c - 1 && (playerY === r || playerY === r + 1))
            );
            const canRollRight = (
              c < COLS - 1 &&
              simGrid[r][c + 1] === 0 &&
              simGrid[r + 1][c + 1] === 0 &&
              !(playerX === c + 1 && (playerY === r || playerY === r + 1))
            );

            // Roll Left
            if (canRollLeft) {
              simGrid[r + 1][c - 1] = item;
              simFalling[r + 1][c - 1] = 1;
              simGrid[r][c] = 0;
              simFalling[r][c] = 0;
              gridChanged = true;
            }
            // Roll Right
            else if (canRollRight) {
              simGrid[r + 1][c + 1] = item;
              simFalling[r + 1][c + 1] = 1;
              simGrid[r][c] = 0;
              simFalling[r][c] = 0;
              gridChanged = true;
            } else {
              simFalling[r][c] = 0;
            }
          } else {
            simFalling[r][c] = 0;
          }
        }
      }
    }

    if (gridChanged) renderSim();
  }

  function renderSim() {
    const w = currentLevel.tileset;
    simCtx.fillStyle = '#000000';
    simCtx.fillRect(0, 0, MAP_W, MAP_H);

    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const tileId = simGrid[r][c];

        // Authentic NES Exit Door (Tile 4):
        // Renders as Wall until diamond quota is met, then turns into the Portal ($F3E0)
        if (tileId === 4 && exitOpened && portalImages[w]) {
          simCtx.drawImage(portalImages[w], c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE);
          continue;
        }

        const key = `${w}_${tileId}`;
        const img = tileImages[key];
        if (img) {
          simCtx.drawImage(img, c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        }
      }
    }

    // Draw Rockford
    const rx = playerX * TILE_SIZE;
    const ry = playerY * TILE_SIZE;
    if (rockfordImg && rockfordImg.complete) {
      simCtx.drawImage(rockfordImg, rx, ry, TILE_SIZE, TILE_SIZE);
    } else {
      simCtx.save();
      simCtx.fillStyle = '#e45c10';
      simCtx.beginPath();
      simCtx.arc(rx + 8, ry + 8, 6, 0, Math.PI * 2);
      simCtx.fill();

      simCtx.fillStyle = '#ffffff';
      simCtx.fillRect(rx + 5, ry + 5, 2, 3);
      simCtx.fillRect(rx + 9, ry + 5, 2, 3);
      simCtx.fillStyle = '#000000';
      simCtx.fillRect(rx + 6, ry + 6, 1, 2);
      simCtx.fillRect(rx + 10, ry + 6, 1, 2);
      simCtx.restore();
    }
  }

  window.addEventListener('DOMContentLoaded', init);
})();
