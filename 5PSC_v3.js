/**
 * 5PSC v3.0 — 5-Phase Soliton Cipher
 * Stream cipher based on Wu Xing dynamical system
 * 
 * CHANGELOG v3.0 (based on independent peer review):
 *   FIX-1: Yin system initialized from domain-separated seed derivation
 *          (eliminates zero initial divergence between Yang and Yin)
 *   FIX-2: Feedback accumulator extended from 8-bit to 32-bit with 
 *          multiplicative mixing (eliminates 256-cycle period)
 *   FIX-3: Position factor parameters derived from wider state 
 *          (eliminates small 32K affine search space)
 *   FIX-4: History array removed (served no cryptographic purpose)
 *   FIX-5: Seed generation uses crypto.getRandomValues exclusively
 *          (Math.random was present in v2 HTML demo)
 *   FIX-6: Improved mult/offset distribution in position factor
 * 
 * KNOWN LIMITATIONS (unchanged, documented since v2):
 *   - No AEAD (no integrity/authentication)
 *   - No formalized nonce/IV (same seed = same ciphertext)
 *   - S-box not analyzed for differential uniformity
 *   - Not constant-time (timing side-channel possible)
 *   - No formal cryptanalysis by professional cryptanalyst
 * 
 * LICENSE: MIT
 * AUTHORS: Quintilio Menicocci & Claude (Anthropic)
 */

(function(exports) {
"use strict";

var GRID = 10000;
var SPEED_LIMIT = 800;
var ALPHA_NUM = 100000;
var ALPHA_DEN = 13703600;
var NAMES = ["Wood", "Fire", "Earth", "Metal", "Water"];
var INHIBITS = [2, 3, 4, 0, 1];

// ═══════════════════════════════════════════════════════════
// PRNG — deterministic hash from 256-bit seed
// ═══════════════════════════════════════════════════════════

function hashMix(h) {
  h = Math.imul(h ^ (h >>> 16), 0x45d9f3b);
  h = Math.imul(h ^ (h >>> 13), 0x45d9f3b);
  return (h ^ (h >>> 16)) >>> 0;
}

function entSeed256(seed256, counter) {
  var h = (seed256[counter % 8] ^ Math.imul(counter, 2654435761)) >>> 0;
  for (var i = 0; i < 8; i++) {
    h = (h ^ seed256[i]) >>> 0;
    h = hashMix(h);
  }
  return h >>> 0;
}

function entSeed256f(seed256, counter) {
  return entSeed256(seed256, counter) / 0xFFFFFFFF;
}

// ═══════════════════════════════════════════════════════════
// FIX-1: Domain-separated seed derivation for Yin system
// ═══════════════════════════════════════════════════════════

function deriveYinSeed(seed256) {
  var yinSeed = new Array(8);
  var separator = [0x59494E21, 0x4E215949, 0x21594E49, 0x494E2159,
                   0x59214E49, 0x4E494E21, 0x21494E59, 0x59494E49];
  for (var i = 0; i < 8; i++) {
    var h = (seed256[i] ^ separator[i]) >>> 0;
    h = hashMix(h);
    h = (h ^ seed256[(i + 3) % 8]) >>> 0;
    h = hashMix(h);
    h = (h ^ seed256[(i + 5) % 8]) >>> 0;
    h = hashMix(h);
    yinSeed[i] = h >>> 0;
  }
  return yinSeed;
}

// ═══════════════════════════════════════════════════════════
// S-box from pi — deterministic Fisher-Yates (unchanged)
// ═══════════════════════════════════════════════════════════

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
for (var _i = 0; _i < 256; _i++) SBOX_INV[SBOX[_i]] = _i;

// ═══════════════════════════════════════════════════════════
// Organism creation (FIX-4: no history array)
// ═══════════════════════════════════════════════════════════

function createElement(i, seed256) {
  var r = Math.floor(entSeed256f(seed256, i * 100 + 1) * GRID);
  var c = Math.floor(entSeed256f(seed256, i * 100 + 2) * GRID);
  var vr = Math.floor((entSeed256f(seed256, i * 100 + 3) - 0.5) * 2 * 400);
  var vc = Math.floor((entSeed256f(seed256, i * 100 + 4) - 0.5) * 2 * 400);
  return { i: i, name: NAMES[i], row: r, col: c, vr: vr, vc: vc, distance: 0 };
}

// ═══════════════════════════════════════════════════════════
// Wu Xing dynamics (integer arithmetic)
// ═══════════════════════════════════════════════════════════

function computeDynamicForces(organisms) {
  var totalDist = 0;
  for (var i = 0; i < 5; i++) {
    for (var j = i + 1; j < 5; j++) {
      var dr = Math.abs(organisms[i].row - organisms[j].row);
      var dc = Math.abs(organisms[i].col - organisms[j].col);
      dr = Math.min(dr, GRID - dr);
      dc = Math.min(dc, GRID - dc);
      totalDist += Math.sqrt(dr * dr + dc * dc);
    }
  }
  var expansion_1000 = Math.floor(totalDist / (10 * 7.071));
  var gen_1000 = Math.floor((ALPHA_NUM * (1000 + expansion_1000 * 30) * 5) / ALPHA_DEN);
  var inh_1000 = Math.floor((ALPHA_NUM * (1000 + (1000 - expansion_1000) * 30) * 5) / ALPHA_DEN);
  return { generate: gen_1000, inhibit: inh_1000, expansion: expansion_1000 };
}

function moveWuXing(f, all, isYin, fGen, fInh) {
  var pushR = 0, pushC = 0;
  var parent = all[(f.i + 4) % 5];
  pushR += Math.floor((parent.row - f.row) * fGen / (GRID * 10));
  pushC += Math.floor((parent.col - f.col) * fGen / (GRID * 10));

  var ci = -1;
  for (var k = 0; k < 5; k++) {
    if (INHIBITS[k] === f.i) { ci = k; break; }
  }
  if (ci >= 0) {
    pushR -= Math.sign(f.vr) * Math.floor(fInh / 10);
    pushC -= Math.sign(f.vc) * Math.floor(fInh / 10);
  }

  var climateHash = 0;
  for (var k = 0; k < all.length; k++) {
    if (k !== f.i) {
      climateHash = (climateHash ^ Math.imul(all[k].row, 65537) + Math.imul(all[k].col, 257)) >>> 0;
    }
  }
  var m1 = (climateHash ^ Math.imul(f.row, 31337) ^ Math.imul(f.i, 7919)) >>> 0;
  var m2 = (climateHash ^ Math.imul(f.col, 48271) ^ Math.imul(f.i, 6151)) >>> 0;
  var e0 = (m1 % 10000) / 10000;
  var e1 = (m2 % 10000) / 10000;

  var vr, vc;
  if (isYin) {
    vr = f.vr - pushR + Math.floor((e0 - 0.5) * 20);
    vc = f.vc - pushC + Math.floor((e1 - 0.5) * 20);
  } else {
    vr = f.vr + pushR + Math.floor((e0 - 0.5) * 20);
    vc = f.vc + pushC + Math.floor((e1 - 0.5) * 20);
  }

  vr = Math.max(-SPEED_LIMIT, Math.min(SPEED_LIMIT, vr));
  vc = Math.max(-SPEED_LIMIT, Math.min(SPEED_LIMIT, vc));
  var row = ((f.row + vr) % GRID + GRID) % GRID;
  var col = ((f.col + vc) % GRID + GRID) % GRID;
  var dr2 = Math.abs(row - f.row);
  var dc2 = Math.abs(col - f.col);

  return {
    i: f.i, name: f.name,
    row: row, col: col, vr: vr, vc: vc,
    distance: f.distance + Math.sqrt(dr2 * dr2 + dc2 * dc2)
  };
}

function evolveOrganisms(yang, yin) {
  var fY = computeDynamicForces(yang);
  var fI = computeDynamicForces(yin);
  return {
    yang: yang.map(function(f) { return moveWuXing(f, yang, false, fY.generate, fY.inhibit); }),
    yin:  yin.map(function(f) { return moveWuXing(f, yin,  true,  fI.generate, fI.inhibit); })
  };
}

// ═══════════════════════════════════════════════════════════
// Modular inverse
// ═══════════════════════════════════════════════════════════

function modInverse(a, m) {
  var old_r = ((a % m) + m) % m, r = m, old_s = 1, s = 0;
  while (r !== 0) {
    var q = Math.floor(old_r / r);
    var t = r; r = old_r - q * r; old_r = t;
    var ts = s; s = old_s - q * s; old_s = ts;
  }
  if (old_r !== 1) return null;
  return ((old_s % m) + m) % m;
}

// ═══════════════════════════════════════════════════════════
// FIX-3 & FIX-6: Expanded position factor
// ═══════════════════════════════════════════════════════════

function computePositionFactor(pos, yang, yin) {
  var eI = pos % 5;
  var eN = (eI + 1) % 5;
  var eP = (eI + 4) % 5;
  var cycle = Math.floor(pos / 5);

  var dR = Math.abs(yang[eI].row - yin[eI].row);
  var dC = Math.abs(yang[eI].col - yin[eI].col);
  var crossA = Math.abs(yang[eN].col - yin[eP].row);
  var crossB = Math.abs(yang[eP].row - yin[eN].col);
  var crossC = Math.abs(yang[(eI + 2) % 5].row - yin[(eI + 3) % 5].col);

  var stateA = (Math.imul(dR, 65537) ^ Math.imul(crossA, 257) ^ Math.imul(cycle, 131071)) >>> 0;
  var stateB = (Math.imul(dC, 48271) ^ Math.imul(crossB, 6151) ^ Math.imul(cycle, 7919)) >>> 0;
  var stateC = (Math.imul(crossC, 31337) ^ Math.imul(dR + dC, 16411)) >>> 0;

  stateA = hashMix(stateA);
  stateB = hashMix(stateB);
  stateC = hashMix(stateC);

  var mult = (stateA % 256) | 1;
  if (mult < 3) mult += 2;
  var offset = stateB % 256;
  var offset2 = stateC % 256;
  var inv = modInverse(mult, 256);

  return { mult: mult, offset: offset, offset2: offset2, inv: inv };
}

// ═══════════════════════════════════════════════════════════
// FIX-2: 32-bit feedback with multiplicative mixing
// ═══════════════════════════════════════════════════════════

function feedbackMix(feedback32, cipherByte, mult) {
  var f = (feedback32 + cipherByte + 1) >>> 0;
  f = Math.imul(f, 0x9E3779B1) >>> 0;
  f = (f ^ (mult * 0x100 + cipherByte)) >>> 0;
  f = (f ^ (f >>> 17)) >>> 0;
  return f;
}

function feedbackByte(feedback32) {
  return ((feedback32 ^ (feedback32 >>> 8) ^ (feedback32 >>> 16) ^ (feedback32 >>> 24)) & 0xFF);
}

// ═══════════════════════════════════════════════════════════
// UTF-8 helpers
// ═══════════════════════════════════════════════════════════

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

function bytesToStr(plain) {
  var result = "";
  var i = 0;
  while (i < plain.length) {
    var b = plain[i];
    if (b < 0x80) { result += String.fromCharCode(b); i++; }
    else if (b < 0xE0) { result += String.fromCharCode(((b & 0x1F) << 6) | (plain[i + 1] & 0x3F)); i += 2; }
    else { result += String.fromCharCode(((b & 0x0F) << 12) | ((plain[i + 1] & 0x3F) << 6) | (plain[i + 2] & 0x3F)); i += 3; }
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

// ═══════════════════════════════════════════════════════════
// FIX-5: Secure seed generation
// ═══════════════════════════════════════════════════════════

function generateSeed256() {
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    var arr = new Uint32Array(8);
    crypto.getRandomValues(arr);
    return Array.from(arr);
  }
  if (typeof require === 'function') {
    var cr = require('crypto');
    var buf = cr.randomBytes(32);
    var seed = [];
    for (var i = 0; i < 8; i++) seed.push(buf.readUInt32BE(i * 4));
    return seed;
  }
  throw new Error("No CSPRNG available");
}

// ═══════════════════════════════════════════════════════════
// ENCRYPT v3
// ═══════════════════════════════════════════════════════════

function encrypt(message, warmup, seed256) {
  var yinSeed = deriveYinSeed(seed256);
  var yang = NAMES.map(function(_, i) { return createElement(i, seed256); });
  var yin  = NAMES.map(function(_, i) { return createElement(i, yinSeed); });

  for (var b = 0; b < warmup; b++) {
    var ev = evolveOrganisms(yang, yin);
    yang = ev.yang; yin = ev.yin;
  }

  var msgBytes = strToBytes(message);
  var cipher = [];
  var feedback32 = 0;

  for (var i = 0; i < msgBytes.length; i++) {
    var f = computePositionFactor(i, yang, yin);
    var fb = feedbackByte(feedback32);

    var s1 = (((msgBytes[i] ^ fb) * f.mult) + f.offset) % 256;
    var s2 = SBOX[s1];
    var s3 = SBOX[(s2 + f.mult + fb) % 256];
    var s4 = s3 ^ ((f.offset2 * 37 + i) % 256);

    cipher.push(s4);
    feedback32 = feedbackMix(feedback32, s4, f.mult);

    if (i % 5 === 4) {
      var ev = evolveOrganisms(yang, yin);
      yang = ev.yang; yin = ev.yin;
    }
  }

  return { hex: bytesToHex(cipher), seed: seed256, bytes: cipher, plainBytes: msgBytes, warmup: warmup };
}

// ═══════════════════════════════════════════════════════════
// DECRYPT v3
// ═══════════════════════════════════════════════════════════

function decrypt(hexCipher, warmup, seed256) {
  var yinSeed = deriveYinSeed(seed256);
  var yang = NAMES.map(function(_, i) { return createElement(i, seed256); });
  var yin  = NAMES.map(function(_, i) { return createElement(i, yinSeed); });

  for (var b = 0; b < warmup; b++) {
    var ev = evolveOrganisms(yang, yin);
    yang = ev.yang; yin = ev.yin;
  }

  var cBytes = hexToBytes(hexCipher);
  var plain = [];
  var feedback32 = 0;

  for (var i = 0; i < cBytes.length; i++) {
    var f = computePositionFactor(i, yang, yin);
    var fb = feedbackByte(feedback32);

    var s3 = cBytes[i] ^ ((f.offset2 * 37 + i) % 256);
    var s2 = ((SBOX_INV[s3] - f.mult - fb + 256 * 10) % 256);
    var s1 = SBOX_INV[s2];
    var pXor = ((s1 - f.offset + 256 * 10) * f.inv) % 256;
    var p = pXor ^ fb;

    plain.push(p);
    feedback32 = feedbackMix(feedback32, cBytes[i], f.mult);

    if (i % 5 === 4) {
      var ev = evolveOrganisms(yang, yin);
      yang = ev.yang; yin = ev.yin;
    }
  }

  return bytesToStr(plain);
}

// ═══════════════════════════════════════════════════════════
// Self-test
// ═══════════════════════════════════════════════════════════

function selfTest() {
  var seed = generateSeed256();
  var msg = "Test roundtrip 5PSC v3.0 — integrity check! 日本語テスト";
  var enc = encrypt(msg, 100, seed);
  var dec = decrypt(enc.hex, 100, seed);
  var pass = dec === msg;

  var seed2 = generateSeed256();
  var enc2 = encrypt(msg, 100, seed2);
  var crossPass = enc.hex !== enc2.hex;

  var encA = encrypt("A".repeat(200), 100, generateSeed256());
  var unique = new Set(encA.bytes).size;
  var entropyPass = unique > 120;

  return {
    roundtrip: pass,
    crossSeed: crossPass,
    entropy: entropyPass,
    allPass: pass && crossPass && entropyPass,
    message: msg,
    decrypted: dec,
    uniqueBytes: unique
  };
}

// ═══════════════════════════════════════════════════════════
// Exports
// ═══════════════════════════════════════════════════════════

exports.encrypt = encrypt;
exports.decrypt = decrypt;
exports.generateSeed256 = generateSeed256;
exports.selfTest = selfTest;
exports.VERSION = "3.0.0";
exports._deriveYinSeed = deriveYinSeed;
exports._computePositionFactor = computePositionFactor;
exports._SBOX = SBOX;
exports._SBOX_INV = SBOX_INV;

})(typeof module !== 'undefined' ? module.exports : (window.PSC5 = {}));
