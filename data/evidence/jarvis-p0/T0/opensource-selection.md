# Open-source Selection

| Capability | Donor | Fixed source | Decision |
|---|---|---|---|
| Prompt data/instruction boundary and priority | `akshayaggarwal99/jarvis-ai-assistant` MIT | commit `bec50ef6e615707613c4fa22c8bd6afc3cc93152`, `src/prompts/prompts.ts` | Adopt the explicit speech/selection markers and priority order; translate names to Ultima terms. |
| Memory PoisonGuard | `AdelElo13/DockWright-MacOS-Agent` MIT | commit `d6d3f3f71fc83afc9df3f74f9376413084777b90`, `Core/Memory/MemoryPoisonGuard.swift` | Adopt the evaluation order and patterns, extend the multilingual list required by the work order, and expose a fail-closed Python writer. |
| Wake phrase fuzzy match and 50-second restart | DockWright MIT | same commit, `Core/Voice/WakeWordDetector.swift` | Adopt strict Levenshtein ratio `<0.35`, sliding windows, and the 50-second proactive restart concept; map restart to a sherpa stream rollover without restarting the microphone process. |
| Pluggable transcription | Jarvis MIT | commit `bec50ef6...`, `src/interfaces/transcription.ts` and `src/transcription/` | Adopt a small provider contract and routing registry; preserve the existing local sherpa implementation as first choice and make optional providers injectable rather than enabled by default. |
| AGPL engine | neuromcp | not read or copied | Excluded. No dependency, source, or runtime integration. |

No new package dependency is required. Python standard library plus already-present sherpa-onnx runtime is sufficient.
