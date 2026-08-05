# Security Policy

## Supported versions

SyberMem is pre-1.0. Security fixes are applied to the latest `main`.

## Reporting a vulnerability

Please **do not** open a public issue for security vulnerabilities.

Instead, report privately via GitHub Security Advisories:
<https://github.com/goudaren0528/sybermem/security/advisories/new>

Include:

- A description of the issue and its impact.
- Steps to reproduce (a minimal proof-of-concept is ideal).
- Affected components (core, CLI, hooks, install scripts, or a specific platform
  manifest).

## Response expectations

- Acknowledgement: within a few days.
- Assessment and remediation plan: as soon as the report is triaged.
- Fixes are prioritized by exploitability and impact.

## Scope notes

SyberMem executes local hooks and install scripts. Reports about the install
scripts (`scripts/install*.sh`, `scripts/install*.ps1`), the hook runtime
(`.sybermem/hooks/`), and any code path that reads untrusted input are in scope.
