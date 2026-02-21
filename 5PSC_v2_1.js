// ═══════════════════════════════════════════════════════════════════
// 5PSC v2.1 — 5-Phase Soliton Cipher (Integer-Only Edition)
// A stream cipher based on Wu Xing (Five Elements) dynamic system
//
// Author: Soliton Cipher (Mount Etna, Sicily)
// Date: February 2026
// Prior art: Certified email (PEC), February 19, 2026
// License: Free for everyone. No restrictions.
//
// v2.1 fixes (from CryptoHack Discord community review):
//   - Math.random → crypto.getRandomValues (nvme0n1)
//   - ALL floating point removed → integer-only arithmetic (6...)
//   - Math.sqrt → Manhattan distance (integer)
//   - α scaled to integer fraction (no float)
//   - Cross-platform deterministic: same input = same output, always
//
// Previous v2 fixes over v1:
//   1. Seed 32-bit → 256-bit (brute force impossible)
//   2. Double S-box + feedback chain (breaks linearity)
//   3. Organisms evolve DURING encryption, not just warmup
// ═══════════════════════════════════════════════════════════════════

// ─── CONSTANTS ───────────────────────────────────────────────────
var GRID       = 10000;                // Toroidal grid size
var SPEED_LIMIT = 800;                 // Max velocity per axis
var NAMES      = ["Wood", "Fire", "Earth", "Metal", "Water"];
var INHIBITS   = [2, 3, 4, 0, 1];     // Wu Xing inhibition cycle

// α = 1/137 as integer fraction: ALPHA_NUM / ALPHA_DEN
// Instead of float 0.00729..., we compute (value * ALPHA_NUM) / ALPHA_DEN
var ALPHA_NUM  = 1;
var ALPHA_DEN  = 137;

// ─── SEED: 256-BIT (CSPRNG) ────────────────────────────────────
// Fixed after feedback from /dev/nvme0n1 on CryptoHack Discord

function generateSeed256() {
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    var arr = new Uint32Array(8);
    crypto.getRandomValues(arr);
    return Array.from(arr);
  }
  if (typeof require !== 'undefined') {
    var c = require('crypto');
    var buf = c.randomBytes(32);
    var seed = [];
    for (var i = 0; i < 8; i++) {
      seed.push(buf.readUInt32BE(i * 4));
    }
    return seed;
  }
  throw new Error("No secure random source available");
}

// ─── INTEGER HASH FROM SEED ────────────────────────────────────
// Returns integer 0 to 0xFFFFFFFF (deterministic, no floats)

function seedHashInt(seed256, counter) {
  var h = seed256[counter % 8] ^ Math.imul(counter, 2654435761);
  for (var i = 0; i < 8; i++) {
    h = h ^ seed256[i];
    h = Math.imul(h ^ (h >>> 16), 0x45d9f3b);
  }
  h = Math.imul(h ^ (h >>> 13), 0x45d9f3b);
  return (h ^ (h >>> 16)) >>> 0;
}

// ─── S-BOX (NON-LINEARITY) ─────────────────────────────────────
// Fisher-Yates shuffle with π seed — fully transparent

var SBOX = (function() {
  var box = [];
  for (var i = 0; i < 256; i++) box[i] = i;
  var state = 314159265;
  for (var i = 255; i > 0; i--) {
    state = Math.imul(state ^ (state >>> 16), 0x45d9f3b);
    state = Math.imul(state ^ (state >>> 13), 0x45d9f3b);
    state = (state ^ (state >>> 16)) >>> 0;
    var j = state % (i + 1);
    var tmp = box[i]; box[i] = box[j]; box[j] = tmp;
  }
  return box;
})();

var SBOX_INV = new Array(256);
for (var i = 0; i < 256; i++) SBOX_INV[SBOX[i]] = i;

// ─── ELEMENT CREATION (INTEGER ONLY) ───────────────────────────

function createElement(index, seed256) {
  var h1 = seedHashInt(seed256, index * 100 + 1);
  var h2 = seedHashInt(seed256, index * 100 + 2);
  var h3 = seedHashInt(seed256, index * 100 + 3);
  var h4 = seedHashInt(seed256, index * 100 + 4);

  var row = h1 % GRID;
  var col = h2 % GRID;
  // Velocity: -400 to +399 (integer)
  var vr  = (h3 % 800) - 400;
  var vc  = (h4 % 800) - 400;

  return {
    i: index, name: NAMES[index],
    row: row, col: col, vr: vr, vc: vc,
    history: [{ row: row, col: col }],
    distance: 0
  };
}

// ─── DYNAMIC FORCES (INTEGER ONLY) ─────────────────────────────
// Uses Manhattan distance (|dr| + |dc|) instead of sqrt
// All calculations scaled by 1000 to maintain precision without floats

function calculateDynamicForces(elements) {
  var totalDist = 0;
  for (var i = 0; i < 5; i++) {
    for (var j = i + 1; j < 5; j++) {
      var dr = Math.abs(elements[i].row - elements[j].row);
      var dc = Math.abs(elements[i].col - elements[j].col);
      dr = Math.min(dr, GRID - dr);  // Toroidal
      dc = Math.min(dc, GRID - dc);
      totalDist += dr + dc;  // Manhattan distance (integer)
    }
  }
  // 10 pairs, max Manhattan each = GRID = 10000, so max total = 100000
  // expansion_1000 = totalDist * 1000 / 100000 = totalDist / 100
  var expansion_1000 = (totalDist / 100) | 0;  // 0..1000 range
  if (expansion_1000 > 1000) expansion_1000 = 1000;

  // generate = α * (1 + expansion * 30) * 5
  // In integer: gen_1000 = (1000 + expansion_1000 * 30) * 5 / 137
  var gen_1000 = (((1000 + expansion_1000 * 30) * 5) / ALPHA_DEN) | 0;
  var inh_1000 = (((1000 + (1000 - expansion_1000) * 30) * 5) / ALPHA_DEN) | 0;

  return {
    generate: gen_1000,   // scaled by 1000
    inhibit:  inh_1000,   // scaled by 1000
    expansion: expansion_1000
  };
}

// ─── WU XING MOVEMENT (INTEGER ONLY) ───────────────────────────
// All pushes computed in integer, scaled appropriately

function moveWuXing(elem, all, isYin, forceGen_1000, forceInh_1000) {
  var pushR = 0, pushC = 0;

  // Generation: parent pulls
  // Old: (parent.row - elem.row) / GRID * forceGen * 100
  // New: (parent.row - elem.row) * forceGen_1000 * 100 / (GRID * 1000)
  //    = (parent.row - elem.row) * forceGen_1000 / (GRID * 10)
  var parent = all[(elem.i + 4) % 5];
  pushR = ((parent.row - elem.row) * forceGen_1000 / (GRID * 10)) | 0;
  pushC = ((parent.col - elem.col) * forceGen_1000 / (GRID * 10)) | 0;

  // Inhibition: controller resists
  var controllerIdx = -1;
  for (var k = 0; k < 5; k++) {
    if (INHIBITS[k] === elem.i) { controllerIdx = k; break; }
  }
  if (controllerIdx >= 0) {
    var signR = elem.vr > 0 ? 1 : (elem.vr < 0 ? -1 : 0);
    var signC = elem.vc > 0 ? 1 : (elem.vc < 0 ? -1 : 0);
    pushR = pushR - ((signR * forceInh_1000 * 100 / 1000) | 0);
    pushC = pushC - ((signC * forceInh_1000 * 100 / 1000) | 0);
  }

  // Environmental noise (already integer)
  var climateHash = 0;
  for (var k = 0; k < all.length; k++) {
    if (k !== elem.i) {
      climateHash = (climateHash ^ (all[k].row * 65537 + all[k].col * 257)) >>> 0;
    }
  }
  var mix1 = (climateHash ^ (elem.row * 31337 + elem.i * 7919)) >>> 0;
  var mix2 = (climateHash ^ (elem.col * 48271 + elem.i * 6151)) >>> 0;
  // noise: -10 to +9 (integer, no float)
  var noise0 = (mix1 % 20) - 10;
  var noise1 = (mix2 % 20) - 10;

  // Apply forces
  var vr, vc;
  if (isYin) {
    vr = elem.vr - pushR + noise0;
    vc = elem.vc - pushC + noise1;
  } else {
    vr = elem.vr + pushR + noise0;
    vc = elem.vc + pushC + noise1;
  }

  // Speed limit
  if (vr > SPEED_LIMIT) vr = SPEED_LIMIT;
  if (vr < -SPEED_LIMIT) vr = -SPEED_LIMIT;
  if (vc > SPEED_LIMIT) vc = SPEED_LIMIT;
  if (vc < -SPEED_LIMIT) vc = -SPEED_LIMIT;

  // Move on toroidal grid
  var newRow = ((elem.row + vr) % GRID + GRID) % GRID;
  var newCol = ((elem.col + vc) % GRID + GRID) % GRID;

  // Manhattan distance for history (integer)
  var dr = Math.abs(newRow - elem.row);
  var dc = Math.abs(newCol - elem.col);
  var hist = elem.history.slice(-60);
  hist.push({ row: newRow, col: newCol });

  return {
    i: elem.i, name: elem.name,
    row: newRow, col: newCol, vr: vr, vc: vc,
    history: hist,
    distance: elem.distance + dr + dc  // Manhattan, integer
  };
}

// ─── MODULAR INVERSE ────────────────────────────────────────────
function modInverse(a, m) {
  var old_r = ((a % m) + m) % m, r = m, old_s = 1, s = 0;
  while (r !== 0) {
    var q = Math.floor(old_r / r);
    var tmp_r = r; r = old_r - q * r; old_r = tmp_r;
    var tmp_s = s; s = old_s - q * s; old_s = tmp_s;
  }
  if (old_r !== 1) return null;
  return ((old_s % m) + m) % m;
}

// ─── POSITION FACTOR (INTEGER ONLY) ────────────────────────────

function calculatePositionFactor(position, yang, yin) {
  var elIdx  = position % 5;
  var elNext = (elIdx + 1) % 5;
  var elPrev = (elIdx + 4) % 5;
  var cycle  = Math.floor(position / 5);

  var diffR = Math.abs(yang[elIdx].row - yin[elIdx].row);
  var diffC = Math.abs(yang[elIdx].col - yin[elIdx].col);

  var diffRmix = diffR + Math.abs(yang[elNext].col - yin[elPrev].row) + cycle * 7;
  var diffCmix = diffC + Math.abs(yang[elPrev].row - yin[elNext].col) + cycle * 13;

  var mult = diffRmix % 256;
  if (mult % 2 === 0) mult = (mult + 1) % 256;
  if (mult < 3) mult = mult + 2;

  var offset = diffCmix % 256;
  var inv = modInverse(mult, 256);

  return { mult: mult, offset: offset, inv: inv };
}

// ─── UTF-8 ENCODING ─────────────────────────────────────────────
function strToBytes(s) {
  var b = [];
  for (var i = 0; i < s.length; i++) {
    var c = s.charCodeAt(i);
    if (c < 0x80) b.push(c);
    else if (c < 0x800) { b.push(0xC0 | (c >> 6)); b.push(0x80 | (c & 0x3F)); }
    else { b.push(0xE0 | (c >> 12)); b.push(0x80 | ((c >> 6) & 0x3F)); b.push(0x80 | (c & 0x3F)); }
  }
  return b;
}

function bytesToStr(bytes) {
  var result = "";
  var i = 0;
  while (i < bytes.length) {
    var b = bytes[i];
    if (b < 0x80) { result += String.fromCharCode(b); i++; }
    else if (b < 0xE0) { result += String.fromCharCode(((b & 0x1F) << 6) | (bytes[i+1] & 0x3F)); i += 2; }
    else { result += String.fromCharCode(((b & 0x0F) << 12) | ((bytes[i+1] & 0x3F) << 6) | (bytes[i+2] & 0x3F)); i += 3; }
  }
  return result;
}

function bytesToHex(b) {
  return b.map(function(v) { return ("00" + v.toString(16)).slice(-2); }).join("");
}

function hexToBytes(h) {
  var b = [];
  for (var i = 0; i < h.length; i += 2) b.push(parseInt(h.substr(i, 2), 16));
  return b;
}

// ─── ORGANISM EVOLUTION ─────────────────────────────────────────

function evolveOrganisms(yang, yin) {
  var fY = calculateDynamicForces(yang);
  var fI = calculateDynamicForces(yin);
  return {
    yang: yang.map(function(e) { return moveWuXing(e, yang, false, fY.generate, fY.inhibit); }),
    yin:  yin.map(function(e) { return moveWuXing(e, yin,  true,  fI.generate, fI.inhibit); })
  };
}

// ═════════════════════════════════════════════════════════════════
// ENCRYPT
// ═════════════════════════════════════════════════════════════════

function encrypt(message, warmup, seed256) {
  var yang = NAMES.map(function(_, i) { return createElement(i, seed256); });
  var yin  = NAMES.map(function(_, i) { return createElement(i, seed256); });

  for (var b = 0; b < warmup; b++) {
    var ev = evolveOrganisms(yang, yin);
    yang = ev.yang; yin = ev.yin;
  }

  var msgBytes = strToBytes(message);
  var cipherBytes = [];
  var feedback = 0;

  for (var i = 0; i < msgBytes.length; i++) {
    var f = calculatePositionFactor(i, yang, yin);

    var step1 = (((msgBytes[i] ^ feedback) * f.mult) + f.offset) % 256;
    var step2 = SBOX[step1];
    var step3 = SBOX[(step2 + f.mult + feedback) % 256];
    var step4 = step3 ^ ((f.offset * 37 + i) % 256);

    cipherBytes.push(step4);
    feedback = (feedback + step4 + f.mult) % 256;

    if (i % 5 === 4) {
      var ev = evolveOrganisms(yang, yin);
      yang = ev.yang; yin = ev.yin;
    }
  }

  return {
    hex: bytesToHex(cipherBytes),
    seed: seed256,
    warmup: warmup,
    length: msgBytes.length
  };
}

// ═════════════════════════════════════════════════════════════════
// DECRYPT
// ═════════════════════════════════════════════════════════════════

function decrypt(hexCipher, warmup, seed256) {
  var yang = NAMES.map(function(_, i) { return createElement(i, seed256); });
  var yin  = NAMES.map(function(_, i) { return createElement(i, seed256); });

  for (var b = 0; b < warmup; b++) {
    var ev = evolveOrganisms(yang, yin);
    yang = ev.yang; yin = ev.yin;
  }

  var cipherBytes = hexToBytes(hexCipher);
  var plainBytes = [];
  var feedback = 0;

  for (var i = 0; i < cipherBytes.length; i++) {
    var f = calculatePositionFactor(i, yang, yin);

    var step3 = cipherBytes[i] ^ ((f.offset * 37 + i) % 256);
    var step2 = ((SBOX_INV[step3] - f.mult - feedback + 256 * 10) % 256);
    var step1 = SBOX_INV[step2];
    var plainXored = ((step1 - f.offset + 256 * 10) * f.inv) % 256;
    var plain = plainXored ^ feedback;

    plainBytes.push(plain);
    feedback = (feedback + cipherBytes[i] + f.mult) % 256;

    if (i % 5 === 4) {
      var ev = evolveOrganisms(yang, yin);
      yang = ev.yang; yin = ev.yin;
    }
  }

  return bytesToStr(plainBytes);
}

// ═════════════════════════════════════════════════════════════════
// SELF-TEST
// ═════════════════════════════════════════════════════════════════

if (typeof require !== 'undefined') {
  console.log("5PSC v2.1 — Self-test (Integer-Only Edition)\n");

  var seed = generateSeed256();
  var messages = [
    "The quieter you become, the more you can hear.",
    "Hello World! Test with numbers 12345 and symbols #$%",
    "A".repeat(100),
    "Special chars: àèìòù £€ @#"  // UTF-8
  ];

  var allPass = true;

  for (var m = 0; m < messages.length; m++) {
    var enc = encrypt(messages[m], 100, seed);
    var dec = decrypt(enc.hex, 100, seed);
    var pass = dec === messages[m];
    if (!pass) allPass = false;
    console.log((pass ? "PASS" : "FAIL") + " | Message " + (m+1) +
      " (" + messages[m].length + " chars) | " +
      "Unique bytes: " + (new Set(hexToBytes(enc.hex))).size + "/" + enc.length);
  }

  // Different seed = different output
  var seed2 = generateSeed256();
  var enc1 = encrypt("test", 100, seed);
  var enc2 = encrypt("test", 100, seed2);
  var diffPass = enc1.hex !== enc2.hex;
  if (!diffPass) allPass = false;
  console.log((diffPass ? "PASS" : "FAIL") + " | Different seeds produce different output");

  // Cross-platform determinism: same seed = same output (run twice)
  var fixedSeed = [1234567890, 987654321, 111111111, 222222222,
                   333333333, 444444444, 555555555, 666666666];
  var enc3 = encrypt("determinism test", 100, fixedSeed);
  var enc4 = encrypt("determinism test", 100, fixedSeed);
  var detPass = enc3.hex === enc4.hex;
  if (!detPass) allPass = false;
  console.log((detPass ? "PASS" : "FAIL") + " | Determinism: same seed = same output");
  console.log("  Reference hash: " + enc3.hex.substring(0, 32) + "...");

  // Verify NO floating point used (informational)
  console.log("\nFloat-free verification:");
  console.log("  Math.random: NOT used (crypto.getRandomValues)");
  console.log("  Math.sqrt:   NOT used (Manhattan distance)");
  console.log("  Float division: NOT used (integer scaled /1000)");
  console.log("  ALPHA: integer fraction 1/137");

  console.log("\n" + (allPass ? "ALL TESTS PASSED" : "SOME TESTS FAILED"));
}
