# OpenCode V2 migration: current scope and acceptance

Target host: OpenCode **2.0.15**. This is not an all-V2 compatibility claim. The server and companion TUI are implemented in the repository; deployment and live-model acceptance are separate steps.

## Current behavior

- The V2 server entrypoint uses `{ id: "sybermem", setup }`; the V1 implementation remains a separate compatibility export. `prompt` admits identity only; `context` reads canonical persisted user messages from `session.context`, not failed or queued prompt text. Session snapshots are serialized. Each eligible message is captured, usage-journaled and summarized once, while each independent outgoing request still receives context. Repeated events are idempotent. Compaction supplements system parts without replacing the transcript or summary.
- Startup, recall, habits, norms and pending-candidate nudges are injected as system text parts. Usage records describe attempted outgoing-request injection, **not** proof of provider acceptance. The local pending-candidate nudge is present.
- `execute.after` observes completed edits/todos. Shell test/build evidence requires a completed tool call with explicit numeric exit code `0`; missing, nonzero or error status is not success evidence. The actual 2.0.15 shell event fields still require live confirmation.
- The server exposes bounded, read-only feedback status through RPC and emits notices; the companion TUI uses RPC/events to show toasts for the selected session. Status includes the setup epoch even when no summary exists. Each setup generates a new epoch. The TUI recovers missed status on startup, route change and timer, and rejects late snapshots, stale epochs, foreign sessions/locations and duplicate or older notices. Unload removes subscriptions/registrations and clears state. Server-side epoch wiring is implemented and has directed tests, **not yet final joint acceptance**.
- There is no sidebar and no deterministic marker in assistant reply text. The V1 remote-version background refresh has **not** been restored in V2; local nudges do not imply remote refresh.

## Distribution target contract

The installer detects OpenCode's installed major via `opencode --version` or accepts explicit `--opencode-major 1|2` (also `SYBERMEM_OPENCODE_MAJOR`). Unknown/unparseable version without override **skips OpenCode installation** and reports loader/function unverified. V1 uses the independent `sybermem-v1.ts` source and installs `~/.config/opencode/plugins/sybermem.ts`; V2 copies the complete `dist-v2` package (`package.json`, `server.js`, `tui.js`) to `~/.config/opencode/sybermem-v2/` as **one plugin directory target** in the selected `opencode.jsonc` or `opencode.json` plugin array. Migration removes known old entries/files to avoid dual loading; unmanaged or modified targets are refused rather than overwritten. Managed file hashes and previous config are backed up in memory and restored on install failure (an incomplete rollback is reported). Do not infer live host loading from file hashes alone. Complete distribution and upgrade/removal regression checks before calling this delivered.

## Evidence and remaining acceptance

Historical reports of **130/367**, **9/58**, an `active` plugin state and `features` flags are prior evidence with their own scopes; they are not this revision's complete test result. The current directed tests/fixtures are narrower and should be reported separately, without converting either set into a same-revision full acceptance claim. A loader listing establishes that the host loaded an entrypoint, not the deployed bundle's identity, live TUI rendering or provider dispatch.

- Verify the completed directory installer and upgrade/removal behavior, including one server + TUI package entry and no stale competing file entry.
- On real OpenCode 2.0.15, verify persisted-message admission, per-message once-only capture/usage/summary, per-request injection, same-event deduplication and compaction supplementation; confirm shell completion/exit field shape and numeric-zero gating.
- Exercise actual RPC/TUI toasts and route/timer recovery, empty-summary epoch status, late snapshot/old epoch rejection, setup replacement and unload cleanup; directed server-epoch tests do not replace this joint acceptance.
- Separately verify runtime plugin-list identity and real-model TUI/provider behavior. No global deployment was changed in this documentation pass, and no real-model TUI acceptance has been performed here. Do not label the migration fully accepted or broadly compatible with every V2 release.
