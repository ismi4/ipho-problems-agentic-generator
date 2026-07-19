# Injected faults — five-problem mechanics bench

Clean official solutions were downloaded from <https://ipho.olimpicos.net/>.
Each solution below has a matching `*_FAULTY.pdf` under `pdfs/faulty/`.

| Problem | Clean | Faulty | Faults |
|---|---|---|---|
| 2020 Anisotropic Friction | `IPhO_2020_S2.pdf` | `IPhO_2020_S2_FAULTY.pdf` | F2020-1..3 |
| 2021 Planetary Physics | `IPhO_2021_S1.pdf` | `IPhO_2021_S1_FAULTY.pdf` | ERR-6..10 (see `INJECTED_ERRORS.md`) |
| 2023 Water and Objects | `IPhO_2023_S3.pdf` | `IPhO_2023_S3_FAULTY.pdf` | ERR-1..5 (see `INJECTED_ERRORS.md`) |
| 2024 Black Widow Pulsar | `IPhO_2024_S3.pdf` | `IPhO_2024_S3_FAULTY.pdf` | F2024-1..2 |
| 2025 Cox's Timepiece | `IPhO_2025_S2.pdf` | `IPhO_2025_S2_FAULTY.pdf` | F2025-1..2 |

### New faults (2020 / 2024 / 2025)

**F2020-1** · A1 · wrong extremum — power-max angle `α=0` → `α=π/2`  
**F2020-2** · A3 · dropped factor — `vx=0.125` → `0.250` m/s  
**F2020-3** · C2 · wrong parameter — `v0max=2.2` → `3.1` m/s  

**F2024-1** · A-3 · wrong root — Lagrange `x̄0≈0.36` → `0.25`  
**F2024-2** · A-6 · wrong numeric — `T=9×10³ K` → `9×10² K`  

**F2025-1** · C.1 · dropped factor — `ξ⋆=2` → `xi*=1`  
**F2025-2** · C.3 · dropped factor — regime boundaries using `2` → `1`

Regenerate with:

```bash
cd verifier_experiments
PYTHONPATH=inject_errors python inject_errors/inject_all_five.py
# plus the ASCII 2025 patch in the same module / ad-hoc script used in the run
```
