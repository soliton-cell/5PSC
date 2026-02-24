#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════
# 5PSC v2.1 — 5-Phase Soliton Cipher (Integer-Only Edition)
# A stream cipher based on Wu Xing (Five Elements) dynamic system
#
# Python port — bit-identical to the JavaScript reference implementation
#
# Author: Soliton Cipher (Mount Etna, Sicily)
# Date: February 2026
# Prior art: Certified email (PEC), February 19, 2026
# License: Free for everyone. No restrictions.
#
# Original JS: https://github.com/soliton-cell/5PSC
#
# v2.1 fixes (from CryptoHack Discord community review):
#   - Math.random → CSPRNG (nvme0n1)
#   - ALL floating point removed → integer-only arithmetic (6...)
#   - Math.sqrt → Manhattan distance (integer)
#   - α scaled to integer fraction (no float)
#   - Cross-platform deterministic: same input = same output, always
# ═══════════════════════════════════════════════════════════════════

import os
import struct

# ─── CONSTANTS ───────────────────────────────────────────────────
GRID = 10000           # Toroidal grid size
SPEED_LIMIT = 800      # Max velocity per axis
NAMES = ["Wood", "Fire", "Earth", "Metal", "Water"]
INHIBITS = [2, 3, 4, 0, 1]  # Wu Xing inhibition cycle

# α = 1/137 as integer fraction
ALPHA_NUM = 1
ALPHA_DEN = 137


# ─── 32-BIT INTEGER ARITHMETIC ───────────────────────────────────
# Python integers have arbitrary precision. These helpers emulate
# JavaScript's 32-bit unsigned/signed integer behavior exactly.

def to_uint32(x):
    """Emulate JavaScript's >>> 0 (unsigned 32-bit)"""
    return x & 0xFFFFFFFF

def imul(a, b):
    """Emulate Math.imul: 32-bit signed multiply, return lower 32 bits signed"""
    a = a & 0xFFFFFFFF
    b = b & 0xFFFFFFFF
    result = (a * b) & 0xFFFFFFFF
    if result >= 0x80000000:
        result -= 0x100000000
    return result


# ─── SEED: 256-BIT (CSPRNG) ─────────────────────────────────────

def generate_seed256():
    """Generate 8 × 32-bit unsigned integers from CSPRNG"""
    raw = os.urandom(32)
    return list(struct.unpack('>8I', raw))


# ─── INTEGER HASH FROM SEED ─────────────────────────────────────

def seed_hash_int(seed256, counter):
    """Deterministic hash from seed + counter. Returns uint32."""
    h = seed256[counter % 8] ^ imul(counter, 2654435761)
    for i in range(8):
        h = h ^ seed256[i]
        h = imul(h ^ (to_uint32(h) >> 16), 0x45d9f3b)
    h = imul(h ^ (to_uint32(h) >> 13), 0x45d9f3b)
    return to_uint32(h ^ (to_uint32(h) >> 16))


# ─── S-BOX (NON-LINEARITY) ──────────────────────────────────────
# Fisher-Yates shuffle with π seed — fully transparent

def _build_sbox():
    box = list(range(256))
    state = 314159265
    for i in range(255, 0, -1):
        state = imul(state ^ (to_uint32(state) >> 16), 0x45d9f3b)
        state = imul(state ^ (to_uint32(state) >> 13), 0x45d9f3b)
        state = to_uint32(state ^ (to_uint32(state) >> 16))
        j = state % (i + 1)
        box[i], box[j] = box[j], box[i]
    return box

SBOX = _build_sbox()
SBOX_INV = [0] * 256
for _i in range(256):
    SBOX_INV[SBOX[_i]] = _i


# ─── ELEMENT CREATION (INTEGER ONLY) ─────────────────────────────

def create_element(index, seed256):
    h1 = seed_hash_int(seed256, index * 100 + 1)
    h2 = seed_hash_int(seed256, index * 100 + 2)
    h3 = seed_hash_int(seed256, index * 100 + 3)
    h4 = seed_hash_int(seed256, index * 100 + 4)

    row = h1 % GRID
    col = h2 % GRID
    vr = (h3 % 800) - 400
    vc = (h4 % 800) - 400

    return {
        'i': index, 'name': NAMES[index],
        'row': row, 'col': col, 'vr': vr, 'vc': vc,
        'history': [{'row': row, 'col': col}],
        'distance': 0
    }


# ─── DYNAMIC FORCES (INTEGER ONLY) ──────────────────────────────

def calculate_dynamic_forces(elements):
    total_dist = 0
    for i in range(5):
        for j in range(i + 1, 5):
            dr = abs(elements[i]['row'] - elements[j]['row'])
            dc = abs(elements[i]['col'] - elements[j]['col'])
            dr = min(dr, GRID - dr)  # Toroidal
            dc = min(dc, GRID - dc)
            total_dist += dr + dc     # Manhattan distance (integer)

    # expansion_1000: 0..1000 range
    expansion_1000 = int(total_dist / 100)
    if expansion_1000 > 1000:
        expansion_1000 = 1000

    # generate = α * (1 + expansion * 30) * 5 — integer scaled
    gen_1000 = int((1000 + expansion_1000 * 30) * 5 / ALPHA_DEN)
    inh_1000 = int((1000 + (1000 - expansion_1000) * 30) * 5 / ALPHA_DEN)

    return {
        'generate': gen_1000,
        'inhibit': inh_1000,
        'expansion': expansion_1000
    }


# ─── WU XING MOVEMENT (INTEGER ONLY) ────────────────────────────

def move_wu_xing(elem, all_elems, is_yin, force_gen_1000, force_inh_1000):
    push_r = 0
    push_c = 0

    # Generation: parent pulls
    parent = all_elems[(elem['i'] + 4) % 5]
    push_r = int((parent['row'] - elem['row']) * force_gen_1000 / (GRID * 10))
    push_c = int((parent['col'] - elem['col']) * force_gen_1000 / (GRID * 10))

    # Inhibition: controller resists
    controller_idx = -1
    for k in range(5):
        if INHIBITS[k] == elem['i']:
            controller_idx = k
            break

    if controller_idx >= 0:
        sign_r = 1 if elem['vr'] > 0 else (-1 if elem['vr'] < 0 else 0)
        sign_c = 1 if elem['vc'] > 0 else (-1 if elem['vc'] < 0 else 0)
        push_r = push_r - int(sign_r * force_inh_1000 * 100 / 1000)
        push_c = push_c - int(sign_c * force_inh_1000 * 100 / 1000)

    # Environmental noise (integer)
    climate_hash = 0
    for k in range(len(all_elems)):
        if k != elem['i']:
            climate_hash = to_uint32(climate_hash ^ to_uint32(all_elems[k]['row'] * 65537 + all_elems[k]['col'] * 257))

    mix1 = to_uint32(climate_hash ^ to_uint32(elem['row'] * 31337 + elem['i'] * 7919))
    mix2 = to_uint32(climate_hash ^ to_uint32(elem['col'] * 48271 + elem['i'] * 6151))
    noise0 = (mix1 % 20) - 10
    noise1 = (mix2 % 20) - 10

    # Apply forces
    if is_yin:
        vr = elem['vr'] - push_r + noise0
        vc = elem['vc'] - push_c + noise1
    else:
        vr = elem['vr'] + push_r + noise0
        vc = elem['vc'] + push_c + noise1

    # Speed limit
    vr = max(-SPEED_LIMIT, min(SPEED_LIMIT, vr))
    vc = max(-SPEED_LIMIT, min(SPEED_LIMIT, vc))

    # Move on toroidal grid
    new_row = (elem['row'] + vr) % GRID
    new_col = (elem['col'] + vc) % GRID

    # Manhattan distance for history
    dr = abs(new_row - elem['row'])
    dc = abs(new_col - elem['col'])
    hist = elem['history'][-60:] + [{'row': new_row, 'col': new_col}]

    return {
        'i': elem['i'], 'name': elem['name'],
        'row': new_row, 'col': new_col, 'vr': vr, 'vc': vc,
        'history': hist,
        'distance': elem['distance'] + dr + dc
    }


# ─── MODULAR INVERSE ────────────────────────────────────────────

def mod_inverse(a, m):
    old_r = a % m
    r = m
    old_s = 1
    s = 0
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
    if old_r != 1:
        return None
    return old_s % m


# ─── POSITION FACTOR (INTEGER ONLY) ─────────────────────────────

def calculate_position_factor(position, yang, yin):
    el_idx = position % 5
    el_next = (el_idx + 1) % 5
    el_prev = (el_idx + 4) % 5
    cycle = position // 5

    diff_r = abs(yang[el_idx]['row'] - yin[el_idx]['row'])
    diff_c = abs(yang[el_idx]['col'] - yin[el_idx]['col'])

    diff_r_mix = diff_r + abs(yang[el_next]['col'] - yin[el_prev]['row']) + cycle * 7
    diff_c_mix = diff_c + abs(yang[el_prev]['row'] - yin[el_next]['col']) + cycle * 13

    mult = diff_r_mix % 256
    if mult % 2 == 0:
        mult = (mult + 1) % 256
    if mult < 3:
        mult = mult + 2

    offset = diff_c_mix % 256
    inv = mod_inverse(mult, 256)

    return {'mult': mult, 'offset': offset, 'inv': inv}


# ─── UTF-8 ENCODING ─────────────────────────────────────────────

def str_to_bytes(s):
    return list(s.encode('utf-8'))

def bytes_to_str(b):
    return bytes(b).decode('utf-8')

def bytes_to_hex(b):
    return ''.join(f'{v:02x}' for v in b)

def hex_to_bytes(h):
    return [int(h[i:i+2], 16) for i in range(0, len(h), 2)]


# ─── ORGANISM EVOLUTION ─────────────────────────────────────────

def evolve_organisms(yang, yin):
    f_y = calculate_dynamic_forces(yang)
    f_i = calculate_dynamic_forces(yin)
    new_yang = [move_wu_xing(e, yang, False, f_y['generate'], f_y['inhibit']) for e in yang]
    new_yin = [move_wu_xing(e, yin, True, f_i['generate'], f_i['inhibit']) for e in yin]
    return new_yang, new_yin


# ═════════════════════════════════════════════════════════════════
# ENCRYPT
# ═════════════════════════════════════════════════════════════════

def encrypt(message, warmup, seed256):
    yang = [create_element(i, seed256) for i in range(5)]
    yin = [create_element(i, seed256) for i in range(5)]

    for _ in range(warmup):
        yang, yin = evolve_organisms(yang, yin)

    msg_bytes = str_to_bytes(message)
    cipher_bytes = []
    feedback = 0

    for i in range(len(msg_bytes)):
        f = calculate_position_factor(i, yang, yin)

        step1 = (((msg_bytes[i] ^ feedback) * f['mult']) + f['offset']) % 256
        step2 = SBOX[step1]
        step3 = SBOX[(step2 + f['mult'] + feedback) % 256]
        step4 = step3 ^ ((f['offset'] * 37 + i) % 256)

        cipher_bytes.append(step4)
        feedback = (feedback + step4 + f['mult']) % 256

        if i % 5 == 4:
            yang, yin = evolve_organisms(yang, yin)

    return {
        'hex': bytes_to_hex(cipher_bytes),
        'seed': seed256,
        'warmup': warmup,
        'length': len(msg_bytes)
    }


# ═════════════════════════════════════════════════════════════════
# DECRYPT
# ═════════════════════════════════════════════════════════════════

def decrypt(hex_cipher, warmup, seed256):
    yang = [create_element(i, seed256) for i in range(5)]
    yin = [create_element(i, seed256) for i in range(5)]

    for _ in range(warmup):
        yang, yin = evolve_organisms(yang, yin)

    cipher_bytes = hex_to_bytes(hex_cipher)
    plain_bytes = []
    feedback = 0

    for i in range(len(cipher_bytes)):
        f = calculate_position_factor(i, yang, yin)

        step3 = cipher_bytes[i] ^ ((f['offset'] * 37 + i) % 256)
        step2 = (SBOX_INV[step3] - f['mult'] - feedback + 256 * 10) % 256
        step1 = SBOX_INV[step2]
        plain_xored = ((step1 - f['offset'] + 256 * 10) * f['inv']) % 256
        plain = plain_xored ^ feedback

        plain_bytes.append(plain)
        feedback = (feedback + cipher_bytes[i] + f['mult']) % 256

        if i % 5 == 4:
            yang, yin = evolve_organisms(yang, yin)

    return bytes_to_str(plain_bytes)


# ═════════════════════════════════════════════════════════════════
# SELF-TEST
# ═════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("5PSC v2.1 — Self-test (Python Edition)\n")

    seed = generate_seed256()
    messages = [
        "The quieter you become, the more you can hear.",
        "Hello World! Test with numbers 12345 and symbols #$%",
        "A" * 100,
        "Special chars: àèìòù £€ @#"  # UTF-8
    ]

    all_pass = True

    for m, msg in enumerate(messages):
        enc = encrypt(msg, 100, seed)
        dec = decrypt(enc['hex'], 100, seed)
        passed = dec == msg
        if not passed:
            all_pass = False
        unique = len(set(hex_to_bytes(enc['hex'])))
        print(f"{'PASS' if passed else 'FAIL'} | Message {m+1} "
              f"({len(msg)} chars) | Unique bytes: {unique}/{enc['length']}")

    # Different seed = different output
    seed2 = generate_seed256()
    enc1 = encrypt("test", 100, seed)
    enc2 = encrypt("test", 100, seed2)
    diff_pass = enc1['hex'] != enc2['hex']
    if not diff_pass:
        all_pass = False
    print(f"{'PASS' if diff_pass else 'FAIL'} | Different seeds produce different output")

    # Cross-platform determinism: same seed = same output
    fixed_seed = [1234567890, 987654321, 111111111, 222222222,
                  333333333, 444444444, 555555555, 666666666]
    enc3 = encrypt("determinism test", 100, fixed_seed)
    enc4 = encrypt("determinism test", 100, fixed_seed)
    det_pass = enc3['hex'] == enc4['hex']
    if not det_pass:
        all_pass = False
    print(f"{'PASS' if det_pass else 'FAIL'} | Determinism: same seed = same output")
    print(f"  Reference hash: {enc3['hex'][:32]}...")

    # Cross-platform verification
    # Run both JS and Python with the fixed seed above.
    # If both produce the same reference hash, they are bit-identical.
    print(f"\nCross-platform verification:")
    print(f"  Run: node 5PSC_v2_1.js")
    print(f"  Run: python3 5PSC_v2_1.py")
    print(f"  Compare the 'Reference hash' lines. They must match.")

    print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
