"""
5PSC v3.0 — 5-Phase Soliton Cipher
Python reference implementation

CHANGELOG v3.0: See README.md for full details.
  FIX-1: Yin domain-separated seed derivation
  FIX-2: 32-bit feedback with multiplicative mixing
  FIX-3: Expanded position factor parameter space
  FIX-4: History array removed
  FIX-5: CSPRNG-only seed generation
  FIX-6: Hash-mixed mult/offset distribution
"""
import math
import os

GRID = 10000
SPEED_LIMIT = 800
ALPHA_NUM = 100000
ALPHA_DEN = 13703600
NAMES = ["Wood", "Fire", "Earth", "Metal", "Water"]
INHIBITS = [2, 3, 4, 0, 1]


def _imul(a, b):
    """Emulate JavaScript Math.imul — 32-bit integer multiply"""
    return ((a & 0xFFFFFFFF) * (b & 0xFFFFFFFF)) & 0xFFFFFFFF


def _hash_mix(h):
    h = _imul(h ^ ((h >> 16) & 0xFFFF), 0x45d9f3b)
    h = _imul(h ^ ((h >> 13) & 0x7FFFF), 0x45d9f3b)
    return (h ^ ((h >> 16) & 0xFFFF)) & 0xFFFFFFFF


def ent_seed256(seed256, counter):
    h = (seed256[counter % 8] ^ _imul(counter, 2654435761)) & 0xFFFFFFFF
    for i in range(8):
        h = (h ^ seed256[i]) & 0xFFFFFFFF
        h = _hash_mix(h)
    return h & 0xFFFFFFFF


def ent_seed256f(seed256, counter):
    return ent_seed256(seed256, counter) / 0xFFFFFFFF


# FIX-1: Domain-separated seed for Yin system
def derive_yin_seed(seed256):
    separator = [0x59494E21, 0x4E215949, 0x21594E49, 0x494E2159,
                 0x59214E49, 0x4E494E21, 0x21494E59, 0x59494E49]
    yin_seed = []
    for i in range(8):
        h = (seed256[i] ^ separator[i]) & 0xFFFFFFFF
        h = _hash_mix(h)
        h = (h ^ seed256[(i + 3) % 8]) & 0xFFFFFFFF
        h = _hash_mix(h)
        h = (h ^ seed256[(i + 5) % 8]) & 0xFFFFFFFF
        h = _hash_mix(h)
        yin_seed.append(h & 0xFFFFFFFF)
    return yin_seed


# S-box from pi
def _build_sbox():
    box = list(range(256))
    state = 314159265
    for i in range(255, 0, -1):
        state = _imul(state ^ ((state >> 16) & 0xFFFF), 0x45d9f3b)
        state = _imul(state ^ ((state >> 13) & 0x7FFFF), 0x45d9f3b)
        state = (state ^ ((state >> 16) & 0xFFFF)) & 0xFFFFFFFF
        j = state % (i + 1)
        box[i], box[j] = box[j], box[i]
    return box


SBOX = _build_sbox()
SBOX_INV = [0] * 256
for _i in range(256):
    SBOX_INV[SBOX[_i]] = _i


# FIX-4: No history array
def create_element(i, seed256):
    r = int(ent_seed256f(seed256, i * 100 + 1) * GRID)
    c = int(ent_seed256f(seed256, i * 100 + 2) * GRID)
    vr = int((ent_seed256f(seed256, i * 100 + 3) - 0.5) * 2 * 400)
    vc = int((ent_seed256f(seed256, i * 100 + 4) - 0.5) * 2 * 400)
    return {'i': i, 'name': NAMES[i], 'row': r, 'col': c, 'vr': vr, 'vc': vc, 'distance': 0}


def compute_dynamic_forces(organisms):
    total_dist = 0
    for i in range(5):
        for j in range(i + 1, 5):
            dr = abs(organisms[i]['row'] - organisms[j]['row'])
            dc = abs(organisms[i]['col'] - organisms[j]['col'])
            dr = min(dr, GRID - dr)
            dc = min(dc, GRID - dc)
            total_dist += math.sqrt(dr * dr + dc * dc)
    expansion_1000 = int(total_dist / (10 * 7.071))
    gen_1000 = int((ALPHA_NUM * (1000 + expansion_1000 * 30) * 5) / ALPHA_DEN)
    inh_1000 = int((ALPHA_NUM * (1000 + (1000 - expansion_1000) * 30) * 5) / ALPHA_DEN)
    return {'generate': gen_1000, 'inhibit': inh_1000, 'expansion': expansion_1000}


def _sign(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)


def move_wu_xing(f, all_org, is_yin, f_gen, f_inh):
    push_r, push_c = 0, 0
    parent = all_org[(f['i'] + 4) % 5]
    push_r += int((parent['row'] - f['row']) * f_gen / (GRID * 10))
    push_c += int((parent['col'] - f['col']) * f_gen / (GRID * 10))

    ci = -1
    for k in range(5):
        if INHIBITS[k] == f['i']:
            ci = k
            break
    if ci >= 0:
        push_r -= _sign(f['vr']) * int(f_inh / 10)
        push_c -= _sign(f['vc']) * int(f_inh / 10)

    climate_hash = 0
    for k in range(len(all_org)):
        if k != f['i']:
            climate_hash = (climate_hash ^ (_imul(all_org[k]['row'], 65537) + _imul(all_org[k]['col'], 257))) & 0xFFFFFFFF

    m1 = (climate_hash ^ _imul(f['row'], 31337) ^ _imul(f['i'], 7919)) & 0xFFFFFFFF
    m2 = (climate_hash ^ _imul(f['col'], 48271) ^ _imul(f['i'], 6151)) & 0xFFFFFFFF
    e0 = (m1 % 10000) / 10000
    e1 = (m2 % 10000) / 10000

    if is_yin:
        vr = f['vr'] - push_r + int((e0 - 0.5) * 20)
        vc = f['vc'] - push_c + int((e1 - 0.5) * 20)
    else:
        vr = f['vr'] + push_r + int((e0 - 0.5) * 20)
        vc = f['vc'] + push_c + int((e1 - 0.5) * 20)

    vr = max(-SPEED_LIMIT, min(SPEED_LIMIT, vr))
    vc = max(-SPEED_LIMIT, min(SPEED_LIMIT, vc))
    row = (f['row'] + vr) % GRID
    col = (f['col'] + vc) % GRID
    dr2 = abs(row - f['row'])
    dc2 = abs(col - f['col'])

    return {
        'i': f['i'], 'name': f['name'],
        'row': row, 'col': col, 'vr': vr, 'vc': vc,
        'distance': f['distance'] + math.sqrt(dr2 * dr2 + dc2 * dc2)
    }


def evolve_organisms(yang, yin):
    fy = compute_dynamic_forces(yang)
    fi = compute_dynamic_forces(yin)
    new_yang = [move_wu_xing(f, yang, False, fy['generate'], fy['inhibit']) for f in yang]
    new_yin = [move_wu_xing(f, yin, True, fi['generate'], fi['inhibit']) for f in yin]
    return new_yang, new_yin


def mod_inverse(a, m):
    a = ((a % m) + m) % m
    old_r, r = a, m
    old_s, s = 1, 0
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
    if old_r != 1:
        return None
    return ((old_s % m) + m) % m


# FIX-3 & FIX-6: Expanded position factor
def compute_position_factor(pos, yang, yin):
    eI = pos % 5
    eN = (eI + 1) % 5
    eP = (eI + 4) % 5
    cycle = pos // 5

    dR = abs(yang[eI]['row'] - yin[eI]['row'])
    dC = abs(yang[eI]['col'] - yin[eI]['col'])
    crossA = abs(yang[eN]['col'] - yin[eP]['row'])
    crossB = abs(yang[eP]['row'] - yin[eN]['col'])
    crossC = abs(yang[(eI + 2) % 5]['row'] - yin[(eI + 3) % 5]['col'])

    stateA = (_imul(dR, 65537) ^ _imul(crossA, 257) ^ _imul(cycle, 131071)) & 0xFFFFFFFF
    stateB = (_imul(dC, 48271) ^ _imul(crossB, 6151) ^ _imul(cycle, 7919)) & 0xFFFFFFFF
    stateC = (_imul(crossC, 31337) ^ _imul(dR + dC, 16411)) & 0xFFFFFFFF

    stateA = _hash_mix(stateA)
    stateB = _hash_mix(stateB)
    stateC = _hash_mix(stateC)

    mult = (stateA % 256) | 1
    if mult < 3:
        mult += 2
    offset = stateB % 256
    offset2 = stateC % 256
    inv = mod_inverse(mult, 256)

    return {'mult': mult, 'offset': offset, 'offset2': offset2, 'inv': inv}


# FIX-2: 32-bit feedback
def feedback_mix(feedback32, cipher_byte, mult):
    f = (feedback32 + cipher_byte + 1) & 0xFFFFFFFF
    f = _imul(f, 0x9E3779B1)
    f = (f ^ (mult * 0x100 + cipher_byte)) & 0xFFFFFFFF
    f = (f ^ ((f >> 17) & 0x7FFF)) & 0xFFFFFFFF
    return f


def feedback_byte(feedback32):
    return ((feedback32 ^ ((feedback32 >> 8) & 0xFFFFFF)
             ^ ((feedback32 >> 16) & 0xFFFF)
             ^ ((feedback32 >> 24) & 0xFF)) & 0xFF)


def random_seed():
    raw = os.urandom(32)
    return [int.from_bytes(raw[i*4:(i+1)*4], 'big') for i in range(8)]


def encrypt(message, warmup, seed256):
    msg_bytes = list(message.encode('utf-8'))
    yin_seed = derive_yin_seed(seed256)
    yang = [create_element(i, seed256) for i in range(5)]
    yin = [create_element(i, yin_seed) for i in range(5)]

    for _ in range(warmup):
        yang, yin = evolve_organisms(yang, yin)

    cipher = []
    fb32 = 0

    for i in range(len(msg_bytes)):
        f = compute_position_factor(i, yang, yin)
        fb = feedback_byte(fb32)

        s1 = (((msg_bytes[i] ^ fb) * f['mult']) + f['offset']) % 256
        s2 = SBOX[s1]
        s3 = SBOX[(s2 + f['mult'] + fb) % 256]
        s4 = s3 ^ ((f['offset2'] * 37 + i) % 256)

        cipher.append(s4)
        fb32 = feedback_mix(fb32, s4, f['mult'])

        if i % 5 == 4:
            yang, yin = evolve_organisms(yang, yin)

    return cipher


def decrypt(cipher_bytes, warmup, seed256):
    yin_seed = derive_yin_seed(seed256)
    yang = [create_element(i, seed256) for i in range(5)]
    yin = [create_element(i, yin_seed) for i in range(5)]

    for _ in range(warmup):
        yang, yin = evolve_organisms(yang, yin)

    plain = []
    fb32 = 0

    for i in range(len(cipher_bytes)):
        f = compute_position_factor(i, yang, yin)
        fb = feedback_byte(fb32)

        s3 = cipher_bytes[i] ^ ((f['offset2'] * 37 + i) % 256)
        s2 = ((SBOX_INV[s3] - f['mult'] - fb + 256 * 10) % 256)
        s1 = SBOX_INV[s2]
        p_xor = ((s1 - f['offset'] + 256 * 10) * f['inv']) % 256
        p = p_xor ^ fb

        plain.append(p)
        fb32 = feedback_mix(fb32, cipher_bytes[i], f['mult'])

        if i % 5 == 4:
            yang, yin = evolve_organisms(yang, yin)

    return bytes(plain).decode('utf-8')


if __name__ == "__main__":
    seed = random_seed()
    msg = "Test roundtrip 5PSC v3.0!"
    enc = encrypt(msg, 100, seed)
    dec = decrypt(enc, 100, seed)
    print(f"Roundtrip: {'PASS' if dec == msg else 'FAIL'}")
    print(f"Message:  {msg}")
    print(f"Cipher:   {bytes(enc).hex()}")
    print(f"Decoded:  {dec}")
