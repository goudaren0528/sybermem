# Capability Checks

This file contains the digest and analysis capability checks for the `sybermem-init-project` skill.

## Step 1.2: Enable digest capability if missing

For projects that already have `.sybermem/INDEX.md`, check whether digest support is present:

- `.sybermem/digests/`
- `.sybermem/templates/digest-template.md`
- `## Stage Digests` section in `.sybermem/INDEX.md`

If any are missing:
- create the missing `digests/` directory
- create the missing `digest-template.md` from `project-files/.sybermem/templates/digest-template.md`
- insert the missing `## Stage Digests` section into `INDEX.md`

Do this idempotently. Never duplicate the section, never overwrite an existing digest template without asking, and never treat the absence of digest support as a reason to reinitialize the whole project.

## Step 1.3: Enable analysis capability if missing

For projects that already have `.sybermem/INDEX.md`, check whether analysis support is present:

- `.sybermem/analysis/` directory
- `.sybermem/analysis/phase-index.md`

If any are missing:
- create the missing `analysis/` directory
- create the missing `phase-index.md` from `project-files/.sybermem/analysis/phase-index.md`

Do this idempotently. Never overwrite an existing phase-index without asking.

## Step 1.4: Enable theme-digest capability if missing

For projects that already have `.sybermem/INDEX.md`, check whether theme-digest support is present:

- `.sybermem/theme-digests/` directory
- `.sybermem/templates/theme-digest-template.md`
- `## Theme Digests` section in `.sybermem/INDEX.md`
- `<!-- add new theme digest records here -->` anchor

If any are missing:
- create the missing `theme-digests/` directory
- create the missing `theme-digest-template.md` from `project-files/.sybermem/templates/theme-digest-template.md`
- insert the missing `## Theme Digests` section into `INDEX.md`

Do this idempotently. Never duplicate the section, never overwrite an existing theme digest template without asking.

## Step 1.5: Provision Archived Conclusions section if missing

For projects that already have `.sybermem/INDEX.md`, check whether the Archived Conclusions section is present:

- `## Archived Conclusions` in `.sybermem/INDEX.md`
- `<!-- add new archived conclusions here -->` anchor

If missing, insert the section between `## Key Conclusions` (after its closing `---`) and `## Stage Digests`. Do this idempotently. Never duplicate the section, and never move or rewrite existing conclusions when inserting this block.
