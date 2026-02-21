# 5PSC v3.0 — 5-Phase Soliton Cipher

A stream cipher based on Wu Xing (Five Phases) dynamical systems operating on a toroidal grid.

## What This Is

An experimental cipher that uses dual evolving dynamical systems (Yang and Yin) as a key-dependent state machine. The internal state continuously evolves through Wu Xing generation/inhibition cycles, producing position-dependent encryption parameters for each byte.

**This is a research/hobbyist cipher.** It has not undergone formal cryptanalysis. Do not use for protecting real data.

## What's New in v3.0

Version 3.0 addresses all critical issues identified during independent peer review:

| Fix | Issue | Solution |
|-----|-------|----------|
| FIX-1 | Yang and Yin started from identical state → zero initial divergence | Yin system initialized from domain-separated seed derivation |
| FIX-2 | 8-bit feedback accumulator → cycles in ≤256 steps | Extended to 32-bit with multiplicative mixing (golden ratio constant) |
| FIX-3 | Small affine parameter space (~32K) → searchable with known plaintext | Parameters derived from wider organism state via hash mixing |
| FIX-4 | History array consumed memory with no cryptographic purpose | Removed |
| FIX-5 | `Math.random()` present in HTML demo seed generation | `crypto.getRandomValues` / `crypto.randomBytes` exclusively |
| FIX-6 | Biased mult/offset distribution in position factor | Hash-mixed derivation from cross-element state |

## Architecture

```
256-bit seed ──┬──────────────────→ Yang system (5 organisms on 10K×10K torus)
               └── deriveYinSeed() → Yin system  (5 organisms, different positions)
                        │
                    warmup(N) ← organisms evolve N steps before encryption
                        │
              ┌─────────┴─────────┐
              │  For each byte:   │
              │  1. Position factor from Yang/Yin differential │
              │  2. Affine transform (mult, offset)           │
              │  3. S-box substitution ×2                     │
              │  4. XOR with position-dependent mask           │
              │  5. 32-bit feedback update                     │
              │  6. Every 5 bytes: organisms evolve            │
              └───────────────────┘
```

## Usage

### JavaScript (Node.js)
```javascript
var psc = require('./5PSC_v3.js');

var seed = psc.generateSeed256();  // 256-bit CSPRNG seed
var encrypted = psc.encrypt("Hello World", 100, seed);
var decrypted = psc.decrypt(encrypted.hex, 100, seed);

console.log(encrypted.hex);   // ciphertext as hex
console.log(decrypted);       // "Hello World"
```

### JavaScript (Browser)
```html
<script src="5PSC_v3.js"></script>
<script>
  var seed = PSC5.generateSeed256();
  var enc = PSC5.encrypt("Hello World", 100, seed);
  var dec = PSC5.decrypt(enc.hex, 100, seed);
</script>
```

### Python
```python
from psc5_v3 import encrypt, decrypt, random_seed

seed = random_seed()
cipher = encrypt("Hello World", 100, seed)
plain = decrypt(cipher, 100, seed)
```

## Known Limitations

These are documented since v1 and remain in v3:

- **No AEAD** — no integrity protection. Bit-flipping attacks are possible.
- **No nonce/IV** — same seed + same message = same ciphertext. Classic stream cipher weakness.
- **S-box not formally analyzed** — generated from π via Fisher-Yates. No differential/linear uniformity proof.
- **Not constant-time** — S-box lookups and branches are timing-observable. Side-channel exploitable.
- **No formal cryptanalysis** — security level is genuinely unknown until a professional cryptanalyst attempts to break it.

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | Jan 2026 | Initial implementation with floating-point arithmetic |
| v2.0 | Feb 2026 | Integer arithmetic, CSPRNG seed, double S-box. Based on CryptoHack/Reddit feedback |
| v2.1 | Feb 2026 | Bug fixes from /dev/nvme0n1 review |
| v3.0 | Feb 2026 | Critical fixes from independent peer review (6 issues addressed) |

## Academic Paper

See [ePrint IACR 2026/107945](https://eprint.iacr.org/2026/107945) (covers v2 architecture; v3 changelog pending update).

## Philosophy

The cipher's design draws from the Wu Xing (五行) cycle of Chinese natural philosophy and the fine-structure constant α ≈ 1/137 as a coupling parameter. These are design choices, not security claims — the cryptographic strength comes from the mathematical properties of the system, not from the physical constants.

## License

MIT

## Authors

Quintilio Menicocci & Claude (Anthropic)
