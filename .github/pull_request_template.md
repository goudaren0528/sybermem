## Summary

<!-- What does this PR change and why? -->

## Checklist

- [ ] `pytest packages/core packages/cli` is green
- [ ] `python scripts/check-plugin-package.py` prints `OK`
- [ ] If I changed skills, I edited `packages/claude-skills/` and ran `python scripts/sync-plugin-skills.py`
- [ ] If I changed a hook, all 3 authoritative copies are in sync and the hook fails open
- [ ] If I bumped the version, I edited `VERSION` and ran `python scripts/sync-version.py`
- [ ] Dual-language docs (`README.md` / `README.en.md`) are in sync for user-facing changes
- [ ] No cache artifacts committed (`__pycache__`, `.pytest_cache`, `dist/`)

## Notes

<!-- Anything reviewers should know: risks, follow-ups, deferred items. -->
