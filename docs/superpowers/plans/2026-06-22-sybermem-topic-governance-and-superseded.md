# SyberMem Topic Governance & Superseded Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add topic-status markers (`active`/`low`/`deprecated → new-topic`) and structured `superseded_by` handling so search can warn on stale topics, records can point to their replacements, and `/sybermem-link superseded-by` can archive old conclusions automatically.

**Architecture:** This is a pure-markdown behavior change: extend Topic Index syntax, add `superseded_by` to decision/requirement templates, extend `/sybermem-link` with a new `superseded-by` relation that updates both record frontmatter and INDEX.md archive placement, and teach `/sybermem-search` to surface topic-status and supersession hints. No new scripts or dependencies.

**Tech Stack:** Markdown (skills, templates, INDEX, README)

---

### Task 1: Document topic-governance syntax in INDEX files and README

**Files:**
- Modify: `.sybermem/INDEX.md`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md`
- Modify: `README.md`

- [ ] **Step 1: Add Topic Index suffix guidance to the live INDEX**

In `.sybermem/INDEX.md`, locate this block:

```markdown
## Topic Index

<!-- Auto-maintained: maps topic tags to record IDs for fast lookup -->
```

Replace it with:

```markdown
## Topic Index

<!-- Auto-maintained: maps topic tags to record IDs for fast lookup -->
<!-- Optional suffix: [active] [low] [deprecated → <new-topic>] -->
```

- [ ] **Step 2: Add the same Topic Index suffix guidance to the init-project template INDEX**

In `packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md`, locate the same two-line block and make the same replacement.

- [ ] **Step 3: Add README documentation for topic markers and superseded_by**

In `README.md`, after the existing `## 记录关系与检索` section, add:

```markdown
## Topic 治理与替代关系

Topic Index 现在支持可选状态后缀：

- `[active]` — 当前活跃 topic（默认；无标记视为 active）
- `[low]` — 低活跃度 topic，仍可查询
- `[deprecated → <new-topic>]` — 已被新 topic 替代，search 会提示使用新 topic

记录 frontmatter 还支持可选的 `superseded_by: <record-id>` 字段，用于表示旧记录已被新记录替代。`/sybermem-link old superseded-by new` 会：

1. 在旧记录 frontmatter 写入 `superseded_by: <new-id>`
2. 将旧记录的 Key Conclusion 从 `## Key Conclusions` 移到 `## Archived Conclusions`
3. 在归档行尾追加 `[superseded by <new-id>]`
```

- [ ] **Step 4: Verify**

Run: `python -c "
for f in ['.sybermem/INDEX.md','packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md']:
    t = open(f, encoding='utf-8').read()
    assert 'Optional suffix: [active] [low] [deprecated → <new-topic>]' in t
    print(f, 'OK')
rt = open('README.md', encoding='utf-8').read()
assert 'Topic 治理与替代关系' in rt
assert 'superseded_by: <record-id>' in rt
print('README OK')
"`
Expected: both INDEX files OK, then `README OK`.

- [ ] **Step 5: Commit**

```bash
git add .sybermem/INDEX.md packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md README.md
git commit -m "docs: add topic governance markers and superseded handling docs"
```

---

### Task 2: Add superseded_by to decision and requirement templates

**Files:**
- Modify: `packages/claude-skills/sybermem-record/templates/decision.md`
- Modify: `packages/claude-skills/sybermem-record/templates/requirement.md`

- [ ] **Step 1: Update decision.md template comments**

The current decision template frontmatter comment block is:

```markdown
# Optional relations (forward-only, values are existing record IDs):
# implements: [requirement-NNN]   # this decision implements a requirement
# fixes: [bug-NNN]                 # this decision addresses a bug
# related: [type-NNN]              # weak association
```

Replace it with:

```markdown
# Optional relations (forward-only, values are existing record IDs):
# implements: [requirement-NNN]   # this decision implements a requirement
# fixes: [bug-NNN]                 # this decision addresses a bug
# related: [type-NNN]              # weak association
# superseded_by: decision-NNN      # this decision has been replaced by a newer one
```

- [ ] **Step 2: Update requirement.md template comments**

The current requirement template comment block is:

```markdown
# Optional relations (forward-only, values are existing record IDs):
# related: [type-NNN]              # weak association with another record
```

Replace it with:

```markdown
# Optional relations (forward-only, values are existing record IDs):
# related: [type-NNN]              # weak association with another record
# superseded_by: requirement-NNN   # this requirement has been replaced by a newer one
```

- [ ] **Step 3: Verify**

Run: `python -c "
for f, marker in [
    ('packages/claude-skills/sybermem-record/templates/decision.md', 'superseded_by: decision-NNN'),
    ('packages/claude-skills/sybermem-record/templates/requirement.md', 'superseded_by: requirement-NNN'),
]:
    t = open(f, encoding='utf-8').read()
    assert marker in t
    print(f, 'OK')
"`
Expected: both files OK.

- [ ] **Step 4: Commit**

```bash
git add packages/claude-skills/sybermem-record/templates/decision.md packages/claude-skills/sybermem-record/templates/requirement.md
git commit -m "docs: add superseded_by to decision and requirement templates"
```

---

### Task 3: Extend /sybermem-link with superseded-by relation

**Files:**
- Modify: `packages/claude-skills/sybermem-link/SKILL.md`

- [ ] **Step 1: Expand relation type to include superseded-by**

Make these exact changes in `packages/claude-skills/sybermem-link/SKILL.md`:

1. In the HARD-GATE section, change:

```markdown
Do NOT add a relation type other than implements, fixes, or related.
```

to:

```markdown
Do NOT add a relation type other than implements, fixes, related, or superseded-by.
```

2. In the Usage section, add an example after the existing two lines:

```markdown
/sybermem-link decision-003 superseded-by decision-007
```

3. Change the relation list line from:

```markdown
`<relation>` must be one of: `implements`, `fixes`, `related`.
```

to:

```markdown
`<relation>` must be one of: `implements`, `fixes`, `related`, `superseded-by`.
```

4. In Flow step 2, change the validation text from:

```markdown
If `<relation>` is not one of `implements`/`fixes`/`related`, stop and tell the user the valid relations.
```

to:

```markdown
If `<relation>` is not one of `implements`/`fixes`/`related`/`superseded-by`, stop and tell the user the valid relations.
```

- [ ] **Step 2: Add superseded-by composite behavior to the Flow**

Replace the current steps 5–7 block:

```markdown
5. **Append the relation** — in the source record's frontmatter, add `<target-id>` to the `<relation>` field. If the field does not exist, create it as a list. If `<target-id>` is already present, skip (no duplicate).
6. **Write the source record only** — save the source file. Do NOT modify the target.
7. **Report** — tell the user which record and field were updated.
```

with:

```markdown
5. **Apply the relation**:
   - For `implements` / `fixes` / `related` — in the source record's frontmatter, add `<target-id>` to the `<relation>` field. If the field does not exist, create it as a list. If `<target-id>` is already present, skip (no duplicate).
   - For `superseded-by` — write `superseded_by: <target-id>` in the source record's frontmatter. If the field already exists with the same value, skip. If it exists with a different value, warn and ask before overwriting.
6. **Apply archive side-effect for `superseded-by` only** — if the relation is `superseded-by`, find the source record's active Key Conclusion in `## Key Conclusions`, move that line to `## Archived Conclusions`, and append `[superseded by <target-id>]` to the line. If it is already archived with the same suffix, skip.
7. **Write the source-side updates** — save the source record, and for `superseded-by` save the updated `INDEX.md`. Do NOT modify the target record.
8. **Report** — tell the user which record and field were updated, and whether a conclusion line was archived.
```

- [ ] **Step 3: Update Relation Semantics, Error Handling, Red Flags, and Rationalizations**

Make these exact edits:

1. In the Relation Semantics table, add a row:

```markdown
| `superseded-by` | source has been replaced by the target | old decision/requirement → new decision/requirement |
```

2. In Error Handling, add:

```markdown
- `superseded-by` with source == target → stop; a record cannot supersede itself.
- `superseded-by` when the source already points to a different replacement → ask before overwriting.
```

3. In Red Flags, add a bullet:

```markdown
- Deleting the source conclusion instead of moving it to `## Archived Conclusions`
```

4. In Common Rationalizations, add a row:

```markdown
| "I'll just delete the old conclusion" | History must remain searchable. Move it to Archived Conclusions with a superseded marker. |
```

5. In the Core Invariant section, replace:

```markdown
- **Only the source record's frontmatter is modified. The target record is never touched.**
```

with:

```markdown
- **Only the source side is modified. For `superseded-by`, that includes the source record's frontmatter plus the source conclusion's placement in `INDEX.md`. The target record is never touched.**
```

- [ ] **Step 4: Verify**

Run: `python -c "
t = open('packages/claude-skills/sybermem-link/SKILL.md', encoding='utf-8').read()
for marker in ['superseded-by', 'superseded_by: <target-id>', 'Archived Conclusions', 'superseded by <target-id>']:
    assert marker in t, marker
print('OK')
"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add packages/claude-skills/sybermem-link/SKILL.md
git commit -m "feat: add superseded-by handling to sybermem-link"
```

---

### Task 4: Extend /sybermem-search with topic-status and superseded hints

**Files:**
- Modify: `packages/claude-skills/sybermem-search/SKILL.md`

- [ ] **Step 1: Update topic and record-ID retrieval rules**

In `packages/claude-skills/sybermem-search/SKILL.md`, replace these two bullets in Flow step 3:

```markdown
   - **topic** → read `## Topic Index` in `.sybermem/INDEX.md`, collect the record IDs listed for that topic.
   - **record ID** → locate that record, AND reverse-scan all records' `implements`/`fixes`/`related` frontmatter fields for the ID (see Reverse references below).
```

with:

```markdown
   - **topic** → read `## Topic Index` in `.sybermem/INDEX.md`, collect the record IDs listed for that topic, and inspect any optional suffix on the topic line: `[active]`, `[low]`, or `[deprecated → <new-topic>]`.
   - **record ID** → locate that record, AND reverse-scan all records' `implements`/`fixes`/`related` frontmatter fields for the ID, plus scan for records whose `superseded_by:` field points to the ID (see Reverse references below).
```

- [ ] **Step 2: Update Enrichment and Reverse references**

Replace Flow step 4:

```markdown
4. **Enrich each hit** — for every matched record, look up its phase (from phase-index coverage map) and read its `implements`/`fixes`/`related` frontmatter fields.
```

with:

```markdown
4. **Enrich each hit** — for every matched record, look up its phase (from phase-index coverage map), read its `implements`/`fixes`/`related` fields, read its optional `superseded_by` field, and reverse-scan for records that it supersedes.
```

Replace the Reverse references section body:

```markdown
When the query is a record ID, also find which records point AT it:
- Grep all record frontmatter under `.sybermem/{changes,decisions,requirements,bugs}/` for the target ID appearing in `implements:`, `fixes:`, or `related:` fields.
- List those records under `Referenced by:` with the relation type.
```

with:

```markdown
When the query is a record ID, also find which records point AT it:
- Grep all record frontmatter under `.sybermem/{changes,decisions,requirements,bugs}/` for the target ID appearing in `implements:`, `fixes:`, or `related:` fields.
- Grep for records whose `superseded_by:` field points to the target ID; list those under `Supersedes:`.
- List the first set under `Referenced by:` with the relation type.
```

- [ ] **Step 3: Update Output Format and Error Handling**

Replace the Output Format block:

```markdown
## SyberMem Search: "<query>"

Found N records:

1. **[type-NNN]** #topic1 #topic2 — one-line conclusion (date)
   - Phase: phase-00X (phase title)
   - File: .sybermem/<type>/<file>.md
   - Relations: implements requirement-002, related change-005
   - Referenced by: change-008 (implements)

2. ...
```

with:

```markdown
## SyberMem Search: "<query>"

[Optional warning line: deprecated topic / low activity]

Found N records:

1. **[type-NNN]** #topic1 #topic2 — one-line conclusion (date)
   - Phase: phase-00X (phase title)
   - File: .sybermem/<type>/<file>.md
   - Relations: implements requirement-002, related change-005
   - Referenced by: change-008 (implements)
   - Superseded by: decision-007 — one-line conclusion
   - Supersedes: decision-003 — archived old conclusion

2. ...
```

Replace the line:

```markdown
Omit `Relations:` or `Referenced by:` lines when there are none.
```

with:

```markdown
Omit `Relations:`, `Referenced by:`, `Superseded by:`, or `Supersedes:` lines when there are none.
```

In Error Handling, add:

```markdown
- Deprecated topic → still return legacy results, but show a warning suggesting the replacement topic.
- Low-activity topic → still return results, but show an informational low-activity note.
```

- [ ] **Step 4: Update Common Rationalizations**

In the Common Rationalizations table, add:

```markdown
| "The old topic still kind of works, no need to mention it's deprecated" | Search should help users migrate. Show the replacement topic explicitly. |
| "If a record is superseded, I can ignore it entirely" | Users may be searching historical decisions. Show it, but point them to the replacement. |
```

- [ ] **Step 5: Verify**

Run: `python -c "
t = open('packages/claude-skills/sybermem-search/SKILL.md', encoding='utf-8').read()
for marker in ['[deprecated → <new-topic>]', 'Superseded by:', 'Supersedes:', 'Low-activity topic']:
    assert marker in t, marker
print('OK')
"`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add packages/claude-skills/sybermem-search/SKILL.md
git commit -m "feat: add topic-status and superseded hints to sybermem-search"
```

---

### Task 5: Sync plugin tree and verify end-to-end docs

**Files:**
- Modify: `skills/` (generated by sync)

- [ ] **Step 1: Run plugin skill sync**

Run: `python scripts/sync-plugin-skills.py`
Expected: exits 0.

- [ ] **Step 2: Verify plugin copies include the new behaviors**

Run: `python -c "
checks = [
    ('skills/sybermem-link/SKILL.md', 'superseded-by'),
    ('skills/sybermem-search/SKILL.md', 'Superseded by:'),
]
for f, marker in checks:
    t = open(f, encoding='utf-8').read()
    assert marker in t, f'{f} missing {marker}'
    print(f, 'OK')
"`
Expected: both plugin skill copies OK.

- [ ] **Step 3: No commit needed** (the sync results will be included in prior task commits if they changed, otherwise commit them now with a single doc sync commit)

If sync changed tracked files not yet committed, commit with:

```bash
git add skills/
git commit -m "chore: sync plugin skill tree for topic governance and superseded handling"
```
