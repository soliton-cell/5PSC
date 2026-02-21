# 5PSC — 5-Phase Soliton Cipher

A symmetric stream cipher with a continuously evolving internal state. Five coupled state components interact through generation and inhibition cycles on a 10,000 × 10,000 toroidal grid. The keystream is derived from the differential positions of two mirrored state systems (Yang/Yin).

**The key exists only at the instant of use. It is not stored, not transmitted, not recoverable.**

## Why this matters

AI agents (OpenClaw, Moltbot, and others) are being banned by enterprises because they transmit sensitive data without adequate encryption. Current symmetric ciphers use static keys that, once compromised, expose everything.

5PSC eliminates this problem: the internal state evolves with every encrypted byte. Even if an attacker captures the state at time T, by time T+1 it has already changed. There is no single secret to steal.

## Technical specifications

| Property | Value |
|---|---|
| Type | Symmetric stream cipher |
| Seed | 256-bit (CSPRNG) |
| Internal state | 2 × 5 coupled components on 10,000² toroidal grid |
| Arithmetic | Integer-only (no floating point) |
| Non-linearity | Double S-box substitution + feedback chain |
| State evolution | Every 5 encrypted bytes |
| Force balance | Governed by α = 1/137 (integer fraction) |
| Cross-platform | Fully deterministic: same seed → same output, always |

## Architecture

```
Seed (256-bit)
    │
    ├──→ Yang system (5 state components)
    ├──→ Yin system (5 state components)
    │
    │  ┌─── Generation cycle (component N feeds N+1) ───┐
    │  │    Inhibition cycle (component N resists N+2)   │
    │  └─────────────── governed by α = 1/137 ──────────┘
    │
    ▼
Position differential (Yang vs Yin)
    │
    ├──→ Affine transformation (position-dependent)
    ├──→ Double S-box substitution
    ├──→ Feedback chain (each byte affects the next)
    │
    ▼
Keystream byte
```

**State evolution is continuous**: every 5 bytes, all 10 components move according to generation/inhibition forces, environmental noise from neighboring components, and toroidal boundary conditions. The state at byte 1000 depends on the complete history of bytes 0–999.

## Security properties

- **No static key**: internal state changes with every encryption operation
- **Path-dependent**: state at any point depends on entire encryption history
- **No key persistence**: nothing stored before or after encryption
- **Brute force**: 256-bit seed = 2²⁵⁶ possible states (~10⁷⁷)
- **Non-linear mixing**: double S-box + affine transform + feedback eliminates linear correlation

## Known limitations (v2.1)

- **No AEAD**: authentication/integrity verification not yet implemented (planned v3)
- **No explicit IV/nonce**: warmup parameter serves as nonce but should be formalized
- **S-box timing**: not constant-time; production implementation should use ARX or constant-time lookups
- **No formal cryptanalysis**: community code review completed, full cryptanalysis pending

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

// Decrypt
var plaintext = decrypt(result.hex, 100, seed256);

// Generate secure seed
var seed = generateSeed256();  // 8 × 32-bit from CSPRNG
```

## Use cases

- **AI agent communication**: protect data transmitted by autonomous agents (OpenClaw, custom LLM agents)
- **Ephemeral messaging**: messages where the key must not survive the session
- **IoT device encryption**: lightweight stream cipher for constrained environments
- **Zero-persistence systems**: compliance with data regulations requiring no key storage

## Version history

See [CHANGELOG.md](CHANGELOG.md)

## Community review

This cipher was publicly reviewed on CryptoHack Discord (February 20, 2026). Issues identified and fixed:

| Issue | Found by | Status |
|---|---|---|
| `Math.random()` in seed generation | /dev/nvme0n1 | Fixed v2.0 |
| Floating point arithmetic | 6... | Fixed v2.1 |
| Missing AEAD | /dev/nvme0n1 | Planned v3 |
| Missing IV/nonce | /dev/nvme0n1 | Planned v3 |
| S-box timing vulnerability | CryptoHack community | Planned v3 (ARX migration) |

## Built by

A farmer from Mount Etna (Sicily) and Claude (Anthropic).
Tested by the CryptoHack Discord community.

## License

Free for everyone. No restrictions.
