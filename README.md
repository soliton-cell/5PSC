# 5PSC — 5-Phase Soliton Cipher

A stream cipher based on Wu Xing (五行) dynamic system — five interacting organisms whose perpetual-cycle dynamics generate cryptographic keystream.

**Author:** Soliton Cipher (Mount Etna, Sicily)  
**Prior art:** Certified email (PEC), February 19, 2026  
**License:** Free for everyone. No restrictions.  
**Current version:** v4.0

---

## What is this?

5PSC is an experimental cipher that uses a biological-dynamic model instead of algebraic constructions. Ten organisms (5 Yang, 5 Yin) move on a toroidal grid following generation/inhibition cycles derived from Wu Xing (Five Elements) theory. Their positions, velocities, and interactions produce position-dependent encryption parameters for each byte.

This is **not** a replacement for AES. It is an exploration of whether perpetual-cycle dynamics from a different mathematical tradition can generate useful cryptographic properties.

## Why?

Most ciphers derive security from algebraic hardness (factoring, discrete log, lattice problems). 5PSC asks a different question: **can a deterministic dynamic system with sensitive dependence on initial conditions produce cryptographically useful output?**

The answer so far: v2.1 proved it couldn't — yet. Community cryptanalysis on CryptoHack Discord exposed fundamental weaknesses. v4 addresses those weaknesses with proven primitives (AES S-box, SHA-256) while preserving the dynamic core.

The honest answer to "what advantage does this have over existing approaches" is: **none proven**. The advantage is the question itself. If dynamic-system ciphers can work, they open a design space that algebraic ciphers don't explore.

## v4.0 Architecture

### What changed from v2.1 (and why)

| Component | v2.1 (broken) | v4.0 | Attack it fixes |
|-----------|---------------|------|-----------------|
| Position factors | 3 organism pairs mod 256 → 8-bit | SHA-256 of all 40 state variables | GMO_Goat: brute-force with 3-5 known-plaintext pairs |
| S-box | Fisher-Yates/π permutation | AES S-box (Rijndael) | GMO_Goat: 65% linearity |
| Feedback | 32-bit, invertible | 64-bit, non-invertible mixing | GMO_Goat: hash invertibility |
| Nonce | Warmup rounds as nonce | 128-bit random, SHA-256 mixed | Formal nonce separation |
| Interface | String in/out | Bytes in/out | No encoding assumptions |

### Encryption pipeline (per byte)

```
plaintext[i] → XOR feedback → affine(mult, offset) → SBOX → SBOX(+extra+fb) → XOR offset2 → ciphertext[i]
```

### Dynamic core

- 10 organisms on 10000×10000 toroidal grid
- Generation cycle: Wood→Fire→Earth→Metal→Water→Wood
- Inhibition cycle: Wood→Earth, Fire→Metal, Earth→Water, Metal→Wood, Water→Fire
- Force scaling: α = 1/137 (fine-structure constant)
- Organisms evolve every 5 bytes

### Key derivation

```
seed256 (256-bit) + nonce (128-bit) → SHA-256 → session_key
session_key → domain separation → yin_key
```

## Files

- `5PSC_v4.py` — Complete implementation with self-test
- `README.md` — This file
- `CHANGELOG.md` — Version history and credits

## Usage

```bash
python3 5PSC_v4.py
```

Runs self-test: encrypt/decrypt roundtrip, nonce uniqueness, determinism, and GMO_Goat attack resistance simulation.

## Known limitations

- **Not peer-reviewed.** This is an experimental cipher posted for public analysis.
- **Performance:** ~47 KB/s in Python. The dynamic system is computationally expensive.
- **No formal security proof.** The security relies on the difficulty of recovering 10-organism state (~530 bits) from ciphertext, which has not been formally analyzed.
- **Hybrid design.** v4 relies on AES S-box and SHA-256 for proven non-linearity. The dynamic core alone is not sufficient.

## How to break it

If you want to attack v4, the interesting targets are:

1. **State recovery:** Can you recover organism positions from ciphertext + known plaintext, even with SHA-256 position factors?
2. **Dynamic system analysis:** Do the Wu Xing dynamics have attractors or cycles that reduce the effective state space?
3. **Feedback weakness:** Is the 64-bit feedback accumulator distinguishable from random after enough ciphertext?

Pull requests with analysis welcome. If you break it, you get credited in CHANGELOG and fed on Mount Etna. 🌋

## Credits & Community

This cipher exists because of public cryptanalysis on [CryptoHack Discord](https://discord.gg/cryptohack). Built with Claude (Anthropic) as a collaborative tool — the human decides what to build, the AI helps implement.

See [CHANGELOG.md](CHANGELOG.md) for full credits.

---

*Q-Principle Research · Mount Etna, Sicily · 2026*
