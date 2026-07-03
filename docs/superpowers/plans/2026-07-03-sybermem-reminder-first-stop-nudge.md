# SyberMem Reminder-First Stop/Nudge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current stop-hook behavior into a reminder-first system: real `remind` mode, natural-language record intent detection, task-completion nudge support, and a stop-time fallback reminder.

**Architecture:** Extend the existing `.sybermem/hooks/record_change_on_stop.py` rather than replacing it. The hook will gain a true `remind` branch, a session-scoped record-intent marker, and clearer separation between "light reminder" and "auto trail" behavior. The project-level settings and docs will continue to present only `auto` and `remind`, but their semantics will finally match the user-facing description.

**Tech Stack:** Python 3.10+, Claude Code Stop hook, project-local `.sybermem/` state files

---

### Task 1: Fix `remind` mode so it actually reminds without auto-writing records

**Files:**
- Modify: `.sybermem/hooks/record_change_on_stop.py`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py`

- [ ] **Step 1: Replace the auto-only mode check with an explicit mode reader**

In `.sybermem/hooks/record_change_on_stop.py`, replace:

```python
def should_auto_record() -> bool:
    return os.environ.get("SYBERMEM_RECORD_MODE", "auto") == "auto"
```

with:

```python
def record_mode() -> str:
    mode = os.environ.get("SYBERMEM_RECORD_MODE", "auto").strip().lower()
    return mode if mode in {"auto", "remind"} else "auto"


def should_auto_record() -> bool:
    return record_mode() == "auto"
```

- [ ] **Step 2: Update `main()` to keep running in `remind` mode**

At the top of `main()`, replace:

```python
    if not should_auto_record():
        return 0
```

with:

```python
    mode = record_mode()
    if mode not in {"auto", "remind"}:
        return 0
```

This preserves the stop-hook pipeline for both `auto` and `remind` instead of exiting early.

- [ ] **Step 3: Gate auto-trail creation on mode**

In the section that writes the change record file:

```python
    record_path.write_text(...)
    update_index(...)
    save_state(...)
```

wrap those writes so they only happen in `auto` mode:

```python
    if mode == "auto":
        record_path.write_text(render_record(record_date, number, slug.replace("-", " "), files, author, followup_hint), encoding="utf-8")
        update_index(record_date, number, slug.replace("-", " "), slug)
        save_state({"last_fingerprint": fingerprint, "last_record": record_path.name})
    else:
        save_state({"last_fingerprint": fingerprint, "last_record": state.get("last_record", "")})
```

- [ ] **Step 4: Ensure `remind` mode still prints the nudge**

Where the hook already does:

```python
    if nudge_message:
        print(nudge_message)
```

leave that behavior unchanged so `remind` mode still produces reminders even when no record file is written.

- [ ] **Step 5: Mirror the updated hook into the init-project template**

Copy the updated file to:

```text
packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py
```

- [ ] **Step 6: Verify `remind` mode behavior with a temporary workspace**

Run a controlled verification using a temp git workspace or a copied temp project where `SYBERMEM_RECORD_MODE=remind` is set, make one changed file, then invoke the hook manually:

```bash
$env:SYBERMEM_RECORD_MODE = 'remind'; python .sybermem/hooks/record_change_on_stop.py
```

Expected:
- exit 0
- a reminder message may print
- **no new `.sybermem/changes/*.md` file is created**

Then repeat with `SYBERMEM_RECORD_MODE=auto` and verify a new change record **is** created.

- [ ] **Step 7: Commit**

```bash
git add .sybermem/hooks/record_change_on_stop.py packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py
git commit -m "fix: make remind mode emit reminders without auto-writing trails"
```

---

### Task 2: Add explicit record-intent detection and reminder state

**Files:**
- Modify: `.sybermem/hooks/record_change_on_stop.py`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py`
- Create: `.sybermem/.record-intent.example.json`

- [ ] **Step 1: Add a session-scoped intent state file path**

Near the existing state constants, add:

```python
RECORD_INTENT_PATH = SYBERMEM_DIR / ".record-intent.json"
```

- [ ] **Step 2: Add helpers to load/save/clear record intent**

Append these helpers near the other state helpers:

```python
def load_record_intent() -> dict:
    if not RECORD_INTENT_PATH.exists():
        return {}
    try:
        return json.loads(RECORD_INTENT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_record_intent(intent: dict) -> None:
    RECORD_INTENT_PATH.write_text(json.dumps(intent, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clear_record_intent() -> None:
    try:
        RECORD_INTENT_PATH.unlink()
    except FileNotFoundError:
        pass
```

- [ ] **Step 3: Add a simple phrase-matching detector**

Append:

```python
INTENT_PATTERNS = [
    re.compile(r"这轮.*提醒我.*记录"),
    re.compile(r"这次.*要记.*record", re.IGNORECASE),
    re.compile(r"做完.*沉淀一下"),
    re.compile(r"完成后.*提醒我.*/sybermem-record"),
    re.compile(r"这轮工作.*记录到.*sybermem", re.IGNORECASE),
]


def detect_record_intent_from_text(text: str) -> bool:
    return any(pattern.search(text) for pattern in INTENT_PATTERNS)
```

- [ ] **Step 4: Define the integration boundary for phase 1**

For this implementation phase, do **not** attempt to hook into arbitrary conversation text yet. Instead, make the stop-hook *consume* `RECORD_INTENT_PATH` if present. The producing side (who writes this file when a user says “this round should be recorded”) can be integrated later by a dedicated helper/skill.

At the top of `main()`, after loading nudge state, add:

```python
    record_intent = load_record_intent()
```

And use it to strengthen reminder output:

```python
    intent_active = bool(record_intent.get("record_intent"))
```

- [ ] **Step 5: Upgrade reminder wording when explicit intent is active**

Where the hook prints `nudge_message`, replace it with:

```python
    if intent_active:
        print("You marked this work as worth recording earlier. If this round is complete, run /sybermem-record now.")
    elif nudge_message:
        print(nudge_message)
```

At the end of `main()`, after the stop path completes, clear the intent only if a reminder was actually shown:

```python
    if intent_active:
        clear_record_intent()
```

- [ ] **Step 6: Add the example file documenting the shape**

Create `.sybermem/.record-intent.example.json`:

```json
{
  "record_intent": true,
  "source": "user-declared",
  "created_at": "2026-07-03T00:00:00+08:00"
}
```

- [ ] **Step 7: Mirror the updated hook into the init-project template**

Copy the updated file to the init-project template path again.

- [ ] **Step 8: Verify explicit-intent reminder behavior**

Create a temporary `.record-intent.json`, then run the hook once with changed files present.

Expected:
- the output reminder explicitly references the earlier record intent
- the temporary `.record-intent.json` is cleared after the reminder

- [ ] **Step 9: Commit**

```bash
git add .sybermem/hooks/record_change_on_stop.py packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py .sybermem/.record-intent.example.json
git commit -m "feat: add explicit record-intent state for reminder-first flow"
```

---

### Task 3: Improve task-completion nudge semantics in docs and user-facing config

**Files:**
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `packages/claude-skills/using-sybermem/SKILL.md`
- Modify: `skills/using-sybermem/SKILL.md`

- [ ] **Step 1: Update project instructions to describe the real semantics**

In `CLAUDE.md` and `AGENTS.md`, replace any wording that implies `remind` is already functioning if it is currently inaccurate. Update the “After work (auto/remind mode)” section so it explicitly says:

- `auto` = lightweight change trail + reminders
- `remind` = reminders only, no automatic change trail

- [ ] **Step 2: Update README Team/project workflow docs**

Add a short note to both README files clarifying the reminder-first semantics:

Chinese:
```markdown
- **提醒模式**：`remind` 模式不会自动写 `change` trail，只会在高价值变化或显式记录意图存在时提醒你手动 `/sybermem-record`
```

English:
```markdown
- **Reminder mode**: `remind` does not auto-write a `change` trail. It only reminds you to run `/sybermem-record` when high-signal work or an explicit record intent is present
```

- [ ] **Step 3: Update `/using-sybermem` guidance**

In both `packages/claude-skills/using-sybermem/SKILL.md` and `skills/using-sybermem/SKILL.md`, make the routing section mention:
- whether current mode is `auto` or `remind`
- what the stop hook will actually do in that mode

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md AGENTS.md README.md README.en.md packages/claude-skills/using-sybermem/SKILL.md skills/using-sybermem/SKILL.md
git commit -m "docs: clarify reminder-first semantics for stop hook modes"
```

---

### Task 4: End-to-end dogfood and acceptance report

**Files:**
- No repo-file changes required by default

- [ ] **Step 1: Manual dogfood with `auto` mode**

Use a temp controlled change set and run the stop hook once.

Expected:
- a new change trail is created
- a reminder may also appear if the classifier detects it

- [ ] **Step 2: Manual dogfood with `remind` mode**

Set:

```bash
$env:SYBERMEM_RECORD_MODE = 'remind'
```

Run the stop hook with changed files present.

Expected:
- no new change record file
- reminder still appears when the work is high-signal or explicit intent is present

- [ ] **Step 3: Manual dogfood with explicit record intent**

Create a temporary `.record-intent.json`, then run the hook.

Expected:
- reminder explicitly references the earlier intent
- the state file is cleared afterward

- [ ] **Step 4: Record findings**

Summarize clearly:
- what works now
- what still depends on future integration (e.g. who writes `.record-intent.json` in real conversations)

- [ ] **Step 5: No commit needed** (verification only)
