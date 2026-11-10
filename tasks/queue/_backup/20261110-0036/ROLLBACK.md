# Queue status migration rollback

1. Restore `project-index.pre-migration-*.md` to `tasks/queue/index.md`.
2. Restore `global-queue-index.pre-migration-*.md` to `H:/UltimaAI/_shared/queue/global-queue-index.md`.
3. Delete `tasks/queue/queue-status.json`.

Do not merge state from the generated views back into JSON.
