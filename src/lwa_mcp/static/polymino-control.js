const ROWS = 22;
const COLS = 10;
const HIDDEN_ROWS = 2;
const VISIBLE_ROWS = ROWS - HIDDEN_ROWS;

const boardCanvas = document.querySelector('#board');
const currentCanvas = document.querySelector('#currentPreview');
const nextCanvas = document.querySelector('#nextPreview');
const holdCanvas = document.querySelector('#holdPreview');

const sessionStateEl = document.querySelector('#sessionState');
const seedLabelEl = document.querySelector('#seedLabel');
const scoreEl = document.querySelector('#score');
const linesEl = document.querySelector('#lines');
const levelEl = document.querySelector('#level');
const dropRateEl = document.querySelector('#dropRate');
const speedLabelEl = document.querySelector('#speedLabel');
const statusEl = document.querySelector('#status');
const speedInput = document.querySelector('#speed');
const ghostInput = document.querySelector('#ghost');
const gridInput = document.querySelector('#showGrid');
const persistSeedEl = document.querySelector('#persistSeed');
const persistBestScoreEl = document.querySelector('#persistBestScore');
const persistLastScoreEl = document.querySelector('#persistLastScore');
const persistRunCountEl = document.querySelector('#persistRunCount');
const persistSummaryEl = document.querySelector('#persistSummary');
const seedInput = document.querySelector('#seedInput');
const applySeedButton = document.querySelector('#applySeed');
const exportSnapshotButton = document.querySelector('#exportSnapshot');
const importSnapshotButton = document.querySelector('#importSnapshot');
const snapshotFileInput = document.querySelector('#snapshotFile');
const actionLogEl = document.querySelector('#actionLog');
const clearLogButton = document.querySelector('#clearLog');

const buttons = {
  toggle: document.querySelector('#toggle'),
  step: document.querySelector('#step'),
  hold: document.querySelector('#hold'),
  drop: document.querySelector('#drop'),
  rotateLeft: document.querySelector('#rotateLeft'),
  rotateRight: document.querySelector('#rotateRight'),
  reset: document.querySelector('#reset'),
  shuffle: document.querySelector('#shuffle'),
};

const STORAGE_KEY = 'lwa-polymino-control:v1';
const SNAPSHOT_VERSION = 2;
const MAX_ACTION_LOG = 40;

const TONES = {
  gold: {
    light: '#fff0c6',
    mid: '#d9b25f',
    dark: '#785416',
    edge: '#51380d',
    glow: 'rgba(241, 203, 122, 0.35)',
  },
  silver: {
    light: '#f4f7fb',
    mid: '#c8d1de',
    dark: '#687384',
    edge: '#3f4955',
    glow: 'rgba(200, 209, 222, 0.3)',
  },
  platinum: {
    light: '#ffffff',
    mid: '#e8edf6',
    dark: '#8d96a9',
    edge: '#5a6170',
    glow: 'rgba(232, 237, 246, 0.28)',
  },
};

function toneForSize(size) {
  if (size <= 4) return 'gold';
  if (size <= 8) return 'silver';
  return 'platinum';
}

function readPersistedState() {
  try {
    if (!window.localStorage) return {};
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function readQuerySeed() {
  const value = new URLSearchParams(window.location.search).get('seed');
  if (value === null || !/^\d+$/.test(value)) return null;
  const seed = Number(value);
  return Number.isSafeInteger(seed) && seed <= 0xFFFFFFFF ? seed >>> 0 : null;
}

function writePersistedState(snapshot) {
  try {
    if (!window.localStorage) return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
  } catch {
    // Persistence is best-effort.
  }
}

function normalize(cells) {
  const minX = Math.min(...cells.map(([x]) => x));
  const minY = Math.min(...cells.map(([, y]) => y));
  return cells.map(([x, y]) => [x - minX, y - minY]);
}

function bounds(cells) {
  const maxX = Math.max(...cells.map(([x]) => x));
  const maxY = Math.max(...cells.map(([, y]) => y));
  return { width: maxX + 1, height: maxY + 1 };
}

function rotateCW(cells) {
  const { width } = bounds(cells);
  return normalize(cells.map(([x, y]) => [width - 1 - y, x]));
}

function uniqueOrientations(baseCells) {
  const states = [];
  let current = normalize(baseCells);
  for (let i = 0; i < 4; i += 1) {
    const signature = current.map(([x, y]) => `${x},${y}`).sort().join('|');
    if (!states.some((state) => state.signature === signature)) {
      states.push({ signature, cells: current });
    }
    current = rotateCW(current);
  }
  return states.map((state) => state.cells);
}

function makePiece(name, cells) {
  const normalized = normalize(cells);
  const orientations = uniqueOrientations(normalized);
  const size = normalized.length;
  return {
    name,
    size,
    tone: toneForSize(size),
    orientations,
  };
}

const PIECES = [
  makePiece('Monomino', [[0, 0]]),
  makePiece('Domino', [[0, 0], [1, 0]]),
  makePiece('I Triomino', [[0, 0], [1, 0], [2, 0]]),
  makePiece('T Tetromino', [[1, 0], [0, 1], [1, 1], [2, 1]]),
  makePiece('P Pentomino', [[0, 0], [1, 0], [0, 1], [1, 1], [0, 2]]),
  makePiece('L Hexomino', [[0, 0], [0, 1], [0, 2], [1, 2], [2, 2], [2, 1]]),
  makePiece('F Heptomino', [[0, 0], [0, 1], [1, 1], [1, 2], [2, 2], [2, 3], [3, 3]]),
  makePiece('U Octomino', [[1, 0], [0, 1], [1, 1], [2, 1], [1, 2], [1, 3], [2, 3], [3, 3]]),
  makePiece('X Nonomino', [[0, 1], [1, 0], [1, 1], [2, 1], [1, 2], [3, 1], [4, 1], [2, 2], [2, 3]]),
  makePiece('W Decomino', [[0, 0], [1, 0], [2, 0], [0, 1], [2, 1], [0, 2], [1, 2], [2, 2], [1, 3], [1, 4]]),
  makePiece('Y Undecomino', [[0, 0], [1, 0], [2, 0], [3, 0], [1, 1], [3, 1], [0, 2], [1, 2], [2, 2], [3, 2], [2, 3]]),
  makePiece('Z Duodecomino', [[0, 0], [1, 0], [2, 0], [3, 0], [0, 1], [3, 1], [0, 2], [1, 2], [2, 2], [3, 2], [1, 3], [2, 3]]),
  makePiece('V Tridecomino', [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0], [0, 1], [2, 1], [4, 1], [0, 2], [1, 2], [2, 2], [3, 2], [4, 2]]),
];

function createRng(seed) {
  let value = seed >>> 0;
  const rng = () => {
    value += 0x6D2B79F5;
    let t = value;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  rng.getState = () => value >>> 0;
  rng.setState = (nextValue) => {
    value = Number(nextValue) >>> 0;
  };
  return rng;
}

function shuffle(array, rng) {
  const next = array.slice();
  for (let i = next.length - 1; i > 0; i -= 1) {
    const j = Math.floor(rng() * (i + 1));
    [next[i], next[j]] = [next[j], next[i]];
  }
  return next;
}

function clonePiece(piece) {
  return {
    name: piece.name,
    size: piece.size,
    tone: piece.tone,
    orientations: piece.orientations.map((cells) => cells.map(([x, y]) => [x, y])),
  };
}

function pieceByName(name) {
  const definition = PIECES.find((piece) => piece.name === name);
  return definition ? clonePiece(definition) : null;
}

const state = {
  board: new Array(ROWS * COLS).fill(null),
  current: null,
  nextQueue: [],
  holdPiece: null,
  holdUsed: false,
  score: 0,
  lines: 0,
  level: 1,
  running: false,
  gameOver: false,
  runArchived: false,
  lastFrame: 0,
  accumulator: 0,
  speedMs: 850,
  showGhost: true,
  showGrid: true,
  seed: (Date.now() ^ (Math.random() * 0x7fffffff)) >>> 0,
  bestScore: 0,
  lastSavedScore: 0,
  lastSavedLines: 0,
  lastSavedLevel: 1,
  runHistory: [],
  actionLog: [],
};

const persisted = readPersistedState();
const querySeed = readQuerySeed();
state.speedMs = clamp(Number(persisted.speedMs ?? state.speedMs), 120, 1200);
state.showGhost = persisted.showGhost ?? state.showGhost;
state.showGrid = persisted.showGrid ?? state.showGrid;
state.seed = querySeed ?? (Number.isFinite(Number(persisted.seed)) ? Number(persisted.seed) >>> 0 : state.seed);
state.bestScore = Number(persisted.bestScore ?? 0) || 0;
state.lastSavedScore = Number(persisted.lastScore ?? persisted.score ?? 0) || 0;
state.lastSavedLines = Number(persisted.lastLines ?? persisted.lines ?? 0) || 0;
state.lastSavedLevel = Number(persisted.lastLevel ?? persisted.level ?? 1) || 1;
state.runHistory = Array.isArray(persisted.runHistory) ? persisted.runHistory.slice(0, 8) : [];
state.actionLog = Array.isArray(persisted.actionLog) ? persisted.actionLog.slice(0, MAX_ACTION_LOG) : [];

state.rng = createRng(state.seed);

const boardCtx = boardCanvas.getContext('2d');
const currentCtx = currentCanvas.getContext('2d');
const nextCtx = nextCanvas.getContext('2d');
const holdCtx = holdCanvas.getContext('2d');

function index(row, col) {
  return row * COLS + col;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function logAction(action, detail, channel = 'control') {
  const entry = {
    at: new Date().toISOString(),
    action,
    detail,
    channel,
  };
  state.actionLog = [entry, ...state.actionLog].slice(0, MAX_ACTION_LOG);
  renderActionLog();
  persistSession();
}

function renderActionLog() {
  actionLogEl.replaceChildren();
  if (!state.actionLog.length) {
    const empty = document.createElement('li');
    empty.textContent = 'No actions recorded yet.';
    actionLogEl.append(empty);
    return;
  }
  state.actionLog.forEach((entry) => {
    const item = document.createElement('li');
    const time = document.createElement('time');
    const date = new Date(entry.at);
    time.dateTime = entry.at;
    time.textContent = Number.isNaN(date.valueOf()) ? '--:--' : date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const text = document.createElement('span');
    const label = document.createElement('strong');
    label.textContent = `${entry.channel}: ${entry.action}`;
    text.append(label, ` ${entry.detail}`);
    item.append(time, text);
    actionLogEl.append(item);
  });
}

function serializePiece(piece) {
  if (!piece) return null;
  return { name: piece.name, size: piece.size, tone: piece.tone };
}

function serializeCurrent() {
  if (!state.current) return null;
  return {
    piece: serializePiece(state.current.piece),
    x: state.current.x,
    y: state.current.y,
    rotation: state.current.rotation,
  };
}

function buildSnapshot() {
  return {
    snapshot_version: SNAPSHOT_VERSION,
    control: 'lwa-polymino-control',
    created_at: new Date().toISOString(),
    seed: state.seed,
    rng_state: state.rng.getState(),
    board: state.board.map((piece) => piece?.name || null),
    current: serializeCurrent(),
    next_queue: state.nextQueue.map(serializePiece),
    hold_piece: serializePiece(state.holdPiece),
    hold_used: state.holdUsed,
    score: state.score,
    lines: state.lines,
    level: state.level,
    running: state.running,
    game_over: state.gameOver,
    speed_ms: state.speedMs,
    show_ghost: state.showGhost,
    show_grid: state.showGrid,
    best_score: state.bestScore,
    run_history: state.runHistory,
    action_log: state.actionLog,
  };
}

function restoreSnapshot(snapshot) {
  if (!snapshot || snapshot.control !== 'lwa-polymino-control' || snapshot.snapshot_version !== SNAPSHOT_VERSION) {
    throw new Error(`Unsupported snapshot version for ${snapshot?.control || 'unknown control'}.`);
  }
  if (!Array.isArray(snapshot.board) || snapshot.board.length !== ROWS * COLS) {
    throw new Error('Snapshot board dimensions do not match the control.');
  }
  const currentPiece = snapshot.current?.piece ? pieceByName(snapshot.current.piece.name) : null;
  const nextQueue = (snapshot.next_queue || []).map((piece) => pieceByName(piece?.name));
  const holdPiece = snapshot.hold_piece ? pieceByName(snapshot.hold_piece.name) : null;
  if (nextQueue.some((piece) => !piece) || (snapshot.current && !currentPiece) || (snapshot.hold_piece && !holdPiece)) {
    throw new Error('Snapshot contains an unknown polymino family.');
  }
  state.seed = Number(snapshot.seed) >>> 0;
  state.rng = createRng(state.seed);
  state.rng.setState(snapshot.rng_state ?? state.seed);
  state.board = snapshot.board.map((name) => name ? pieceByName(name) : null);
  if (state.board.some((piece, index) => snapshot.board[index] && !piece)) {
    throw new Error('Snapshot contains an unknown board piece.');
  }
  state.current = currentPiece ? {
    piece: currentPiece,
    x: Number(snapshot.current.x),
    y: Number(snapshot.current.y),
    rotation: Number(snapshot.current.rotation) % currentPiece.orientations.length,
  } : null;
  state.nextQueue = nextQueue;
  state.holdPiece = holdPiece;
  state.holdUsed = Boolean(snapshot.hold_used);
  state.score = Math.max(0, Number(snapshot.score) || 0);
  state.lines = Math.max(0, Number(snapshot.lines) || 0);
  state.level = Math.max(1, Number(snapshot.level) || 1);
  state.running = Boolean(snapshot.running);
  state.gameOver = Boolean(snapshot.game_over);
  state.runArchived = false;
  state.speedMs = clamp(Number(snapshot.speed_ms) || 850, 120, 1200);
  state.showGhost = snapshot.show_ghost !== false;
  state.showGrid = snapshot.show_grid !== false;
  state.bestScore = Math.max(Number(snapshot.best_score) || 0, state.score);
  state.runHistory = Array.isArray(snapshot.run_history) ? snapshot.run_history.slice(0, 8) : [];
  state.actionLog = Array.isArray(snapshot.action_log) ? snapshot.action_log.slice(0, MAX_ACTION_LOG) : [];
  state.accumulator = 0;
  state.lastFrame = 0;
  speedInput.value = String(state.speedMs);
  ghostInput.checked = state.showGhost;
  gridInput.checked = state.showGrid;
  seedInput.value = String(state.seed);
  updateHud('Snapshot imported. The run is ready for deterministic replay.');
  updateHudMetrics();
  updatePreviews();
  draw();
  persistSession();
  logAction('snapshot_imported', `seed ${state.seed}`, 'mcp');
}

function inBounds(row, col) {
  return row >= 0 && row < ROWS && col >= 0 && col < COLS;
}

function dropInterval() {
  return Math.max(120, state.speedMs - (state.level - 1) * 55);
}

function currentCells(piece = state.current) {
  if (!piece) return [];
  return piece.piece.orientations[piece.rotation];
}

function pieceBounds(piece = state.current) {
  return bounds(currentCells(piece));
}

function drawQueuePiece() {
  if (state.nextQueue.length < 4) {
    const bag = shuffle(PIECES.map(clonePiece), state.rng);
    state.nextQueue.push(...bag);
  }
}

function takeNextPiece() {
  drawQueuePiece();
  return state.nextQueue.shift();
}

function collides(piece, dx = 0, dy = 0, rotation = piece.rotation) {
  const cells = piece.piece.orientations[rotation];
  for (const [cellX, cellY] of cells) {
    const x = piece.x + dx + cellX;
    const y = piece.y + dy + cellY;
    if (x < 0 || x >= COLS || y >= ROWS) return true;
    if (y >= 0 && state.board[index(y, x)]) return true;
  }
  return false;
}

function createSpawnPosition(pieceDef) {
  const { width } = bounds(pieceDef.orientations[0]);
  return {
    x: Math.floor((COLS - width) / 2),
    y: -2,
  };
}

function spawnPiece(pieceDef = takeNextPiece(), options = {}) {
  const spawn = createSpawnPosition(pieceDef);
  state.current = { piece: pieceDef, x: spawn.x, y: spawn.y, rotation: 0 };
  if (!options.fromHold) {
    state.holdUsed = false;
  }
  if (collides(state.current)) {
    state.running = false;
    state.gameOver = true;
    buttons.toggle.textContent = 'Restart';
    buttons.toggle.setAttribute('aria-pressed', 'false');
    archiveRun('game-over');
    stateMessage(`Game over at score ${state.score}. Reset to try a new seed.`);
  } else {
    updateHud(`New ${pieceDef.name.toLowerCase()} entered the stack.`);
  }
  updatePreviews();
}

function placeCurrent() {
  const cells = currentCells();
  for (const [cellX, cellY] of cells) {
    const x = state.current.x + cellX;
    const y = state.current.y + cellY;
    if (y >= 0 && inBounds(y, x)) {
      state.board[index(y, x)] = state.current.piece;
    }
  }
}

function clearLines() {
  let cleared = 0;
  for (let row = ROWS - 1; row >= 0; row -= 1) {
    let full = true;
    for (let col = 0; col < COLS; col += 1) {
      if (!state.board[index(row, col)]) {
        full = false;
        break;
      }
    }
    if (full) {
      cleared += 1;
      for (let pull = row; pull > 0; pull -= 1) {
        for (let col = 0; col < COLS; col += 1) {
          state.board[index(pull, col)] = state.board[index(pull - 1, col)];
        }
      }
      for (let col = 0; col < COLS; col += 1) {
        state.board[index(0, col)] = null;
      }
      row += 1;
    }
  }
  if (cleared > 0) {
    state.lines += cleared;
    const lineBonus = [0, 120, 320, 700, 1200][cleared] || cleared * 320;
    state.score += lineBonus * state.level;
    state.level = 1 + Math.floor(state.lines / 10);
    stateMessage(`${cleared} line${cleared === 1 ? '' : 's'} cleared. The stack is more expensive now.`);
  }
  return cleared;
}

function lockPiece() {
  placeCurrent();
  const gained = state.current.piece.size * 10;
  state.score += gained;
  const cleared = clearLines();
  if (!cleared) {
    updateHud(`${state.current.piece.name} locked in for +${gained} points.`);
  }
  state.runArchived = false;
  persistSession();
  spawnPiece();
}

function move(dx, dy) {
  if (!state.current || state.gameOver) return false;
  if (!collides(state.current, dx, dy)) {
    state.current.x += dx;
    state.current.y += dy;
    updatePreviews();
    return true;
  }
  return false;
}

function rotate(direction) {
  if (!state.current || state.gameOver) return false;
  const total = state.current.piece.orientations.length;
  const nextRotation = (state.current.rotation + direction + total) % total;
  const kicks = [
    [0, 0],
    [-1, 0],
    [1, 0],
    [-2, 0],
    [2, 0],
    [0, -1],
    [0, -2],
  ];
  for (const [dx, dy] of kicks) {
    if (!collides(state.current, dx, dy, nextRotation)) {
      state.current.x += dx;
      state.current.y += dy;
      state.current.rotation = nextRotation;
      updatePreviews();
      return true;
    }
  }
  return false;
}

function softDrop() {
  if (!move(0, 1)) {
    if (state.current && !state.gameOver) lockPiece();
    return false;
  }
  state.score += 1;
  persistSession();
  return true;
}

function hardDrop() {
  if (!state.current || state.gameOver) return;
  let distance = 0;
  while (move(0, 1)) distance += 1;
  state.score += distance * 2;
  lockPiece();
  updateHud(`Hard drop landed after ${distance} rows.`);
  persistSession();
}

function hold() {
  if (!state.current || state.gameOver || state.holdUsed) return;
  const currentPiece = state.current.piece;
  if (!state.holdPiece) {
    state.holdPiece = clonePiece(currentPiece);
    spawnPiece();
  } else {
    const swap = state.holdPiece;
    state.holdPiece = clonePiece(currentPiece);
    state.current = null;
    spawnPiece(clonePiece(swap), { fromHold: true });
  }
  state.holdUsed = true;
  updateHud(`Hold used with ${currentPiece.name}.`);
  persistSession();
  updatePreviews();
}

function archiveRun(reason) {
  if (state.runArchived || (!state.score && !state.lines)) return;
  const entry = {
    seed: state.seed,
    score: state.score,
    lines: state.lines,
    level: state.level,
    reason,
    ended_at: new Date().toISOString(),
  };
  state.runHistory = [entry, ...state.runHistory].slice(0, 8);
  state.bestScore = Math.max(state.bestScore, state.score);
  state.runArchived = true;
  persistSession();
}

function persistSession() {
  state.bestScore = Math.max(state.bestScore, state.score);
  state.lastSavedScore = state.score;
  state.lastSavedLines = state.lines;
  state.lastSavedLevel = state.level;
  writePersistedState({
    version: SNAPSHOT_VERSION,
    seed: state.seed,
    score: state.score,
    lines: state.lines,
    level: state.level,
    bestScore: state.bestScore,
    lastScore: state.lastSavedScore,
    lastLines: state.lastSavedLines,
    lastLevel: state.lastSavedLevel,
    speedMs: state.speedMs,
    showGhost: state.showGhost,
    showGrid: state.showGrid,
    runHistory: state.runHistory,
    actionLog: state.actionLog,
    updatedAt: new Date().toISOString(),
  });
  updatePersistencePanel();
}

function updatePersistencePanel() {
  persistSeedEl.textContent = String(state.seed);
  persistBestScoreEl.textContent = String(state.bestScore);
  persistLastScoreEl.textContent = String(state.lastSavedScore);
  persistRunCountEl.textContent = String(state.runHistory.length);
  persistSummaryEl.textContent = state.runHistory[0]
    ? `Last saved run: seed ${state.runHistory[0].seed}, ${state.runHistory[0].score} points, ${state.runHistory[0].lines} lines.`
    : 'The current seed, score, level, and control flags are stored locally for repeatable runs.';
  renderActionLog();
}

function reset(seed = state.seed, { archive = true, persist = true } = {}) {
  if (archive) {
    archiveRun('reset');
  }
  state.seed = seed >>> 0;
  state.rng = createRng(state.seed);
  state.board.fill(null);
  state.nextQueue = [];
  state.holdPiece = null;
  state.holdUsed = false;
  state.score = 0;
  state.lines = 0;
  state.level = 1;
  state.running = false;
  state.gameOver = false;
  state.runArchived = false;
  state.accumulator = 0;
  state.lastFrame = 0;
  buttons.toggle.textContent = 'Start';
  buttons.toggle.setAttribute('aria-pressed', 'false');
  drawQueuePiece();
  drawQueuePiece();
  spawnPiece();
  seedLabelEl.textContent = `Seed: ${state.seed}`;
  updateHud('Fresh stack ready. Use the control surface or keyboard.');
  updateHudMetrics();
  updatePreviews();
  draw();
  if (persist) {
    persistSession();
  }
}

function applySeed() {
  const value = Number(seedInput.value);
  if (!Number.isSafeInteger(value) || value < 0 || value > 0xFFFFFFFF) {
    updateHud('Enter an integer seed from 0 to 4294967295.');
    return;
  }
  logAction('seed_applied', `seed ${value}`, 'plugin');
  reset(value);
}

function exportSnapshot() {
  const snapshot = buildSnapshot();
  const blob = new Blob([JSON.stringify(snapshot, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `lwa-polymino-${state.seed}-${Date.now()}.json`;
  link.click();
  URL.revokeObjectURL(url);
  logAction('snapshot_exported', `seed ${state.seed}, score ${state.score}`, 'mcp');
  updateHud('Snapshot exported. Use the JSON file as a CI-style fixture.');
}

function importSnapshotFile(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.addEventListener('load', () => {
    try {
      restoreSnapshot(JSON.parse(String(reader.result)));
    } catch (error) {
      updateHud(`Snapshot import failed: ${error.message}`);
      logAction('snapshot_import_failed', error.message, 'mcp');
    } finally {
      snapshotFileInput.value = '';
    }
  });
  reader.readAsText(file);
}

function updateHud(message) {
  statusEl.textContent = message;
}

function stateMessage(message) {
  sessionStateEl.textContent = message;
}

function updateHudMetrics() {
  scoreEl.textContent = String(state.score);
  linesEl.textContent = String(state.lines);
  levelEl.textContent = String(state.level);
  dropRateEl.textContent = `${(dropInterval() / 1000).toFixed(1)}s`;
  speedLabelEl.textContent = `${(state.speedMs / 1000).toFixed(1)} seconds per drop`;
  seedLabelEl.textContent = `Seed: ${state.seed}`;
  buttons.toggle.textContent = state.running ? 'Pause' : (state.gameOver ? 'Restart' : 'Start');
  buttons.toggle.setAttribute('aria-pressed', String(state.running));
  persistSeedEl.textContent = String(state.seed);
  persistBestScoreEl.textContent = String(state.bestScore);
  persistLastScoreEl.textContent = String(state.lastSavedScore);
  persistRunCountEl.textContent = String(state.runHistory.length);
  seedInput.value = String(state.seed);
}

function drawRoundedCell(ctx, x, y, size, tone, strength = 1) {
  const palette = TONES[tone];
  const radius = Math.max(5, size * 0.18);
  const inset = Math.max(2, size * 0.08);
  const light = ctx.createLinearGradient(x, y, x + size, y + size);
  light.addColorStop(0, palette.light);
  light.addColorStop(0.45, palette.mid);
  light.addColorStop(1, palette.dark);
  ctx.save();
  ctx.shadowColor = palette.glow;
  ctx.shadowBlur = Math.max(8, size * 0.28) * strength;
  ctx.fillStyle = light;
  roundRect(ctx, x + inset, y + inset, size - inset * 2, size - inset * 2, radius);
  ctx.fill();
  ctx.shadowBlur = 0;
  ctx.lineWidth = Math.max(1, size * 0.04);
  ctx.strokeStyle = palette.edge;
  ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,0.28)';
  roundRect(ctx, x + inset * 1.8, y + inset * 1.8, size * 0.42, size * 0.18, radius / 2);
  ctx.fill();
  ctx.restore();
}

function roundRect(ctx, x, y, width, height, radius) {
  const r = Math.min(radius, width / 2, height / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + width, y, x + width, y + height, r);
  ctx.arcTo(x + width, y + height, x, y + height, r);
  ctx.arcTo(x, y + height, x, y, r);
  ctx.arcTo(x, y, x + width, y, r);
  ctx.closePath();
}

function drawCanvas(ctx, canvas, piece = null) {
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(rect.width * dpr));
  canvas.height = Math.max(1, Math.floor(rect.height * dpr));
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, rect.width, rect.height);

  const cellSize = Math.min((rect.width - 24) / COLS, (rect.height - 24) / VISIBLE_ROWS);
  const boardWidth = cellSize * COLS;
  const boardHeight = cellSize * VISIBLE_ROWS;
  const offsetX = (rect.width - boardWidth) / 2;
  const offsetY = (rect.height - boardHeight) / 2;

  if (canvas === boardCanvas) {
    ctx.save();
    ctx.fillStyle = 'rgba(255,255,255,0.03)';
    roundRect(ctx, offsetX - 2, offsetY - 2, boardWidth + 4, boardHeight + 4, 22);
    ctx.fill();
    ctx.restore();
  }

  if (canvas === boardCanvas && state.showGrid) {
    ctx.save();
    ctx.strokeStyle = 'rgba(255,255,255,0.04)';
    ctx.lineWidth = 1;
    for (let col = 0; col <= COLS; col += 1) {
      ctx.beginPath();
      ctx.moveTo(offsetX + col * cellSize, offsetY);
      ctx.lineTo(offsetX + col * cellSize, offsetY + boardHeight);
      ctx.stroke();
    }
    for (let row = 0; row <= VISIBLE_ROWS; row += 1) {
      ctx.beginPath();
      ctx.moveTo(offsetX, offsetY + row * cellSize);
      ctx.lineTo(offsetX + boardWidth, offsetY + row * cellSize);
      ctx.stroke();
    }
    ctx.restore();
  }

  if (canvas === boardCanvas) {
    for (let row = HIDDEN_ROWS; row < ROWS; row += 1) {
      for (let col = 0; col < COLS; col += 1) {
        const cell = state.board[index(row, col)];
        if (!cell) continue;
        const tone = cell.tone;
        drawRoundedCell(
          ctx,
          offsetX + col * cellSize,
          offsetY + (row - HIDDEN_ROWS) * cellSize,
          cellSize,
          tone,
          1
        );
      }
    }

    if (state.current) {
      const cells = currentCells();
      const landing = state.showGhost ? ghostY() : 0;
      for (const [cellX, cellY] of cells) {
        const x = state.current.x + cellX;
        const y = state.current.y + cellY;
        if (x < 0 || x >= COLS || y < HIDDEN_ROWS || y >= ROWS) continue;
        if (state.showGhost) {
          const ghostRow = y + landing;
          if (ghostRow >= HIDDEN_ROWS && ghostRow < ROWS) {
            ctx.save();
            ctx.globalAlpha = 0.25;
            drawRoundedCell(
              ctx,
              offsetX + x * cellSize,
              offsetY + (ghostRow - HIDDEN_ROWS) * cellSize,
              cellSize,
              state.current.piece.tone,
              0.7
            );
            ctx.restore();
          }
        }
        drawRoundedCell(
          ctx,
          offsetX + x * cellSize,
          offsetY + (y - HIDDEN_ROWS) * cellSize,
          cellSize,
          state.current.piece.tone,
          1.15
        );
      }
    }

    if (state.gameOver) {
      ctx.save();
      ctx.fillStyle = 'rgba(8, 10, 14, 0.56)';
      ctx.fillRect(offsetX, offsetY, boardWidth, boardHeight);
      ctx.fillStyle = '#fff0c6';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.font = '700 30px "Segoe UI", system-ui, sans-serif';
      ctx.fillText('GAME OVER', rect.width / 2, rect.height / 2 - 16);
      ctx.font = '500 14px "Segoe UI", system-ui, sans-serif';
      ctx.fillStyle = 'rgba(245, 243, 239, 0.9)';
      ctx.fillText('Press Reset to reseed the stack.', rect.width / 2, rect.height / 2 + 18);
      ctx.restore();
    }
  } else {
    drawPreviewPiece(ctx, rect, piece);
  }
}

function ghostY() {
  if (!state.showGhost || !state.current) return 0;
  let distance = 0;
  while (!collides(state.current, 0, distance + 1)) {
    distance += 1;
  }
  return distance;
}

function drawPreviewPiece(ctx, rect, piece) {
  ctx.save();
  const cells = piece ? piece.orientations[0] : [];
  const box = cells.length ? bounds(cells) : { width: 1, height: 1 };
  const cellSize = Math.min((rect.width - 20) / 6, (rect.height - 20) / 6);
  const originX = (rect.width - box.width * cellSize) / 2;
  const originY = (rect.height - box.height * cellSize) / 2;
  ctx.fillStyle = 'rgba(255,255,255,0.025)';
  ctx.fillRect(0, 0, rect.width, rect.height);
  if (piece) {
    cells.forEach(([cellX, cellY]) => {
      drawRoundedCell(
        ctx,
        originX + cellX * cellSize,
        originY + cellY * cellSize,
        cellSize,
        piece.tone,
        0.9
      );
    });
  } else {
    ctx.fillStyle = 'rgba(245,243,239,0.55)';
    ctx.font = '600 13px "Segoe UI", system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('empty', rect.width / 2, rect.height / 2);
  }
  ctx.restore();
}

function updatePreviews() {
  drawCanvas(currentCtx, currentCanvas, state.current?.piece || null);
  drawCanvas(nextCtx, nextCanvas, state.nextQueue[0] || null);
  drawCanvas(holdCtx, holdCanvas, state.holdPiece || null);
}

function draw() {
  drawCanvas(boardCtx, boardCanvas);
}

function frame(timestamp) {
  if (!state.lastFrame) state.lastFrame = timestamp;
  const delta = timestamp - state.lastFrame;
  state.lastFrame = timestamp;
  if (state.running && !state.gameOver) {
    state.accumulator += delta;
    const interval = dropInterval();
    while (state.accumulator >= interval) {
      state.accumulator -= interval;
      if (!softDrop()) break;
    }
  }
  updateHudMetrics();
  draw();
  requestAnimationFrame(frame);
}

function toggleRun() {
  if (state.gameOver) {
    reset(state.seed, { archive: false });
  }
  state.running = !state.running;
  buttons.toggle.textContent = state.running ? 'Pause' : 'Start';
  buttons.toggle.setAttribute('aria-pressed', String(state.running));
  stateMessage(state.running ? 'Session running.' : 'Session paused.');
  persistSession();
}

function reseed() {
  const nextSeed = (Date.now() ^ (Math.random() * 0x7fffffff)) >>> 0;
  reset(nextSeed);
}

function keyTargetIsEditable(target) {
  return target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement;
}

window.addEventListener('keydown', (event) => {
  if (keyTargetIsEditable(event.target) && event.target !== boardCanvas) return;
  if (!state.current) return;
  switch (event.key) {
    case 'ArrowLeft':
      event.preventDefault();
      logAction('move_left', 'keyboard input', 'plugin');
      move(-1, 0);
      break;
    case 'ArrowRight':
      event.preventDefault();
      logAction('move_right', 'keyboard input', 'plugin');
      move(1, 0);
      break;
    case 'ArrowDown':
      event.preventDefault();
      logAction('soft_drop', 'keyboard input', 'plugin');
      softDrop();
      break;
    case 'ArrowUp':
    case 'x':
    case 'X':
      event.preventDefault();
      logAction('rotate_right', 'keyboard input', 'plugin');
      rotate(1);
      break;
    case 'z':
    case 'Z':
      event.preventDefault();
      logAction('rotate_left', 'keyboard input', 'plugin');
      rotate(-1);
      break;
    case ' ':
      event.preventDefault();
      logAction('hard_drop', 'keyboard input', 'plugin');
      hardDrop();
      break;
    case 'Shift':
      event.preventDefault();
      logAction('hold', 'keyboard input', 'plugin');
      hold();
      break;
    case 'p':
    case 'P':
      event.preventDefault();
      logAction('toggle_run', 'keyboard input', 'mcp');
      toggleRun();
      break;
    case 'r':
    case 'R':
      event.preventDefault();
      logAction('reset', 'keyboard input', 'mcp');
      reset(state.seed);
      break;
    case 'Enter':
      event.preventDefault();
      logAction('soft_drop', 'keyboard input', 'plugin');
      softDrop();
      break;
    default:
      break;
  }
});

buttons.toggle.addEventListener('click', () => { logAction('toggle_run', 'button input', 'mcp'); toggleRun(); });
buttons.step.addEventListener('click', () => {
  logAction('step', 'soft drop requested', 'plugin');
  if (!state.gameOver) softDrop();
});
buttons.hold.addEventListener('click', () => { logAction('hold', 'hold requested', 'plugin'); hold(); });
buttons.drop.addEventListener('click', () => { logAction('hard_drop', 'hard drop requested', 'plugin'); hardDrop(); });
buttons.rotateLeft.addEventListener('click', () => { logAction('rotate_left', 'rotation requested', 'plugin'); rotate(-1); });
buttons.rotateRight.addEventListener('click', () => { logAction('rotate_right', 'rotation requested', 'plugin'); rotate(1); });
buttons.reset.addEventListener('click', () => { logAction('reset', `seed ${state.seed}`, 'mcp'); reset(state.seed); });
buttons.shuffle.addEventListener('click', () => { logAction('reseed', 'new random seed requested', 'mcp'); reseed(); });
applySeedButton.addEventListener('click', applySeed);
exportSnapshotButton.addEventListener('click', exportSnapshot);
importSnapshotButton.addEventListener('click', () => snapshotFileInput.click());
snapshotFileInput.addEventListener('change', () => importSnapshotFile(snapshotFileInput.files[0]));
clearLogButton.addEventListener('click', () => {
  state.actionLog = [];
  persistSession();
  logAction('log_cleared', 'operator cleared the local trace', 'mcp');
});
speedInput.addEventListener('input', () => {
  state.speedMs = Number(speedInput.value);
  updateHudMetrics();
  persistSession();
});
ghostInput.addEventListener('change', () => {
  state.showGhost = ghostInput.checked;
  draw();
  persistSession();
});
gridInput.addEventListener('change', () => {
  state.showGrid = gridInput.checked;
  draw();
  persistSession();
});
boardCanvas.addEventListener('click', () => boardCanvas.focus());
window.addEventListener('resize', () => {
  draw();
  updatePreviews();
});

speedInput.value = String(state.speedMs);
ghostInput.checked = state.showGhost;
gridInput.checked = state.showGrid;
seedInput.value = String(state.seed);
reset(state.seed, { archive: false, persist: false });
renderActionLog();
logAction('control_loaded', `seed ${state.seed}${querySeed === null ? '' : ' from query string'}`, 'mcp');
window.__polyminoControlTest = {
  buildSnapshot,
  restoreSnapshot,
  getState: () => ({
    seed: state.seed,
    score: state.score,
    lines: state.lines,
    level: state.level,
    current: serializeCurrent(),
    nextQueue: state.nextQueue.map(serializePiece),
    actionLog: state.actionLog.slice(),
  }),
};
requestAnimationFrame(frame);
