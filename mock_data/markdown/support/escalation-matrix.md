---
doc_id: SUP-ESC-004
department: Support
sensitivity: internal
allowed_groups: [support, engineering, customer-success]
tenant_id: default
effective_date: 2026-04-15
owner: Support Operations
stale: false
---
# Support Escalation Matrix

## Severity Definitions

- P1: Customer production outage or confirmed data integrity issue.
- P2: Major feature unavailable for multiple customers without a workaround.
- P3: Single-customer issue with workaround.
- P4: How-to question, cosmetic issue, or documentation request.

## Escalation Path

P1 incidents go to the Support Incident channel and the owning service on-call. P2 incidents go to the support lead and service owner. P3 and P4 issues stay in the normal support queue unless they repeat across multiple customers.

## Response Targets

P1 first response target is 15 minutes. P2 is one business hour. P3 is one business day. P4 is two business days.

## Customer Communications

Support should not promise root cause until Engineering confirms it. Public incident updates must be approved by the Communications Lead for P1 incidents.
