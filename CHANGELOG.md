# Changelog

All notable changes to 5PSC are documented here.

## [4.0] — 2026-02-25

Complete redesign of cryptographic layer in response to GMO_Goat's cryptanalysis.

### Changed
- **Position factors:** Now derived from SHA-256 hash of all 40 organism state variables + byte position + feedback state. Previously used 3 organism pairs mod 256 (8-bit brute-forceable).
- **S-box:** Replaced Fisher-Yates/π permutation (65% linearity) with standard AES S-box (max linear probability 2^-3, max differential probability 2^-6).
- **Feedback accumulator:** 64-bit non-invertible mixing replaces 32-bit invertible accumulator. Uses golden ratio constant (0x9E3779B97F4A7C15) and SplitMix64-style mixing.
- **Nonce:** Formal 128-bit random nonce, mixed into seed via SHA-256. Replaces warmup-rounds-as-nonce approach.
- **Interface:** Bytes-in/bytes-out. No string encoding assumptions.

### Added
- `derive_session_key()` — seed + nonce → SHA-256 → session key
- `_state_to_bytes()` — serializes all 10 organisms for hashing
- GMO_Goat attack resistance test in self-test suite
- Double S-box application with extra mixing byte

### Credits
- **GMO_Goat** (CryptoHack Discord) — Position factor brute force, S-box linearity analysis, hash invertibility, known-plaintext attack demonstration. Clean, precise, professional cryptanalysis. v4 exists because of this work.
- **__cdeclan** (CryptoHack Discord) — Suggested aligning with FIPS AES standards. AES S-box adopted in v4.
- **nikost** (CryptoHack Discord) — Identified hallucinated eprint link in README. Fixed.

---

## [2.1] — 2026-02-19

Public release on GitHub. Posted to CryptoHack Discord for analysis.

### Known vulnerabilities (found by community)
- Position factors brute-forceable: 8-bit mult/offset recoverable with 3-5 known-plaintext pairs
- π-derived S-box has 65% linearity (should be ≤50%)
- 32-bit feedback accumulator is invertible
- No formal nonce — warmup rounds used as de facto nonce

### Credits
- **/dev/nvme0n1** — Found Math.random() in seed generation (v2.0)
- **6...** — Found floating-point arithmetic issues

---

## [2.0] — 2026-02-18

First implementation. Integer arithmetic, Wu Xing dynamics, π-derived S-box.

---

## [1.0] — 2026-02-17

Concept. Five-element dynamic system generating keystream.

---

*Every break makes the next version real.*
