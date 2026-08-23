"use strict";

/* =========================================================
   SKY DEFENDER - Vertical Scroll Shooter
   Semua angka gameplay & teks cerita dibaca dari:
     config/game-config.json
     config/story.json
   ========================================================= */

const canvas = document.getElementById("game-canvas");
const ctx = canvas.getContext("2d");
const W = canvas.width, H = canvas.height;

let CFG = null;   // game-config.json
let STORY = null; // story.json
const IMG = {};   // cache: filename -> HTMLImageElement

const State = {
  MENU: "MENU",
  OPENING: "OPENING",
  PLAYING: "PLAYING",
  CONTINUE_PROMPT: "CONTINUE_PROMPT",
  ENDING: "ENDING",
};
let state = State.MENU;

/* ---------- Loading helpers ---------- */
async function loadJSON(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error("Gagal memuat " + path);
  return res.json();
}

function loadImage(name) {
  return new Promise((resolve) => {
    if (IMG[name]) return resolve(IMG[name]);
    const img = new Image();
    img.onload = () => { IMG[name] = img; resolve(img); };
    img.onerror = () => { console.warn("Gambar tidak ditemukan:", name); resolve(null); };
    img.src = "assets/img/" + name;
  });
}

async function preloadAll() {
  const names = new Set();
  names.add(CFG.player.image);
  names.add(CFG.player.bulletImage);
  names.add(CFG.bomb.icon);
  names.add(CFG.bomb.blastImage);
  names.add(CFG.enemyBullet.image);
  names.add(CFG.boss.image);
  names.add("bg_game.png");
  names.add("life_icon.png");
  CFG.enemyTypes.forEach((e) => names.add(e.image));
  names.add(STORY.menu.background);
  names.add(STORY.opening.image);
  names.add(STORY.endingWin.image);
  names.add(STORY.endingLose.image);
  await Promise.all([...names].map(loadImage));
}

/* ---------- Utility ---------- */
function rand(min, max) { return Math.random() * (max - min) + min; }
function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function circleHit(ax, ay, ar, bx, by, br) {
  const dx = ax - bx, dy = ay - by;
  return dx * dx + dy * dy <= (ar + br) * (ar + br);
}
function weightedPick(list) {
  const total = list.reduce((s, e) => s + e.spawnWeight, 0);
  let r = rand(0, total);
  for (const e of list) {
    if (r < e.spawnWeight) return e;
    r -= e.spawnWeight;
  }
  return list[list.length - 1];
}

/* ---------- Input ---------- */
const keys = {};
window.addEventListener("keydown", (e) => {
  keys[e.code] = true;
  if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"].includes(e.code)) e.preventDefault();
});
window.addEventListener("keyup", (e) => { keys[e.code] = false; });

let touchDir = { x: 0, y: 0 };
let touchShoot = false;
function setupTouchControls() {
  const stick = document.getElementById("touch-stick");
  const bombBtn = document.getElementById("touch-bomb");
  let dragging = false, ox = 0, oy = 0;
  stick.addEventListener("pointerdown", (e) => {
    dragging = true; touchShoot = true;
    ox = e.clientX; oy = e.clientY;
    stick.setPointerCapture(e.pointerId);
  });
  stick.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    let dx = e.clientX - ox, dy = e.clientY - oy;
    const max = 50;
    dx = clamp(dx, -max, max); dy = clamp(dy, -max, max);
    touchDir.x = dx / max; touchDir.y = dy / max;
  });
  function endDrag() { dragging = false; touchShoot = false; touchDir.x = 0; touchDir.y = 0; }
  stick.addEventListener("pointerup", endDrag);
  stick.addEventListener("pointercancel", endDrag);
  bombBtn.addEventListener("pointerdown", (e) => { e.preventDefault(); useBomb(); });
}

/* ---------- Game entities ---------- */
let player, bullets, enemyBullets, enemies, particles;
let killCount, score, lives, bombs, shotsSinceLastBomb;
let bossActive, boss, bossPhase2;
let spawnTimer, spawnInterval, rampTimer;
let invincibleTimer;
let fireCooldown;
let bombFlashTimer;
let outcomePending; // "win" | "lose" | null

function resetGameState() {
  player = {
    x: W * CFG.player.startX,
    y: H - CFG.player.startYFromBottom,
    r: CFG.player.hitboxRadius,
  };
  bullets = [];
  enemyBullets = [];
  enemies = [];
  particles = [];
  killCount = 0;
  score = 0;
  lives = CFG.player.startLives;
  bombs = CFG.bomb.startingBombs;
  shotsSinceLastBomb = 0;
  bossActive = false;
  boss = null;
  bossPhase2 = false;
  spawnTimer = CFG.spawning.initialDelaySeconds;
  spawnInterval = rand(CFG.spawning.minSpawnIntervalSeconds, CFG.spawning.maxSpawnIntervalSeconds);
  rampTimer = 0;
  invincibleTimer = 0;
  fireCooldown = 0;
  bombFlashTimer = 0;
  outcomePending = null;
  updateHUD();
}

/* ---------- Enemy spawning ---------- */
function spawnEnemy() {
  const def = weightedPick(CFG.enemyTypes);
  enemies.push({
    def,
    x: rand(def.width, W - def.width),
    y: -def.height,
    hp: def.hitsToKill,
    t: 0,
    baseX: 0,
    shootTimer: rand(0.3, def.shootIntervalSeconds || 2),
  });
}

function spawnBoss() {
  bossActive = true;
  bossPhase2 = false;
  boss = {
    def: CFG.boss,
    x: W / 2,
    y: -CFG.boss.height,
    targetY: 110,
    hp: CFG.boss.hitsToKill,
    maxHp: CFG.boss.hitsToKill,
    entering: true,
    shootTimer: 1.2,
    t: 0,
  };
  document.getElementById("boss-hp-wrap").classList.remove("hidden");
}

/* ---------- Combat ---------- */
function firePlayerBullet() {
  bullets.push({ x: player.x, y: player.y - 20 });
  shotsSinceLastBomb++;
  if (shotsSinceLastBomb >= CFG.bomb.shotsToChargeBomb) {
    shotsSinceLastBomb = 0;
    bombs = Math.min(CFG.bomb.maxBombs, bombs + 1);
    updateHUD();
  }
}

function useBomb() {
  if (state !== State.PLAYING || bombs <= 0) return;
  bombs--;
  bombFlashTimer = 0.45;
  enemyBullets.length = 0;
  for (const en of enemies) { addExplosion(en.x, en.y); score += en.def.score; killCount++; }
  enemies.length = 0;
  if (bossActive && boss) {
    boss.hp -= Math.ceil(boss.maxHp * 0.18);
    addExplosion(boss.x, boss.y);
  }
  updateHUD();
  checkBossDeath();
}

function addExplosion(x, y) {
  for (let i = 0; i < 10; i++) {
    particles.push({
      x, y,
      vx: rand(-140, 140), vy: rand(-140, 140),
      life: rand(0.25, 0.5), maxLife: 0.5,
      color: pick(["#ffcf7a", "#ff8a5b", "#ffffff", "#7fd7ff"]),
    });
  }
}

function playerHit() {
  if (invincibleTimer > 0) return;
  lives--;
  bombs = Math.min(CFG.bomb.maxBombs, bombs + CFG.bomb.refillOnDeath);
  invincibleTimer = CFG.player.invincibleAfterHitSeconds;
  addExplosion(player.x, player.y);
  updateHUD();
  if (lives <= 0) {
    showContinuePrompt();
  }
}

function checkBossDeath() {
  if (bossActive && boss && boss.hp <= 0) {
    addExplosion(boss.x, boss.y);
    score += CFG.boss.score;
    bossActive = false;
    boss = null;
    document.getElementById("boss-hp-wrap").classList.add("hidden");
    outcomePending = "win";
    updateHUD();
  }
}

/* ---------- Update loop ---------- */
function update(dt) {
  if (bombFlashTimer > 0) bombFlashTimer = Math.max(0, bombFlashTimer - dt);
  if (invincibleTimer > 0) invincibleTimer = Math.max(0, invincibleTimer - dt);

  // --- player movement ---
  let dx = 0, dy = 0;
  if (keys["ArrowLeft"] || keys["KeyA"]) dx -= 1;
  if (keys["ArrowRight"] || keys["KeyD"]) dx += 1;
  if (keys["ArrowUp"] || keys["KeyW"]) dy -= 1;
  if (keys["ArrowDown"] || keys["KeyS"]) dy += 1;
  dx += touchDir.x; dy += touchDir.y;
  const len = Math.hypot(dx, dy) || 1;
  if (Math.hypot(dx, dy) > 0.05) {
    player.x += (dx / len) * CFG.player.speed * dt;
    player.y += (dy / len) * CFG.player.speed * dt;
  }
  player.x = clamp(player.x, 20, W - 20);
  player.y = clamp(player.y, 40, H - 20);

  // --- fire ---
  fireCooldown -= dt;
  const wantFire = keys["Space"] || touchShoot;
  if (wantFire && fireCooldown <= 0) {
    firePlayerBullet();
    fireCooldown = 1 / CFG.player.fireRatePerSecond;
  }

  // --- bomb key ---
  if (keys["KeyX"] || keys["ShiftLeft"] || keys["ShiftRight"]) {
    if (!update._bombLatch) { useBomb(); update._bombLatch = true; }
  } else {
    update._bombLatch = false;
  }

  // --- spawning ---
  if (!bossActive && killCount < CFG.enemiesToTriggerBoss) {
    spawnTimer -= dt;
    rampTimer += dt;
    if (rampTimer >= CFG.spawning.difficultyRampEverySeconds) {
      rampTimer = 0;
      spawnInterval = Math.max(0.25, spawnInterval * CFG.spawning.difficultyRampFactor);
    }
    if (spawnTimer <= 0) {
      spawnEnemy();
      spawnTimer = rand(CFG.spawning.minSpawnIntervalSeconds, spawnInterval);
    }
  } else if (!bossActive && killCount >= CFG.enemiesToTriggerBoss && !boss) {
    spawnBoss();
  }

  // --- player bullets ---
  for (let i = bullets.length - 1; i >= 0; i--) {
    const b = bullets[i];
    b.y -= CFG.player.bulletSpeed * dt;
    if (b.y < -20) { bullets.splice(i, 1); continue; }

    let hit = false;
    for (let j = enemies.length - 1; j >= 0; j--) {
      const en = enemies[j];
      if (circleHit(b.x, b.y, 4, en.x, en.y, en.def.width * 0.35)) {
        en.hp -= CFG.player.bulletDamage;
        hit = true;
        if (en.hp <= 0) {
          addExplosion(en.x, en.y);
          score += en.def.score;
          killCount++;
          enemies.splice(j, 1);
        }
        break;
      }
    }
    if (!hit && bossActive && boss && !boss.entering &&
        circleHit(b.x, b.y, 4, boss.x, boss.y, CFG.boss.width * 0.38)) {
      boss.hp -= CFG.player.bulletDamage;
      hit = true;
      if (boss.hp > 0 && boss.hp <= boss.maxHp * (CFG.boss.phaseTwoHpPercent / 100)) bossPhase2 = true;
      checkBossDeath();
    }
    if (hit) bullets.splice(i, 1);
  }

  // --- enemies movement & shooting ---
  for (let i = enemies.length - 1; i >= 0; i--) {
    const en = enemies[i];
    en.t += dt;
    en.y += en.def.speed * dt;
    if (en.def.movement === "zigzag") {
      en.x += Math.sin(en.t * 3) * 60 * dt;
    } else if (en.def.movement === "sine") {
      en.x += Math.sin(en.t * 2.2) * 90 * dt;
    }
    en.x = clamp(en.x, en.def.width / 2, W - en.def.width / 2);

    if (en.def.canShoot) {
      en.shootTimer -= dt;
      if (en.shootTimer <= 0 && en.y > 0 && en.y < H - 80) {
        en.shootTimer = en.def.shootIntervalSeconds;
        enemyBullets.push({ x: en.x, y: en.y + en.def.height / 2, vx: 0, vy: CFG.enemyBullet.speed });
      }
    }

    if (en.y - en.def.height / 2 > H + 20) { enemies.splice(i, 1); continue; }
    if (circleHit(player.x, player.y, player.r, en.x, en.y, en.def.width * 0.35)) {
      addExplosion(en.x, en.y);
      enemies.splice(i, 1);
      playerHit();
    }
  }

  // --- boss update ---
  if (bossActive && boss) {
    boss.t += dt;
    if (boss.entering) {
      boss.y += 60 * dt;
      if (boss.y >= boss.targetY) { boss.y = boss.targetY; boss.entering = false; }
    } else {
      boss.x = W / 2 + Math.sin(boss.t * 0.9) * (W / 2 - CFG.boss.width / 2 - 10);
      const interval = bossPhase2 ? CFG.boss.phaseTwoShootIntervalSeconds : CFG.boss.shootIntervalSeconds;
      boss.shootTimer -= dt;
      if (boss.shootTimer <= 0) {
        boss.shootTimer = interval;
        const n = CFG.boss.bulletsPerVolley;
        for (let k = 0; k < n; k++) {
          const spread = (k - (n - 1) / 2) * 0.35;
          enemyBullets.push({
            x: boss.x, y: boss.y + CFG.boss.height / 2,
            vx: Math.sin(spread) * CFG.enemyBullet.speed,
            vy: Math.cos(spread) * CFG.enemyBullet.speed,
          });
        }
      }
      if (circleHit(player.x, player.y, player.r, boss.x, boss.y, CFG.boss.width * 0.4)) {
        playerHit();
      }
    }
    updateBossHpBar();
  }

  // --- enemy bullets ---
  for (let i = enemyBullets.length - 1; i >= 0; i--) {
    const b = enemyBullets[i];
    b.x += b.vx * dt;
    b.y += b.vy * dt;
    if (b.y > H + 20 || b.x < -20 || b.x > W + 20) { enemyBullets.splice(i, 1); continue; }
    if (circleHit(player.x, player.y, player.r, b.x, b.y, 5)) {
      enemyBullets.splice(i, 1);
      playerHit();
    }
  }

  // --- particles ---
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.life -= dt;
    if (p.life <= 0) { particles.splice(i, 1); continue; }
    p.x += p.vx * dt;
    p.y += p.vy * dt;
  }

  if (score >= 0) maybeAwardExtraLife();

  if (outcomePending === "win") {
    outcomePending = null;
    showEnding("win");
  }
}

let lastExtraLifeAt = 0;
function maybeAwardExtraLife() {
  const step = CFG.scoring.extraLifeEveryScore;
  if (!step) return;
  if (Math.floor(score / step) > Math.floor(lastExtraLifeAt / step)) {
    lastExtraLifeAt = score;
    lives = Math.min(lives + 1, 9);
    updateHUD();
  }
}

/* ---------- Render ---------- */
let bgScroll = 0;
function render(dt) {
  bgScroll = (bgScroll + 60 * dt) % H;
  const bg = IMG["bg_game.png"];
  if (bg) {
    ctx.drawImage(bg, 0, bgScroll - H, W, H);
    ctx.drawImage(bg, 0, bgScroll, W, H);
  } else {
    ctx.fillStyle = "#05061a";
    ctx.fillRect(0, 0, W, H);
  }

  // player
  if (state === State.PLAYING) {
    const flashing = invincibleTimer > 0 && Math.floor(invincibleTimer * 10) % 2 === 0;
    if (!flashing) {
      const img = IMG[CFG.player.image];
      if (img) ctx.drawImage(img, player.x - img.width / 2, player.y - img.height / 2);
    }

    for (const b of bullets) {
      const img = IMG[CFG.player.bulletImage];
      if (img) ctx.drawImage(img, b.x - img.width / 2, b.y - img.height / 2);
    }
    for (const b of enemyBullets) {
      const img = IMG[CFG.enemyBullet.image];
      if (img) ctx.drawImage(img, b.x - img.width / 2, b.y - img.height / 2);
    }
    for (const en of enemies) {
      const img = IMG[en.def.image];
      if (img) ctx.drawImage(img, en.x - img.width / 2, en.y - img.height / 2);
    }
    if (bossActive && boss) {
      const img = IMG[CFG.boss.image];
      if (img) ctx.drawImage(img, boss.x - img.width / 2, boss.y - img.height / 2);
    }
    for (const p of particles) {
      ctx.globalAlpha = clamp(p.life / p.maxLife, 0, 1);
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;
    }
    if (bombFlashTimer > 0) {
      const blast = IMG[CFG.bomb.blastImage];
      ctx.globalAlpha = clamp(bombFlashTimer / 0.45, 0, 1) * 0.9;
      if (blast) ctx.drawImage(blast, 0, 0, W, H);
      else { ctx.fillStyle = "#fff6d0"; ctx.fillRect(0, 0, W, H); }
      ctx.globalAlpha = 1;
    }
  }
}

/* ---------- HUD ---------- */
function updateHUD() {
  const livesWrap = document.getElementById("hud-lives");
  const lifeIcon = IMG["life_icon.png"];
  livesWrap.innerHTML = (STORY.hud.livesLabel + ": ") +
    (lifeIcon ? Array.from({ length: Math.max(lives, 0) }).map(() => `<img src="assets/img/life_icon.png">`).join("") : lives);

  document.getElementById("hud-bombs").textContent = `${STORY.hud.bombLabel}: ${bombs}/${CFG.bomb.maxBombs}`;
  document.getElementById("hud-score").textContent = `${STORY.hud.scoreLabel}: ${score}`;
  document.getElementById("hud-kills").textContent = bossActive
    ? STORY.hud.bossWarningText
    : `${STORY.hud.killLabel}: ${Math.min(killCount, CFG.enemiesToTriggerBoss)}/${CFG.enemiesToTriggerBoss}`;
}

function updateBossHpBar() {
  if (!boss) return;
  const pct = clamp((boss.hp / boss.maxHp) * 100, 0, 100);
  document.getElementById("boss-hp-bar").style.width = pct + "%";
}

/* ---------- Screens ---------- */
function showScreen(id) {
  document.querySelectorAll(".screen").forEach((el) => el.classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
}

function goMenu() {
  state = State.MENU;
  document.getElementById("hud").classList.add("hidden");
  document.getElementById("touch-controls").classList.add("hidden");
  document.getElementById("boss-hp-wrap").classList.add("hidden");
  showScreen("screen-menu");
}

function goOpeningThenPlay() {
  state = State.OPENING;
  showScreen("screen-opening");
}

function startPlaying() {
  resetGameState();
  state = State.PLAYING;
  document.getElementById("hud").classList.remove("hidden");
  document.getElementById("touch-controls").classList.remove("hidden");
  document.querySelectorAll(".screen").forEach((el) => el.classList.add("hidden"));
}

function showContinuePrompt() {
  state = State.CONTINUE_PROMPT;
  showScreen("screen-continue");
}

function resumeAfterContinue() {
  lives = CFG.player.startLives;
  bombs = CFG.bomb.maxBombs;
  invincibleTimer = CFG.player.invincibleAfterHitSeconds;
  enemyBullets.length = 0;
  enemies.length = 0;
  updateHUD();
  state = State.PLAYING;
  document.querySelectorAll(".screen").forEach((el) => el.classList.add("hidden"));
}

function showEnding(kind) {
  state = State.ENDING;
  document.getElementById("hud").classList.add("hidden");
  document.getElementById("touch-controls").classList.add("hidden");
  document.getElementById("boss-hp-wrap").classList.add("hidden");
  const data = kind === "win" ? STORY.endingWin : STORY.endingLose;
  document.getElementById("ending-title").textContent = data.title;
  document.getElementById("ending-image").src = "assets/img/" + data.image;
  document.getElementById("ending-text").innerHTML = data.paragraphs.map((p) => `<p>${p}</p>`).join("");
  document.getElementById("ending-score").textContent = `${STORY.hud.scoreLabel}: ${score}`;
  document.getElementById("btn-ending-restart").textContent = data.restartButtonText;
  showScreen("screen-ending");
}

/* ---------- UI wiring ---------- */
function wireUI() {
  document.getElementById("menu-bg").src = "assets/img/" + STORY.menu.background;
  document.getElementById("menu-title").textContent = STORY.menu.title;
  document.getElementById("menu-subtitle").textContent = STORY.menu.subtitle;
  document.getElementById("btn-start").textContent = STORY.menu.startButtonText;
  document.getElementById("btn-story").textContent = STORY.menu.storyButtonText;
  document.getElementById("menu-howto").textContent = STORY.menu.howToPlayText;
  document.getElementById("menu-footer").textContent = STORY.menu.footerText;

  document.getElementById("opening-title").textContent = STORY.opening.title;
  document.getElementById("opening-image").src = "assets/img/" + STORY.opening.image;
  document.getElementById("opening-text").innerHTML = STORY.opening.paragraphs.map((p) => `<p>${p}</p>`).join("");
  document.getElementById("btn-opening-continue").textContent = STORY.opening.continueButtonText;

  document.getElementById("continue-title").textContent = STORY.continuePrompt.title;
  document.getElementById("continue-message").textContent = STORY.continuePrompt.message;
  document.getElementById("btn-continue-yes").textContent = STORY.continuePrompt.continueButtonText;
  document.getElementById("btn-continue-no").textContent = STORY.continuePrompt.endButtonText;
  document.getElementById("continue-note").textContent = STORY.continuePrompt.note;

  document.getElementById("btn-start").addEventListener("click", () => { startPlaying(); });
  document.getElementById("btn-story").addEventListener("click", () => { goOpeningThenPlay(); });
  document.getElementById("btn-opening-continue").addEventListener("click", () => { startPlaying(); });
  document.getElementById("btn-continue-yes").addEventListener("click", () => { resumeAfterContinue(); });
  document.getElementById("btn-continue-no").addEventListener("click", () => { showEnding("lose"); });
  document.getElementById("btn-ending-restart").addEventListener("click", () => { goMenu(); });

  setupTouchControls();
}

/* ---------- Main loop ---------- */
let lastTime = 0;
function loop(ts) {
  const dt = Math.min(0.05, (ts - lastTime) / 1000 || 0);
  lastTime = ts;

  if (state === State.PLAYING) {
    update(dt);
    updateHUD();
  }
  render(dt);
  requestAnimationFrame(loop);
}

/* ---------- Boot ---------- */
(async function init() {
  try {
    [CFG, STORY] = await Promise.all([
      loadJSON("config/game-config.json"),
      loadJSON("config/story.json"),
    ]);
    await preloadAll();
    wireUI();
    goMenu();
    requestAnimationFrame(loop);
  } catch (err) {
    console.error(err);
    document.body.innerHTML =
      '<div style="color:#fff;padding:30px;font-family:sans-serif">' +
      "Gagal memuat game. Pastikan file dibuka lewat server lokal (bukan file:// langsung), " +
      "karena browser memblokir fetch() JSON dari file lokal.<br><br>" +
      "Jalankan misalnya: <code>python -m http.server 8000</code> di folder scroll-shooting, " +
      "lalu buka <code>http://localhost:8000</code>.<br><br>Detail error: " + err.message +
      "</div>";
  }
})();
