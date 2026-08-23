import * as THREE from 'three';
import './styles.css';

const COLS=28, ROWS=31, TILE=1, WALL=0, OPEN=1, HOUSE=2;
// A compact 28 x 31 arcade-style topology. Characters and pellets use this same grid.
const grid=Array.from({length:ROWS},(_,r)=>Array.from({length:COLS},(_,c)=>{
  if(r===0||r===ROWS-1||c===0||c===COLS-1)return WALL;
  if((r===6||r===24)&&(c>2&&c<25)&&c%5!==0)return WALL;
  if((r===10||r===20)&&(c>1&&c<26)&&c%6!==0)return WALL;
  if((c===5||c===22)&&(r>2&&r<28)&&r%6!==0)return WALL;
  if(r>=14&&r<=16&&c>=11&&c<=16)return HOUSE;
  return OPEN;
}));
const dirs={left:{x:-1,z:0},right:{x:1,z:0},up:{x:0,z:-1},down:{x:0,z:1},none:{x:0,z:0}};
const opposite={left:'right',right:'left',up:'down',down:'up',none:'none'};
const scene=new THREE.Scene(); scene.background=new THREE.Color(0x020616);
const viewport=document.querySelector('#viewport');
const camera=new THREE.OrthographicCamera(-14,14,15.5,-15.5,.1,100); camera.position.set(0,24,12); camera.lookAt(0,0,0);
const renderer=new THREE.WebGLRenderer({antialias:true}); renderer.setPixelRatio(Math.min(devicePixelRatio,2)); renderer.shadowMap.enabled=true; viewport.prepend(renderer.domElement);
scene.add(new THREE.HemisphereLight(0x9fcfff,0x0a1040,2)); const blueLight=new THREE.PointLight(0x164cff,8,30); blueLight.position.set(0,3,0); scene.add(blueLight);
const board=new THREE.Group(); scene.add(board); const wallMat=new THREE.MeshStandardMaterial({color:0x163cff,emissive:0x081c94,emissiveIntensity:1.8,roughness:.35});
const floor=new THREE.Mesh(new THREE.BoxGeometry(COLS,.18,ROWS),new THREE.MeshStandardMaterial({color:0x050b29,roughness:.8})); floor.position.y=-.18; board.add(floor);
const pellets=[], powerPellets=[];
function pos(c,r,y=.2){return new THREE.Vector3((c-(COLS-1)/2)*TILE,y,(r-(ROWS-1)/2)*TILE)}
function valid(c,r){return c>=0&&c<COLS&&r>=0&&r<ROWS&&grid[r][c]!==WALL}
for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){
  if(grid[r][c]===WALL){const m=new THREE.Mesh(new THREE.BoxGeometry(.94,.75,.94),wallMat);m.position.copy(pos(c,r,.2));m.castShadow=true;board.add(m);}
  else if(grid[r][c]!==HOUSE){const power=(r===1||r===29)&&(c===1||c===26); const m=new THREE.Mesh(new THREE.SphereGeometry(power?.22:.075,12,8),new THREE.MeshStandardMaterial({color:power?0xffd400:0xfff1b0,emissive:power?0xffa900:0xffd66b,emissiveIntensity:power?1.8:.7}));m.position.copy(pos(c,r,.18));m.userData={c,r,power,active:true};board.add(m);(power?powerPellets:pellets).push(m);}
}
const mat=(color,emissive=color)=>new THREE.MeshStandardMaterial({color,emissive,emissiveIntensity:1.2});
const pacman={c:13,r:23,dir:'none',wanted:'none',speed:5,mesh:new THREE.Mesh(new THREE.ConeGeometry(.42,.62,28,1,false,Math.PI*1.08),mat(0xffe500))}; pacman.mesh.rotation.x=-Math.PI/2; board.add(pacman.mesh);
const ghostColors=[0xff4668,0xff9bd3,0x47e7ff,0xff9d38];
const ghosts=ghostColors.map((color,i)=>{const g={c:12+i,r:15,dir:i%2?'left':'right',speed:2.7+i*.12,frightened:0,home:{c:12+i,r:15},mesh:new THREE.Mesh(new THREE.SphereGeometry(.4,18,12),mat(color))};g.mesh.position.copy(pos(g.c,g.r,.25));board.add(g.mesh);return g});
let score=0,high=Number(localStorage.getItem('neon-pacman-high')||0),lives=3,running=false,paused=false,power=0,ghostBonus=200,last=0,moveClock=0,ghostClock=0;
const $=s=>document.querySelector(s), scoreEl=$('#score'), highEl=$('#high-score'), livesEl=$('#lives'), message=$('#message'), title=$('#message-title'), copy=$('#message-copy'), status=$('#status'); highEl.textContent=String(high).padStart(6,'0');
function updateUI(){scoreEl.textContent=String(score).padStart(6,'0');highEl.textContent=String(Math.max(high,score)).padStart(6,'0');livesEl.textContent='●'.repeat(lives)+'○'.repeat(3-lives)}
function addScore(n){score+=n;if(score>high){high=score;localStorage.setItem('neon-pacman-high',high)}updateUI()}
function canMove(e,d){const q=dirs[d];return d==='none'||valid(e.c+q.x,e.r+q.z)}
function resetPositions(){pacman.c=13;pacman.r=23;pacman.dir='none';pacman.wanted='none';pacman.mesh.position.copy(pos(13,23,.34));ghosts.forEach((g,i)=>{g.c=12+i;g.r=15;g.dir=i%2?'left':'right';g.frightened=0;g.mesh.position.copy(pos(g.c,g.r,.25));g.mesh.material.color.set(ghostColors[i])})}
function freshBoard(){[...pellets,...powerPellets].forEach(m=>{m.userData.active=true;m.visible=true})}
function begin(){score=0;lives=3;power=0;ghostBonus=200;freshBoard();resetPositions();running=true;paused=false;message.classList.add('hidden');status.textContent='READY // CLEAR THE MAZE';updateUI()}
function end(win){running=false;message.classList.remove('hidden');title.textContent=win?'MAZE CLEAR!':'GAME OVER';copy.textContent=win?`Final score ${score}`:`Final score ${score} // High score ${high}`;$('#start-button').textContent='PLAY AGAIN';status.textContent=win?'CHAMPION // MAZE CLEARED':'SIGNAL LOST // INSERT COIN'}
function loseLife(){lives--;updateUI();if(!lives)return end(false);status.textContent='CAUGHT // READY?';resetPositions();setTimeout(()=>{if(running)status.textContent='KEEP MOVING // POWER UP',0},900)}
function collect(){for(const m of [...pellets,...powerPellets])if(m.userData.active&&m.userData.c===pacman.c&&m.userData.r===pacman.r){m.userData.active=false;m.visible=false;if(m.userData.power){addScore(50);power=8;ghostBonus=200;ghosts.forEach(g=>{g.frightened=power;g.mesh.material.color.set(0x318dff)})}else addScore(10)}}
function stepPac(){if(pacman.wanted!== 'none'&&canMove(pacman,pacman.wanted))pacman.dir=pacman.wanted;if(!canMove(pacman,pacman.dir))return;const d=dirs[pacman.dir];pacman.c+=d.x;pacman.r+=d.z;pacman.mesh.position.copy(pos(pacman.c,pacman.r,.34));if(pacman.dir!=='none')pacman.mesh.rotation.y=Math.atan2(d.x,d.z);collect();if(![...pellets,...powerPellets].some(m=>m.userData.active))end(true)}
function ghostStep(g){const choices=Object.keys(dirs).filter(d=>d!=='none'&&canMove(g,d)&&d!==opposite[g.dir]);if(!choices.length)return;let target=power>0?{c:pacman.c+(g.c-pacman.c)*2,r:pacman.r+(g.r-pacman.r)*2}:{c:pacman.c,r:pacman.r};choices.sort((a,b)=>{const da=dirs[a],db=dirs[b];const aa=Math.hypot(g.c+da.x-target.c,g.r+da.z-target.r),bb=Math.hypot(g.c+db.x-target.c,g.r+db.z-target.r);return (g.frightened?bb-aa:aa-bb)});g.dir=choices[0];const d=dirs[g.dir];g.c+=d.x;g.r+=d.z;g.mesh.position.copy(pos(g.c,g.r,.28))}
function collisions(){for(const g of ghosts)if(g.c===pacman.c&&g.r===pacman.r){if(g.frightened){addScore(ghostBonus);ghostBonus*=2;g.c=g.home.c;g.r=g.home.r;g.frightened=0;g.mesh.material.color.set(ghostColors[ghosts.indexOf(g)])}else loseLife()}}
function tick(t){requestAnimationFrame(tick);const dt=Math.min((t-last)/1000,.1);last=t;if(running&&!paused){moveClock+=dt;ghostClock+=dt;if(moveClock>1/pacman.speed){moveClock=0;stepPac()}if(ghostClock>1/3){ghostClock=0;ghosts.forEach(ghostStep);collisions()}if(power>0){power-=dt;ghosts.forEach((g,i)=>{g.frightened=power;g.mesh.material.color.set(power>0?0x318dff:ghostColors[i])})}pacman.mesh.scale.y=1+Math.sin(t/80)*.08;powerPellets.forEach(m=>{if(m.visible)m.scale.setScalar(1+Math.sin(t/160)*.2)})}renderer.render(scene,camera)}
function resize(){const w=viewport.clientWidth,h=viewport.clientHeight,aspect=w/h;const size=16;camera.left=-size*aspect/2;camera.right=size*aspect/2;camera.top=size/2;camera.bottom=-size/2;camera.updateProjectionMatrix();renderer.setSize(w,h,false)}
addEventListener('resize',resize); addEventListener('keydown',e=>{const map={ArrowLeft:'left',ArrowRight:'right',ArrowUp:'up',ArrowDown:'down',a:'left',d:'right',w:'up',s:'down'};if(map[e.key]){e.preventDefault();pacman.wanted=map[e.key];if(!running)begin()}if(e.key==='p'&&running)paused=!paused}); $('#start-button').addEventListener('click',begin); resize(); updateUI(); requestAnimationFrame(tick);
