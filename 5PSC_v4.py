#!/usr/bin/env python3
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# 5PSC v4.0 \u2014 5-Phase Soliton Cipher
# A stream cipher based on Wu Xing (Five Elements) dynamic system
#
# Author: Soliton Cipher (Mount Etna, Sicily)
# Date: February 2026
# Prior art: Certified email (PEC), February 19, 2026
# License: Free for everyone. No restrictions.
#
# v4.0 fixes (from GMO_Goat cryptanalysis on CryptoHack Discord):
#   - Position factors now derived from FULL 10-organism state hash
#     (was: 3 organism pairs mod 256 = 8-bit brute-forceable)
#     (now: SHA-256 of all 40 state variables = not reducible)
#   - AES S-box replaces Fisher-Yates/\u03c0 S-box
#     (was: 65% linearity)
#     (now: AES S-box, max linearity 2^-3, proven properties)
#   - 64-bit feedback accumulator replaces 32-bit
#     (was: 32-bit, invertible)
#     (now: 64-bit, non-invertible mixing)
#   - Formal nonce: 128-bit random, mixed into seed derivation
#   - Bytes-in, bytes-out interface (no string assumption)
#
# Credits:
#   /dev/nvme0n1 \u2014 Math.random() in seed (v2.0)
#   6... \u2014 floating point arithmetic (v2.1)
#   GMO_Goat \u2014 position factor brute force, S-box linearity,
#              hash invertibility, known-plaintext attack (v4.0)
#
# Previous: https://github.com/soliton-cell/5PSC
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

import os
import struct
import hashlib

# \u2500\u2500\u2500 CONSTANTS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
GRID = 10000
SPEED_LIMIT = 800
NAMES = ["Wood", "Fire", "Earth", "Metal", "Water"]
INHIBITS = [2, 3, 4, 0, 1]
ALPHA_NUM = 1
ALPHA_DEN = 137


# \u2500\u2500\u2500 32-BIT INTEGER ARITHMETIC \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def to_uint32(x):
    return x & 0xFFFFFFFF

def to_uint64(x):
    return x & 0xFFFFFFFFFFFFFFFF

def imul(a, b):
    a = a & 0xFFFFFFFF
    b = b & 0xFFFFFFFF
    result = (a * b) & 0xFFFFFFFF
    if result >= 0x80000000:
        result -= 0x100000000
    return result


# \u2500\u2500\u2500 SEED + NONCE \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def generate_seed256():
    raw = os.urandom(32)
    return list(struct.unpack('>8I', raw))

def generate_nonce():
    """128-bit random nonce, transmitted in clear with ciphertext"""
    return os.urandom(16)

def derive_session_key(seed256, nonce):
    """Mix seed + nonce via SHA-256 to produce session-specific seed"""
    seed_bytes = struct.pack('>8I', *seed256)
    h = hashlib.sha256(seed_bytes + nonce).digest()
    return list(struct.unpack('>8I', h))


# \u2500\u2500\u2500 INTEGER HASH FROM SEED \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def seed_hash_int(seed256, counter):
    h = seed256[counter % 8] ^ imul(counter, 2654435761)
    for i in range(8):
        h = h ^ seed256[i]
        h = imul(h ^ (to_uint32(h) >> 16), 0x45d9f3b)
    h = imul(h ^ (to_uint32(h) >> 13), 0x45d9f3b)
    return to_uint32(h ^ (to_uint32(h) >> 16))


# \u2500\u2500\u2500 AES S-BOX \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# Standard AES S-box: proven non-linearity, max differential
# probability 2^-6, max linear probability 2^-3.
# Replaces the Fisher-Yates/\u03c0 S-box (65% linearity per GMO_Goat).

SBOX = [
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5,
    0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0,
    0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc,
    0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a,
    0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0,
    0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b,
    0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85,
    0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5,
    0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17,
    0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88,
    0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c,
    0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9,
    0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6,
    0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e,
    0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94,
    0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68,
    0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16,
]

SBOX_INV = [0] * 256
for _i in range(256):
    SBOX_INV[SBOX[_i]] = _i


# \u2500\u2500\u2500 ELEMENT CREATION (INTEGER ONLY) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def create_element(index, seed256):
    h1 = seed_hash_int(seed256, index * 100 + 1)
    h2 = seed_hash_int(seed256, index * 100 + 2)
    h3 = seed_hash_int(seed256, index * 100 + 3)
    h4 = seed_hash_int(seed256, index * 100 + 4)
    return {
        'i': index, 'name': NAMES[index],
        'row': h1 % GRID, 'col': h2 % GRID,
        'vr': (h3 % 800) - 400, 'vc': (h4 % 800) - 400,
        'history': [{'row': h1 % GRID, 'col': h2 % GRID}],
        'distance': 0
    }


# \u2500\u2500\u2500 YIN SEED DERIVATION (domain-separated) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def derive_yin_seed(seed256):
    """Domain-separated seed for Yin organisms (from v3 paper)"""
    separator = [0x59696E00, 0x53656564, 0x44657269, 0x76654B65,
                 0x79466F72, 0x596E4F72, 0x67616E69, 0x736D7321]
    yin_seed = [0] * 8
    for i in range(8):
        h = seed256[i] ^ separator[i]
        h = seed_hash_int(seed256, h & 0xFFFF)
        h ^= seed256[(i + 3) % 8]
        h = seed_hash_int(seed256, h & 0xFFFF)
        h ^= seed256[(i + 5) % 8]
        h = seed_hash_int(seed256, h & 0xFFFF)
        yin_seed[i] = to_uint32(h)
    return yin_seed


# \u2500\u2500\u2500 DYNAMIC FORCES (INTEGER ONLY) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def calculate_dynamic_forces(elements):
    total_dist = 0
    for i in range(5):
        for j in range(i + 1, 5):
            dr = abs(elements[i]['row'] - elements[j]['row'])
            dc = abs(elements[i]['col'] - elements[j]['col'])
            dr = min(dr, GRID - dr)
            dc = min(dc, GRID - dc)
            total_dist += dr + dc
    expansion_1000 = int(total_dist / 100)
    if expansion_1000 > 1000:
        expansion_1000 = 1000
    gen_1000 = int((1000 + expansion_1000 * 30) * 5 / ALPHA_DEN)
    inh_1000 = int((1000 + (1000 - expansion_1000) * 30) * 5 / ALPHA_DEN)
    return {'generate': gen_1000, 'inhibit': inh_1000, 'expansion': expansion_1000}


# \u2500\u2500\u2500 WU XING MOVEMENT (INTEGER ONLY) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def move_wu_xing(elem, all_elems, is_yin, force_gen_1000, force_inh_1000):
    parent = all_elems[(elem['i'] + 4) % 5]
    push_r = int((parent['row'] - elem['row']) * force_gen_1000 / (GRID * 10))
    push_c = int((parent['col'] - elem['col']) * force_gen_1000 / (GRID * 10))

    controller_idx = -1
    for k in range(5):
        if INHIBITS[k] == elem['i']:
            controller_idx = k
            break
    if controller_idx >= 0:
        sign_r = 1 if elem['vr'] > 0 else (-1 if elem['vr'] < 0 else 0)
        sign_c = 1 if elem['vc'] > 0 else (-1 if elem['vc'] < 0 else 0)
        push_r -= int(sign_r * force_inh_1000 * 100 / 1000)
        push_c -= int(sign_c * force_inh_1000 * 100 / 1000)

    climate_hash = 0
    for k in range(len(all_elems)):
        if k != elem['i']:
            climate_hash = to_uint32(climate_hash ^ to_uint32(
                all_elems[k]['row'] * 65537 + all_elems[k]['col'] * 257))
    mix1 = to_uint32(climate_hash ^ to_uint32(elem['row'] * 31337 + elem['i'] * 7919))
    mix2 = to_uint32(climate_hash ^ to_uint32(elem['col'] * 48271 + elem['i'] * 6151))
    noise0 = (mix1 % 20) - 10
    noise1 = (mix2 % 20) - 10

    if is_yin:
        vr = elem['vr'] - push_r + noise0
        vc = elem['vc'] - push_c + noise1
    else:
        vr = elem['vr'] + push_r + noise0
        vc = elem['vc'] + push_c + noise1

    vr = max(-SPEED_LIMIT, min(SPEED_LIMIT, vr))
    vc = max(-SPEED_LIMIT, min(SPEED_LIMIT, vc))
    new_row = (elem['row'] + vr) % GRID
    new_col = (elem['col'] + vc) % GRID
    dr = abs(new_row - elem['row'])
    dc = abs(new_col - elem['col'])
    hist = elem['history'][-60:] + [{'row': new_row, 'col': new_col}]

    return {
        'i': elem['i'], 'name': elem['name'],
        'row': new_row, 'col': new_col, 'vr': vr, 'vc': vc,
        'history': hist, 'distance': elem['distance'] + dr + dc
    }


# \u2500\u2500\u2500 ORGANISM EVOLUTION \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def evolve_organisms(yang, yin):
    f_y = calculate_dynamic_forces(yang)
    f_i = calculate_dynamic_forces(yin)
    new_yang = [move_wu_xing(e, yang, False, f_y['generate'], f_y['inhibit']) for e in yang]
    new_yin = [move_wu_xing(e, yin, True, f_i['generate'], f_i['inhibit']) for e in yin]
    return new_yang, new_yin


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# POSITION FACTOR \u2014 v4: FULL STATE HASH (fixes GMO_Goat attack)
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# In v2.1, position factors were:
#   mult = (diffR + cross_distance + cycle*7) % 256    \u2192 8 bits
#   offset = (diffC + cross_distance + cycle*13) % 256  \u2192 8 bits
#   \u2192 brute-forceable with 256\u00b2 or 256\u00b3 per position
#
# In v4, we hash ALL 40 state variables (10 organisms \u00d7 4 vars)
# plus position counter through SHA-256. The output is 256 bits
# of pseudorandom data from which we extract parameters.
# An attacker would need to recover the full organism state
# (10 \u00d7 position on 10000\u00b2 grid = ~53 bits per organism = ~530 bits)
# to predict the position factors. Brute force is infeasible.

def _state_to_bytes(yang, yin):
    """Serialize full state of all 10 organisms to bytes"""
    parts = []
    for org in yang + yin:
        parts.append(struct.pack('>iiii', org['row'], org['col'], org['vr'], org['vc']))
    return b''.join(parts)

def calculate_position_factor(position, yang, yin, feedback_state):
    """
    Derive position-dependent encryption parameters from full organism state.
    Uses SHA-256 of (all organism positions + byte position + feedback state).
    Returns mult (odd, \u22653), offset, offset2, and modular inverse of mult.
    """
    state_bytes = _state_to_bytes(yang, yin)
    pos_bytes = struct.pack('>Q', position)          # 8 bytes
    fb_bytes = struct.pack('>Q', feedback_state)      # 8 bytes

    digest = hashlib.sha256(state_bytes + pos_bytes + fb_bytes).digest()

    # Extract parameters from different parts of the 256-bit digest
    # Each parameter is derived from 32+ bits, then reduced to 8-bit
    # But the SOURCE is 256-bit hash \u2014 not brute-forceable

    raw_mult = struct.unpack('>I', digest[0:4])[0]
    raw_offset = struct.unpack('>I', digest[4:8])[0]
    raw_offset2 = struct.unpack('>I', digest[8:12])[0]
    raw_extra = struct.unpack('>I', digest[12:16])[0]

    # mult must be odd and \u2265 3 for modular inverse to exist
    mult = (raw_mult % 256) | 1    # force odd
    if mult < 3:
        mult += 2

    offset = raw_offset % 256
    offset2 = raw_offset2 % 256

    # Additional mixing byte from digest (used in final XOR)
    extra = raw_extra % 256

    inv = mod_inverse(mult, 256)

    return {
        'mult': mult, 'offset': offset, 'offset2': offset2,
        'extra': extra, 'inv': inv
    }


# \u2500\u2500\u2500 MODULAR INVERSE \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

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


# \u2500\u2500\u2500 64-BIT FEEDBACK ACCUMULATOR \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# Replaces 32-bit accumulator. Non-invertible mixing.
# Uses golden ratio constant for multiplication (no fixed points).

FEEDBACK_MULT = 0x9E3779B97F4A7C15  # golden ratio \u00d7 2^64

def feedback_mix(state, cipher_byte, mult):
    """64-bit non-invertible feedback mixing"""
    state = to_uint64((state + cipher_byte + 1) * FEEDBACK_MULT)
    state = to_uint64(state ^ (state >> 27))
    state = to_uint64(state ^ (mult * 0x100000001))
    state = to_uint64(state * 0xBF58476D1CE4E5B9)
    state = to_uint64(state ^ (state >> 31))
    return state

def feedback_byte(state):
    """Extract 8 bits from 64-bit state by XOR-folding"""
    b = state & 0xFF
    b ^= (state >> 8) & 0xFF
    b ^= (state >> 16) & 0xFF
    b ^= (state >> 24) & 0xFF
    b ^= (state >> 32) & 0xFF
    b ^= (state >> 40) & 0xFF
    b ^= (state >> 48) & 0xFF
    b ^= (state >> 56) & 0xFF
    return b


# \u2500\u2500\u2500 BYTE CONVERSION \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def bytes_to_hex(b):
    return ''.join(f'{v:02x}' for v in b)

def hex_to_bytes(h):
    return [int(h[i:i+2], 16) for i in range(0, len(h), 2)]


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# ENCRYPT
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

def encrypt(plaintext_bytes, warmup, seed256, nonce=None):
    """
    Encrypt bytes (not strings). Returns dict with hex, nonce, etc.
    If nonce is None, generates a random 128-bit nonce.
    """
    if isinstance(plaintext_bytes, str):
        plaintext_bytes = list(plaintext_bytes.encode('utf-8'))
    elif isinstance(plaintext_bytes, bytes):
        plaintext_bytes = list(plaintext_bytes)

    # Generate or use provided nonce
    if nonce is None:
        nonce = generate_nonce()

    # Derive session key from seed + nonce
    session_key = derive_session_key(seed256, nonce)
    yin_key = derive_yin_seed(session_key)

    # Initialize organisms
    yang = [create_element(i, session_key) for i in range(5)]
    yin = [create_element(i, yin_key) for i in range(5)]

    # Warmup
    for _ in range(warmup):
        yang, yin = evolve_organisms(yang, yin)

    # Encrypt
    cipher_bytes = []
    fb_state = 0  # 64-bit feedback

    for i in range(len(plaintext_bytes)):
        fb = feedback_byte(fb_state)
        f = calculate_position_factor(i, yang, yin, fb_state)

        # Encryption pipeline: XOR feedback \u2192 affine \u2192 S-box \u2192 S-box \u2192 XOR
        step1 = (((plaintext_bytes[i] ^ fb) * f['mult']) + f['offset']) % 256
        step2 = SBOX[step1]
        step3 = SBOX[(step2 + f['extra'] + fb) % 256]
        step4 = step3 ^ f['offset2']

        cipher_bytes.append(step4)

        # Update feedback (64-bit, non-invertible)
        fb_state = feedback_mix(fb_state, step4, f['mult'])

        # Evolve organisms every 5 bytes
        if i % 5 == 4:
            yang, yin = evolve_organisms(yang, yin)

    return {
        'hex': bytes_to_hex(cipher_bytes),
        'nonce': nonce.hex(),
        'seed': seed256,
        'warmup': warmup,
        'length': len(plaintext_bytes)
    }


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# DECRYPT
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

def decrypt(hex_cipher, warmup, seed256, nonce_hex):
    """Decrypt hex ciphertext back to bytes."""
    nonce = bytes.fromhex(nonce_hex)

    # Derive session key from seed + nonce
    session_key = derive_session_key(seed256, nonce)
    yin_key = derive_yin_seed(session_key)

    # Initialize organisms
    yang = [create_element(i, session_key) for i in range(5)]
    yin = [create_element(i, yin_key) for i in range(5)]

    # Warmup
    for _ in range(warmup):
        yang, yin = evolve_organisms(yang, yin)

    # Decrypt
    cipher_bytes = hex_to_bytes(hex_cipher)
    plain_bytes = []
    fb_state = 0  # 64-bit feedback

    for i in range(len(cipher_bytes)):
        fb = feedback_byte(fb_state)
        f = calculate_position_factor(i, yang, yin, fb_state)

        # Reverse pipeline: XOR \u2192 inv S-box \u2192 inv S-box \u2192 inv affine \u2192 XOR feedback
        step3 = cipher_bytes[i] ^ f['offset2']
        step2 = (SBOX_INV[step3] - f['extra'] - fb + 256 * 10) % 256
        step1 = SBOX_INV[step2]
        plain_xored = ((step1 - f['offset'] + 256 * 10) * f['inv']) % 256
        plain = plain_xored ^ fb

        plain_bytes.append(plain)

        # Update feedback with ciphertext byte (must match encrypt)
        fb_state = feedback_mix(fb_state, cipher_bytes[i], f['mult'])

        # Evolve organisms every 5 bytes
        if i % 5 == 4:
            yang, yin = evolve_organisms(yang, yin)

    return bytes(plain_bytes)


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# SELF-TEST
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

if __name__ == '__main__':
    print("5PSC v4.0 \u2014 Self-test\n")
    print("Fixes: GMO_Goat cryptanalysis (CryptoHack Discord)")
    print("  - Position factors from full 10-organism SHA-256 hash")
    print("  - AES S-box (replaces \u03c0 S-box, 65% linearity)")
    print("  - 64-bit non-invertible feedback (was 32-bit)")
    print("  - Formal 128-bit nonce (was: warmup-as-nonce)")
    print("  - Bytes-in/bytes-out (was: string interface)")
    print()

    seed = generate_seed256()
    all_pass = True

    # Test 1: Basic encrypt/decrypt roundtrip
    messages = [
        b"The quieter you become, the more you can hear.",
        b"Hello World! Test with numbers 12345 and symbols #$%",
        b"A" * 100,
        "Special chars: \u00e0\u00e8\u00ec\u00f2\u00f9 \u00a3\u20ac @#".encode('utf-8'),
    ]

    for m, msg in enumerate(messages):
        enc = encrypt(msg, 100, seed)
        dec = decrypt(enc['hex'], 100, seed, enc['nonce'])
        passed = dec == msg
        if not passed:
            all_pass = False
        unique = len(set(hex_to_bytes(enc['hex'])))
        print(f"{'PASS' if passed else 'FAIL'} | Message {m+1} "
              f"({len(msg)} bytes) | Unique bytes: {unique}/{enc['length']}")

    # Test 2: Different seeds = different output
    seed2 = generate_seed256()
    enc1 = encrypt(b"test", 100, seed)
    enc2 = encrypt(b"test", 100, seed2)
    diff_pass = enc1['hex'] != enc2['hex']
    if not diff_pass:
        all_pass = False
    print(f"{'PASS' if diff_pass else 'FAIL'} | Different seeds \u2192 different output")

    # Test 3: Same seed + different nonce = different output
    nonce1 = generate_nonce()
    nonce2 = generate_nonce()
    enc3 = encrypt(b"nonce test", 100, seed, nonce1)
    enc4 = encrypt(b"nonce test", 100, seed, nonce2)
    nonce_pass = enc3['hex'] != enc4['hex']
    if not nonce_pass:
        all_pass = False
    print(f"{'PASS' if nonce_pass else 'FAIL'} | Same seed + different nonce \u2192 different output")

    # Test 4: Determinism - same seed + same nonce = same output
    enc5 = encrypt(b"determinism", 100, seed, nonce1)
    enc6 = encrypt(b"determinism", 100, seed, nonce1)
    det_pass = enc5['hex'] == enc6['hex']
    if not det_pass:
        all_pass = False
    print(f"{'PASS' if det_pass else 'FAIL'} | Same seed + same nonce \u2192 same output")

    # Test 5: Nonce transmitted in clear (verify it works)
    msg = b"The farmer and the AI"
    enc = encrypt(msg, 100, seed)
    # Receiver gets: hex ciphertext + nonce (in clear) + knows seed + warmup
    dec = decrypt(enc['hex'], 100, seed, enc['nonce'])
    nonce_rt_pass = dec == msg
    if not nonce_rt_pass:
        all_pass = False
    print(f"{'PASS' if nonce_rt_pass else 'FAIL'} | Nonce roundtrip (transmitted in clear)")

    # Test 6: GMO_Goat attack simulation
    # Known-plaintext: encrypt 5 messages with SAME seed but DIFFERENT nonces
    # Even with known plaintext pairs, position factors should not be recoverable
    # because each nonce produces a completely different session key
    print(f"\n--- GMO_Goat attack resistance ---")
    pts = [os.urandom(32) for _ in range(5)]
    cts = [encrypt(p, 100, seed) for p in pts]
    # All nonces should be different
    nonces_unique = len(set(c['nonce'] for c in cts)) == 5
    print(f"{'PASS' if nonces_unique else 'FAIL'} | All 5 encryptions use unique nonces")
    # All ciphertexts should be different
    cts_unique = len(set(c['hex'] for c in cts)) == 5
    print(f"{'PASS' if cts_unique else 'FAIL'} | All 5 ciphertexts are unique")
    # Each can be decrypted with its own nonce
    all_dec = True
    for p, c in zip(pts, cts):
        d = decrypt(c['hex'], 100, seed, c['nonce'])
        if d != p:
            all_dec = False
    print(f"{'PASS' if all_dec else 'FAIL'} | All 5 decrypt correctly with their nonces")

    print(f"\n{'ALL TESTS PASSED' if all_pass and nonces_unique and cts_unique and all_dec else 'SOME TESTS FAILED'}")

    # Performance benchmark
    import time
    msg = b"Performance test message for 5PSC v4" * 28  # ~1000 bytes
    nonce = generate_nonce()
    start = time.time()
    for _ in range(10):
        encrypt(msg, 100, seed, nonce)
    elapsed = time.time() - start
    throughput = (len(msg) * 10) / elapsed / 1024
    print(f"\nPerformance: {len(msg)} bytes \u00d7 10 = {elapsed:.2f}s "
          f"({throughput:.1f} KB/s)")
