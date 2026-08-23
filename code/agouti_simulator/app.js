const ROWS = 16;
const COLS = 24;
const CAT = '🐈';
const canvas = document.querySelector('#life-board');
const ctx = canvas.getContext('2d');
const generationEl = document.querySelector('#generation');
const liveCountEl = document.querySelector('#live-count');
const statusEl = document.querySelector('#status');
const speedInput = document.querySelector('#speed');
const speedValue = document.querySelector('#speed-value');
const wrapInput = document.querySelector('#wrap');
let cells = new Uint8Array(ROWS * COLS);
let generation = 0;
let selected = { row: 7, col: 12 };
let running = false;
let lastTick = 0;
let frame = 0;

const index = (row, col) => row * COLS + col;
const inBounds = (row, col) => row >= 0 && row < ROWS && col >= 0 && col < COLS;
function neighbors(row, col) {
  let count = 0;
  for (let dr = -1; dr <= 1; dr += 1) for (let dc = -1; dc <= 1; dc += 1) {
    if (!dr && !dc) continue;
    let nr = row + dr; let nc = col + dc;
    if (wrapInput.checked) { nr = (nr + ROWS) % ROWS; nc = (nc + COLS) % COLS; }
    if (inBounds(nr, nc)) count += cells[index(nr, nc)];
  }
  return count;
}
function step() {
  const next = new Uint8Array(cells.length);
  for (let row = 0; row < ROWS; row++) for (let col = 0; col < COLS; col++) {
    const alive = cells[index(row, col)] === 1; const count = neighbors(row, col);
    next[index(row, col)] = (alive && (count === 2 || count === 3)) || (!alive && count === 3) ? 1 : 0;
  }
  cells = next; generation += 1; announce(`Generation ${generation}. ${liveCount()} cats are alive.`); draw();
}
function liveCount() { return cells.reduce((sum, cell) => sum + cell, 0); }
function announce(message) { statusEl.textContent = message; generationEl.textContent = generation; liveCountEl.textContent = `${liveCount()} ${liveCount() === 1 ? 'cat' : 'cats'} alive`; }
function project(row, col, size) { return { x: (col - row) * size / 2, y: (col + row) * size / 4 }; }
function drawDiamond(x, y, size, fill, stroke) { ctx.beginPath(); ctx.moveTo(x, y - size / 4); ctx.lineTo(x + size / 2, y); ctx.lineTo(x, y + size / 4); ctx.lineTo(x - size / 2, y); ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); ctx.strokeStyle = stroke; ctx.stroke(); }
function draw() {
  const dpr = window.devicePixelRatio || 1; const rect = canvas.getBoundingClientRect(); canvas.width = rect.width * dpr; canvas.height = rect.height * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const size = Math.min(rect.width / (COLS * .52), rect.height / (ROWS * .29)); const origin = { x: rect.width / 2, y: rect.height * .47 };
  ctx.clearRect(0, 0, rect.width, rect.height);
  for (let row = 0; row < ROWS; row++) for (let col = 0; col < COLS; col++) {
    const point = project(row, col, size); const x = origin.x + point.x; const y = origin.y + point.y - (ROWS + COLS) * size / 8;
    const isSelected = selected.row === row && selected.col === col;
    drawDiamond(x, y, size, cells[index(row, col)] ? 'rgba(167,243,208,.14)' : 'rgba(118,139,192,.045)', isSelected ? '#fca5a5' : 'rgba(154,167,215,.18)');
    if (cells[index(row, col)]) { ctx.font = `${Math.max(15, size * .48)}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(CAT, x, y - size * .1); }
  }
  const point = project(selected.row, selected.col, size); drawDiamond(origin.x + point.x, origin.y + point.y - (ROWS + COLS) * size / 8, size, 'transparent', '#fca5a5');
}
function setCell(row, col, value = null) { if (!inBounds(row, col)) return; cells[index(row, col)] = value === null ? (cells[index(row, col)] ? 0 : 1) : value ? 1 : 0; announce(value === null ? `Selected row ${row + 1}, column ${col + 1}.` : 'Board updated.'); draw(); }
function seed(points, offsetRow = 7, offsetCol = 12) { cells.fill(0); points.forEach(([row, col]) => { if (inBounds(row + offsetRow, col + offsetCol)) cells[index(row + offsetRow, col + offsetCol)] = 1; }); generation = 0; announce('Pattern loaded. Ready to explore.'); draw(); }
const patterns = { glider: [[0,1],[1,2],[2,0],[2,1],[2,2]], pulsar: [[-2,-1],[-2,0],[-2,1],[-1,-2],[-1,1],[0,-2],[0,1],[1,-2],[1,1],[2,-1],[2,0],[2,1]], cats: [[-1,-1],[-1,0],[0,-1],[0,0],[-1,2],[-1,3],[0,2],[0,3],[2,-1],[3,-1],[2,0],[3,0]] };
function loop(time) { if (running && time - lastTick > 1000 / Number(speedInput.value)) { lastTick = time; step(); } frame = requestAnimationFrame(loop); }
document.querySelector('#step').addEventListener('click', step);
document.querySelector('#play').addEventListener('click', (event) => { running = !running; event.currentTarget.setAttribute('aria-pressed', running); event.currentTarget.innerHTML = running ? '<span aria-hidden="true">Ⅱ</span> Pause life' : '<span aria-hidden="true">▶</span> Start life'; announce(running ? 'Life is running.' : 'Life paused.'); });
document.querySelector('#clear').addEventListener('click', () => { cells.fill(0); generation = 0; announce('Board cleared. Place a few cats to begin.'); draw(); });
document.querySelector('#randomize').addEventListener('click', () => { cells = Uint8Array.from({ length: ROWS * COLS }, () => Math.random() < .23 ? 1 : 0); generation = 0; announce('A new world has appeared.'); draw(); });
document.querySelectorAll('[data-pattern]').forEach((button) => button.addEventListener('click', () => seed(patterns[button.dataset.pattern])));
speedInput.addEventListener('input', () => { speedValue.textContent = `${speedInput.value} gen / sec`; });
canvas.addEventListener('click', (event) => { const rect = canvas.getBoundingClientRect(); const size = Math.min(rect.width / (COLS * .52), rect.height / (ROWS * .29)); const origin = { x: rect.width / 2, y: rect.height * .47 - (ROWS + COLS) * size / 8 }; const x = event.clientX - rect.left - origin.x; const y = event.clientY - rect.top - origin.y; const col = Math.round(y / (size / 2) + x / size); const row = Math.round(y / (size / 2) - x / size); selected = { row, col }; setCell(row, col); });
canvas.addEventListener('keydown', (event) => { let { row, col } = selected; if (event.key === 'ArrowUp') row -= 1; else if (event.key === 'ArrowDown') row += 1; else if (event.key === 'ArrowLeft') col -= 1; else if (event.key === 'ArrowRight') col += 1; else if (event.key === ' ' || event.key === 'Enter') { event.preventDefault(); setCell(row, col); return; } else return; event.preventDefault(); selected = { row: Math.max(0, Math.min(ROWS - 1, row)), col: Math.max(0, Math.min(COLS - 1, col)) }; announce(`Selected row ${selected.row + 1}, column ${selected.col + 1}.`); draw(); });
window.addEventListener('resize', draw); seed(patterns.glider, 2, 2); frame = requestAnimationFrame(loop);
