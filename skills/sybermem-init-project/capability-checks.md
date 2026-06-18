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
