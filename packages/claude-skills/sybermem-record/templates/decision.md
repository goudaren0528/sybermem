---
type: decision
record_id: {{record_id}}
date: {{date}}
title: {{title}}
status: {{status}}
supersedes: {{supersedes}}
key_conclusion: {{key_conclusion}}
topics: {{topics}}
# Optional relations (forward-only, values are existing record IDs):
# implements: [requirement-<record-id>]   # this decision implements a requirement
# fixes: [bug-<record-id>]                 # this decision addresses a bug
# superseded_by: decision-<record-id>      # this decision has been replaced by a newer one
# related: [type-<record-id>]              # weak association
---

## Context
{{context}}

## Considered Options
{{alternatives}}

## Final Decision
{{decision}}

## Impact and Consequences
{{consequences}}

## Related Changes
{{related_changes}}

## Notes
{{notes}}
