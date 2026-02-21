# Changelog

## v2.1 — February 21, 2026
**Integer-Only Edition** — all floating point removed for cross-platform determinism.

### Fixed
- `Math.sqrt()` → Manhattan distance (integer)
- Float division → integer arithmetic scaled by 1000
- `ALPHA` float → integer fraction `1/137`

### Credits
- Floating point issue identified by **6...** (CryptoHack Discord)

---

## v2.0 — February 20, 2026
**Public release** on CryptoHack Discord.

### Fixed (from community feedback)
- `Math.random()` → `crypto.getRandomValues()` / `crypto.randomBytes()` (CSPRNG)

### Previous fixes over v1
- Seed expanded from 32-bit to 256-bit
- Double S-box + feedback chain (breaks linearity)
- Organisms evolve during encryption, not just warmup

### Credits
- `Math.random()` vulnerability identified by **/dev/nvme0n1** (CryptoHack Discord)
- AEAD absence noted by **/dev/nvme0n1**
- IV/nonce absence noted by **/dev/nvme0n1**
- ARX suggestion (over S-box) by **/dev/nvme0n1**
- S-box timing attack concern by **You ⚡+W** (CryptoHack Discord)

---

## v1.0 — February 19, 2026
Initial version. Prior art certified via PEC (Italian certified email).

### Known issues (fixed in v2)
- 32-bit seed (brute-forceable)
- Single S-box (linear)
- Static organisms during encryption
