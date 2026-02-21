# Changelog

## v3.0.0 (2026-02-22)

Based on independent peer review of v2.1 code and documentation.

### Critical Fixes
- **FIX-1**: Yin system now initialized from domain-separated seed derivation. Previously both Yang and Yin started from identical state with zero initial divergence. The `deriveYinSeed()` function XORs the original seed with a domain separator ("YIN!") and applies three rounds of hash mixing with cross-word dependencies.
- **FIX-2**: Feedback accumulator extended from 8-bit (mod 256) to 32-bit with multiplicative mixing using golden ratio constant (0x9E3779B1). Previous 8-bit accumulator cycled in ≤256 steps.
- **FIX-3**: Position factor parameters now derived from wider organism state. Previous implementation used raw mod-256 of position differences, yielding ~32K possible affine transforms. Now uses hash-mixed cross-element state with three independent derivation paths.

### Improvements  
- **FIX-4**: Removed history array from organisms (60-position buffer that served no cryptographic purpose).
- **FIX-5**: HTML demo seed generation now uses `crypto.getRandomValues` exclusively. `Math.random()` was present in v2 HTML demo.
- **FIX-6**: Improved mult/offset distribution via `hashMix()` applied to gathered state, producing near-uniform distribution across 8-bit range.

### New Features
- `offset2` parameter in position factor for XOR step independence
- `feedbackMix()` and `feedbackByte()` exported for testing
- `deriveYinSeed()` exported for verification

## v2.1.0 (2026-02-19)

- Bug fixes from /dev/nvme0n1 review on CryptoHack
- Integer-only arithmetic (no floating-point in crypto path)

## v2.0.0 (2026-02-18)

- CSPRNG seed generation (crypto.getRandomValues)
- Double S-box substitution
- Continuous organism evolution during encryption

## v1.0.0 (2026-01-23)

- Initial implementation
- Floating-point arithmetic
- Single S-box
