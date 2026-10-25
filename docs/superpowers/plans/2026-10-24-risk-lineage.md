# Risk lineage wire contract implementation plan

**Goal:** Carry canonical risk IDs, selected risk parents and finding provenance across compatible message schemas.

```text
Test risk 101
   │ validation.parent_risk_ids = [101]
   ▼
Validation risk 102
   │ finding.source_risk_ids = [102]
   ▼
Finding A                         Finding B (source_risk_ids = [103])
   └──────── explicit selected findings ────────┘
                          │ chain.parent_risk_ids = [102, 103]
                          ▼
                     Chained risk 104
```

`source_risk_ids` identifies the risk rows that produced a finding. `parent_risk_ids` identifies the selected risk rows from which a new risk derives. Finding references select inputs; models do not invent database IDs.

## Complete additive field assignments

In `src/ostorlab/agent/message/proto/v3/report/risk/risk.proto`:

```protobuf
optional int64 risk_id = 25;
optional string kind = 26;
repeated int64 parent_risk_ids = 27;
```

In `src/ostorlab/agent/message/proto/v3/report/vulnerability/vulnerability.proto`:

```protobuf
repeated int64 source_risk_ids = 23;
```

Existing field numbers are unchanged. IDs refer to actual persisted backend Risk rows; an absent ID stays absent rather than defaulting to `0`. Kind values are lowercase `test`, `validation`, `chain`, `enumeration`. Protobuf int64 JSON may contain numeric strings; consumers normalize positive int64 IDs at ingestion. Repeated fields permit multiple selected parents/sources. Old messages remain readable and have no guessed origin or lineage.

Backend `createRisk`/`updateRisk` accept optional GraphQL `kind` and `parentRiskIds`.
Omitted metadata preserves existing state; supplied parents merge idempotently.
The backend checks the caller's scan access, requires every parent to belong to the
child's AgenticDeepScan, validates IDs, rejects self-edges and cycles, and applies
each update atomically. Parent summaries expose a fixed field set: `id`,
`description`, `kind`, `riskRating`, and `riskStatus`.

The derivation rules are:

- Plain agent roots use `kind=test`.
- Validation uses `kind=validation` and its triggering test as parent.
- Findings snapshot producing validation/test risk IDs before active pointers clear.
- Stream chains derive parents only from explicitly selected findings' `source_risk_ids`.
- Enumeration derives from its triggering finding.
- Root and legacy data have no inferred parents.

## Completed implementation and checks

- [x] Add actual Message.from_data/from_raw new/legacy round trips for risk and vulnerability messages and asset injection.
- [x] Observe missing-field failures before adding the schemas.
- [x] Append only the four assignments above.
- [x] Regenerate only affected `_pb2.py` and `_pb2.pyi` files with pinned generators (grpcio-tools 1.78.0, mypy-protobuf 5.1.0).
- [x] Verify serializer/report compatibility tests and inspect the generated diff. The coordinated affected suite passed 35 tests.
- [x] Commit runtime schema/asset support as **0b2b325c7fd02af18500a7d39ad286765e77e34d** and publish SDK draft PR #1264.

Portable focused reproduction, from a repository environment with test dependencies installed:

```bash
PYTHONPATH=src python -m pytest tests/agent/message/proto/v3/report/risk tests/agent/message/proto/v3/report/vulnerability tests/agent/message/message_test.py tests/agent/message/serializer_test.py -q
```

## Deployment order

- [ ] Validate and deploy backend lineage storage/API before releasing updated agents.
- [ ] Make the updated SDK schema available before agents emit the new fields.
- [ ] Release coordinated clients only after backend/API and cross-repository validation pass.

These rollout tasks remain unchecked: publishing a draft or recording tests does not authorize deployment. Clients retain the tested runtime pin **0b2b325c7fd02af18500a7d39ad286765e77e34d**. A documentation-only SDK commit changes no runtime schema and does not require repinning clients.
