# T0 Baseline Findings

- Work order: `wo-ultimaagent-20261103-0023`
- Executor: Codex, inline execution in `H:/UltimaAI/UltimaAgent`
- Git branch: `codex/voice-fsmn-new-path`
- T0 product changes: none

## Repository state

The checkout was already heavily dirty. Existing modified/untracked work was preserved. In particular, `src/brain/agent_server.py` had four unrelated 14B-to-8B comment edits and the whole `src/brain/memory/` tree was pre-existing but untracked. This order will stage exact paths/hunks only and will not absorb that memory tree.

The current checkout is a normal repository rather than a linked worktree. A new worktree was not created because the task-relevant source/research baseline includes untracked files that would be absent from a HEAD-based worktree, and the user explicitly supplied this checkout as the execution directory. The cost of this ruling is that staged-path and staged-diff review is mandatory before commit.

## Frozen dependencies

- 0016 tag `ultimaagent-reply-constraint-routing-20261101` resolves to `a3fca7c3751e8a2f3227c29b6eb3c09455ae0490`.
- 0017 tag `ultimaagent-reply-constraint-structured-20261101` resolves to `5ef3ec30a8635b3232d78a1edcabdc7362d9ae07`.
- KWS authority was read before any voice implementation change.

## Donor source correction

The work-order statement that both DockWright files already existed in `docs/research/sources/` was false in the starting checkout. The official repository was resolved at fixed main commit `d6d3f3f71fc83afc9df3f74f9376413084777b90`, and the two source files plus MIT license were copied byte-for-byte into `docs/research/sources/dockwright/`. Local hashes match the downloaded donor bytes.

## Baseline RED/GREEN

- RED command: `tools/venv-openjarvis/Scripts/python.exe -m pytest src -q --disable-warnings ...`
- RED result: exit `1`; `931 passed, 1 failed, 120 subtests passed`.
- Failure: `src/brain/tests/test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains` raised `FileNotFoundError` for the unqualified `ollama` executable.
- Root cause: `C:/Users/Administrator/AppData/Local/Programs/Ollama/ollama.exe` exists and its process is running, but that directory was missing from the tool process `PATH`.
- Targeted GREEN: adding that directory only to the child test process `PATH` produced `1 passed`, exit `0`.
- Full GREEN: the same process-local `PATH` addition produced `932 passed, 0 failed, 120 subtests passed`, exit `0`, in 155.85 seconds.
- No system environment, service, model, inference parameter, or production default was changed.

## KWS invariants and observed drift

Frozen authority states `keywords_threshold=0.08`, `keywords_score=2.0`, `num_trailing_blanks=8`, 16 kHz model input, and the saved 8-positive/8-negative corpus comparison. This work order will not edit these values.

The tracked `src/brain/voice/kws_listener.py` currently contains historical constants `keywords_score=1.0` and `num_trailing_blanks=0`, which differ from the authority document. Correcting that pre-existing drift would change production defaults and is therefore outside this order. T3 will prove that the new wrapper code does not modify any existing constant and will evaluate the authoritative saved corpus separately.
