# Capability Checks

This file contains the digest and analysis capability checks for the `sybermem-init-project` skill.

## Step 1.2: Enable digest capability if missing

Check whether digest support is present (do not use the derived `INDEX.md` as the capability signal):

- `.sybermem/digests/`
- `.sybermem/templates/digest-template.md`

If any are missing:
- create the missing `digests/` directory
- create the missing `digest-template.md` from `project-files/.sybermem/templates/digest-template.md`
- rebuild `INDEX.md` with `sybermem project index build` when derived navigation is needed

Do this idempotently. Never duplicate the section, never overwrite an existing digest template without asking, and never treat the absence of digest support as a reason to reinitialize the whole project.

## Step 1.3: Enable analysis capability if missing

Check whether analysis support is present:

- `.sybermem/analysis/` directory
- `.sybermem/analysis/phase-index.md`

If any are missing:
- create the missing `analysis/` directory
- create the missing `phase-index.md` from `project-files/.sybermem/analysis/phase-index.md`

Do this idempotently. Never overwrite an existing phase-index without asking.

## Step 1.4: Enable theme-digest capability if missing

Check whether theme-digest support is present (do not use the derived `INDEX.md` as the capability signal):

- `.sybermem/theme-digests/` directory
- `.sybermem/templates/theme-digest-template.md`

If any are missing:
- create the missing `theme-digests/` directory
- create the missing `theme-digest-template.md` from `project-files/.sybermem/templates/theme-digest-template.md`
- rebuild `INDEX.md` with `sybermem project index build` when derived navigation is needed

Do this idempotently. Never duplicate the section, never overwrite an existing theme digest template without asking.

## Step 1.5: Provision Archived Conclusions section if missing

Archived Conclusions are also generated from records and digests. Do not check for or insert an Archived Conclusions section or anchor by hand; run `sybermem project index build` to regenerate the complete derived `INDEX.md`.
