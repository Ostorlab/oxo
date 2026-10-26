# Persisted risk messages implementation plan

> For agentic workers: implement the independent repository tasks in the existing isolated Herdr worktrees, with test-first verification and a final independent review.

**Goal:** Publish risk messages only after successful backend persistence, carrying canonical `risk_id` instead of duplicating backend kind/parent metadata.

**Architecture:** Batch and stream persist kind/parents through GraphQL, verify the successful response and positive int64 ID, then publish. Auto-exploit requires the canonical ID and loads the authorized risk from its current AgenticDeepScan before activating or executing it. Findings continue to carry `source_risk_ids` for selecting chain parents. Backend/UI lineage storage remains authoritative.

**Tech stack:** Python, protobuf2, Django/Graphene, pytest, existing local PostgreSQL/Redis integration environment.

## Shared contract

- Keep risk wire field `risk_id = 25`; remove `kind = 26` and `parent_risk_ids = 27`. Reserve both removed numbers and names. Remove their SDK Risk asset constructor fields and the parent Sequence serializer workaround.
- Keep protobuf risk_id optional for generic wire decoding compatibility; every supported producer and the auto-exploit execution boundary require a valid persisted positive int64 ID. A message missing it is rejected before risk writes, status/cache updates or execution. There is no description-based create fallback for received risks.
- Keep internal agent Risk/RiskInfo kind/parents fields and GraphQL persistence inputs. Remove metadata only from outgoing risk payloads and SDK wire schema. Keep vulnerability source_risk_ids = 23 unchanged.
- Add robot GraphQL `agenticRisk(riskId: ID!, agenticDeepScanId: ID!): RiskType`. Verify access to the requested session's scan and require the risk to belong to that exact session. Return an error for missing, malformed, inaccessible or foreign-session IDs. Reuse RiskType and its parent summaries.
- Consumer query selects `id description riskRating kind parents { id }`; backend values, not any obsolete message metadata, initialize RiskInfo. The current ADS comes from successful persist_ai_pentest. Do not create a risk, activate stale pointers, start execution or update the cache after a failed lookup.
- Preserve update-by-ID semantics in the runner and validation child creation/provenance. A failed update of the canonical row must stop execution; no replacement row may be created.
- A producer persistence failure, false/missing success, malformed/nonpositive/out-of-range ID or unconfigured backend must prevent emission and success/dedup/cache markers, with an explicit failure path that permits normal upstream retry. Successful repeated persistence remains idempotent. Do not introduce an outbox or broad retry redesign.
- Existing six PRs are open drafts with matching clean feature heads. Update affected existing PRs, keep risk-chain labels, no merge/deployment. The frontend has no wire contract change.

## 1. SDK wire and asset (root)

Files: src/ostorlab/agent/message/proto/v3/report/risk/risk.proto, risk_pb2.py/.pyi, src/ostorlab/assets/risk.py, tests/agent/message/proto/v3/report/risk/lineage_test.py, existing risk/asset/serializer tests.

- [x] Add failing tests asserting the risk descriptor has risk_id25, lacks kind/parent fields and reserves26/27 and their names; canonical ID round trips on real raw wire.
- [x] Replace obsolete metadata/tuple tests with canonical-ID wire and legacy decoding controls. Legacy raw wire with removed tags must not expose those tags as metadata.
- [x] Remove fields/imports/workaround, regenerate only the affected risk modules using existing pinned generators.
- [x] Run SDK focused risk/vulnerability/message/serializer/asset tests, scoped mypy and Ruff; commit/push a schema revision before updating client pins.

Example target assertion:

```python
def testRiskWire_whenCanonicalRiskSerialized_preservesOnlyRiskReference() -> None:
    sent = message.Message.from_data(
        "v3.report.risk",
        {"description": "Persisted chain", "rating": "High", "risk_id": 8},
    )
    received = message.Message.from_raw("v3.report.risk", sent.raw)
    assert int(received.data["risk_id"]) == 8
    assert "kind" not in received.data
    assert "parent_risk_ids" not in received.data
```

SDK evidence: four intended failures before the removal, then **40 affected tests passed**. Scoped mypy checks two files; Ruff and diff whitespace checks pass. The legacy decoder remains compatible, while execution requires persistence at the agent boundary.

## 2. Backend canonical read (backend worker)

Files: reporting_engine/ai_pentest/schemas/robot.py, reporting_engine/apis/schemas/robot.py and robot schema tests.

- [ ] Reproduce missing agenticRisk field through actual robot GraphQL tests.
- [ ] Add the small session/scan-authorized read and schema composition; validate ID syntax/range without exposing unrelated rows.
- [ ] Assert exact stored kind/parents, ordered parent summaries, existing rating/status read compatibility, unauthorized scan/tenant, other session, unknown risk/session and malformed IDs.
- [ ] Run the affected backend suites inside the existing risk-lineage-backend container and static/typing checks. No host Django, reseed, migration or unrelated rating-validation change.
- [ ] Coordinate one owned API refresh after the tested commit and verify the read through real HTTP. Report READY with unchanged credential bytes/demo IDs.

Canonical client query:

```graphql
query PersistedRisk($riskId: ID!, $agenticDeepScanId: ID!) {
  agenticRisk(riskId: $riskId, agenticDeepScanId: $agenticDeepScanId) {
    id description riskRating kind parents { id }
  }
}
```

## 3. Auto-exploit consumer (auto worker)

Files: agent/apis/api.py and tests/apis/api_test.py, agent/storage.py and tests/storage_test.py, agent/auto_exploit_agent.py and tests/auto_exploit_agent_test.py, agent/pentest/runner.py and tests/pentest/runner_test.py, workflow definitions if needed.

- [ ] Add failing tests for missing/invalid risk ID, lookup failure/foreign context and conflicting old message metadata. Assert no createRisk, execution, pointer/status/cache mutation on failure.
- [ ] Add API/storage canonical metadata loading using the shared query, current ADS and normal robot headers. Validate response identity and required metadata; do not trust message kind/parents.
- [ ] Replace incoming no-ID creation fallback with mandatory load-by-ID; preserve backend kind/parents when runner updates by canonical ID.
- [ ] Require successful current-session and canonical update before execution; keep validation creation and source snapshots intact.
- [ ] Adapt existing process fixtures to real persisted-risk contract rather than weakening assertions. Run API/storage/process/runner/validation/cache suites, typing/Ruff and real generated-wire controls.

## 4. Stream and batch publishers (stream worker)

Files: both agent/threat_intelligence_agent.py, agent/storage.py, agent/definitions.py or risk assets' to_report_payload methods if they add wire metadata; their emission/storage/dedup tests.

- [ ] Add failing persistence-before-publish tests for stream request/response, ordinary assets, vulnerability chains and multi-asset risks, plus batch emission.
- [ ] Reject None/false/missing success and invalid IDs before emit or processed/dedup/cache success markers. Exercise retry after failure without duplicate backend rows.
- [ ] Keep kind/parents on backend persist calls; emit only canonical risk_id alongside existing required description/rating and target. Verify actual SDK wire serialization after new SDK source is available.
- [ ] Audit every risk emission call site in both agents, then run relevant storage/emission/lineage/multi-asset/processor tests and static checks. Keep normal attempt-limit policy and unrelated tools unchanged.

## 5. Integration, review and publication (root)

Files: runtime/persist-first-20261026 evidence; existing runtime/integration harness and tracked contract documentation in affected repositories.

- [ ] Point local integration at the new SDK and tested backend READY. Verify positive real GraphQL/PostgreSQL/Redis dataflow: persist chain with exact selected parents, send ID-only protobuf, receive canonical metadata, execute/update same risk/analysis, emit findings with source IDs.
- [ ] Verify mandatory-persistence failure behavior and unauthorized/foreign lookup boundaries; no no-ID typed-create fallback assertions remain.
- [ ] Update all three affected client dependency pins to the exact new SDK commit after testing. Preserve schema numbers for vulnerability provenance.
- [ ] Independently review the full change for dropped risks, stale pointers, cache/dedup poisoning, wire fields and cross-scan lookup. Address confirmed defects with regressions.
- [ ] Update affected draft PR descriptions and wire contract docs; preserve historical evidence clearly. Reset review labels, trigger one exact-head automated review per changed PR and verify effective CI. Explain optional cosmetic suggestions without unrelated churn.
- [ ] Leave API/UI live for review; do not merge, deploy or reseed. Record exact heads and evidence limits in the final handoff.
