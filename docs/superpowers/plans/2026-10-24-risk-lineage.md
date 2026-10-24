# Risk lineage wire contract implementation plan

> **For agentic workers:** Use the shared contract `/tmp/risk-lineage-20261024/CONTRACT.md` for cross-repository integration and independent review.

**Goal:** Carry stable Risk IDs and multiple parents across risk messages, and producer Risk IDs across vulnerability messages.

**Architecture:** Append compatible protobuf fields without changing existing field numbers. Regenerate only the two affected runtime modules and type stubs using pinned generators. Exercise real Message.from_data/from_raw round trips for both updated and legacy payloads.

**Tech Stack:** Protobuf 6, grpcio-tools 1.78.0, mypy-protobuf 5.1.0, pytest.

- [x] Add four wire round-trip tests in `tests/agent/message/proto/v3/report/risk/lineage_test.py`.
- [x] Run tests before implementation: the risk_id and source_risk_ids cases fail on missing schema fields; legacy cases pass.
- [x] Append risk_id=25, kind=26, parent_risk_ids=27 in `risk.proto`, and source_risk_ids=23 in `vulnerability.proto`.
- [x] Regenerate the two `_pb2.py` and `_pb2.pyi` files with repository-pinned compilers in a temporary venv.
- [x] Run new plus existing report/risk and report/vulnerability tests: 18 pass.
- [ ] Run affected serializer tests and Ruff, inspect generated diff, and independently review compatibility.
- [ ] Commit the scoped schema, generated modules, and tests; prepare a matching SDK PR before agent rollout.
