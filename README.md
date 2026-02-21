# 5PSC — 5-Phase Soliton Cipher

A stream cipher engine where five elements (Wood, Fire, Earth, Metal, Water) form two living organisms — Yang and Yin — that evolve continuously on a toroidal grid. The keystream emerges from the interaction between these organisms. The key is not stored — it exists only in the instant it's used.

## How it works

- **256-bit seed** generates two organisms (Yang + Yin), each with 5 elements
- Elements move on a 10,000 × 10,000 toroidal grid following Wu Xing (五行) generation and inhibition cycles
- The fine-structure constant α = 1/137 governs the balance between generation and inhibition forces
- Organisms evolve during encryption — every 5 bytes, the state changes
- Each byte is encrypted through double S-box substitution with position-dependent affine transformation
- **Deterministic**: same seed + same warmup = same output, always, on any platform
- **Integer-only arithmetic**: no floating point, fully cross-platform deterministic

## Quick start

```bash
node 5PSC_v2_1.js
```

Runs self-test: 4 message tests + seed uniqueness + determinism verification.

## API

```javascript
// Encrypt
var result = encrypt("your message", 100, seed256);
// result.hex = ciphertext in hex
// result.seed = seed used
// result.warmup = warmup rounds

// Decrypt
var plaintext = decrypt(result.hex, 100, seed256);

// Generate secure seed
var seed = generateSeed256();  // 8 × 32-bit from CSPRNG
```

## Version history

See [CHANGELOG.md](CHANGELOG.md)

## Acknowledgments

Built by a 76-year-old farmer from Mount Etna (Sicily) and Claude (Anthropic).
Improved by the CryptoHack Discord community — in particular /dev/nvme0n1 and 6...

## License

Free for everyone. No restrictions.
