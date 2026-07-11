# Ticket Asset Group Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable users to scan ticket assets using the YAML Asset Group (`--assets` / `-a` file) with fully validated schema constraints and parsing logic.

**Architecture:** We will extend the existing Ostorlab Asset Group schema (`target_group_schema.json`) to define custom schemas for `ticketType` and `commentType`, map them to native `Ticket` and `Comment` objects inside `AssetsDefinition.from_yaml()`, and update unit tests to verify end-to-end correctness.

**Tech Stack:** Python 3.13+, draft-2020-12 JSON Schema, pytest, ruamel.yaml.

---

### Task 1: Update JSON Schema Definitions

**Files:**
- Modify: `src/ostorlab/agent/schema/target_group_schema.json`

- [ ] **Step 1: Define `commentType` and `ticketType` under `CustomTypes`**

  In `src/ostorlab/agent/schema/target_group_schema.json`, add `commentType` and `ticketType` schemas within `"CustomTypes"`.
  
  ```json
      "commentType": {
        "description": "[Optional] - Ticket comment.",
        "type": "object",
        "properties": {
          "author": {
            "description": "[Optional] - Author of the comment.",
            "type": "string"
          },
          "message": {
            "description": "[Optional] - Comment message content.",
            "type": "string"
          }
        }
      },
      "ticketType": {
        "description": "[Optional] - Ticket asset.",
        "type": "object",
        "properties": {
          "title": {
            "description": "[Required] - Title of the ticket.",
            "type": "string"
          },
          "description": {
            "description": "[Required] - Description of the ticket.",
            "type": "string"
          },
          "ticket_id": {
            "description": "[Optional] - ID of the ticket.",
            "type": "string"
          },
          "ticket_key": {
            "description": "[Optional] - Key of the ticket.",
            "type": "string"
          },
          "comments": {
            "description": "[Optional] - Comments list.",
            "type": "array",
            "items": {
              "$ref": "#/CustomTypes/commentType"
            }
          }
        },
        "required": [
          "title",
          "description"
        ]
      }
  ```

- [ ] **Step 2: Register `ticket` property under the `assets` object**

  In the top-level `"properties"` -> `"assets"` -> `"properties"`, register `ticket` as an array pointing to `ticketType`.
  
  ```json
          "ticket": {
            "type": "array",
            "items" : {
              "$ref": "#/CustomTypes/ticketType"
            }
          }
  ```

- [ ] **Step 3: Commit schema changes**

  Run:
  ```bash
  git add src/ostorlab/agent/schema/target_group_schema.json
  git commit -m "feat(schema): add ticket and comment types to target group schema"
  ```

---

### Task 2: Implement Ticket Parser Logic

**Files:**
- Modify: `src/ostorlab/runtimes/definitions.py`

- [ ] **Step 1: Add import for `ticket` asset**

  At the top of `src/ostorlab/runtimes/definitions.py`, add the import:
  
  ```python
  from ostorlab.assets import ticket as ticket_asset
  ```

- [ ] **Step 2: Parse `ticket` asset lists in `from_yaml`**

  In `AssetsDefinition.from_yaml` method around line 321, retrieve the `ticket` assets list:
  
  ```python
          ticket_assets = assets.get("ticket", [])
  ```

- [ ] **Step 3: Construct `Ticket` and `Comment` instances in the assets loop**

  Loop through the parsed list, build the `Comment` list, build the `Ticket` object, and append to `assets_def`:
  
  ```python
          for asset in ticket_assets:
              parsed_comments = []
              for comment in asset.get("comments", []):
                  parsed_comments.append(
                      ticket_asset.Comment(
                          author=comment.get("author"),
                          message=comment.get("message"),
                      )
                  )
              assets_def.append(
                  ticket_asset.Ticket(
                      title=asset.get("title"),
                      description=asset.get("description"),
                      ticket_id=asset.get("ticket_id"),
                      comments=parsed_comments,
                      ticket_key=asset.get("ticket_key"),
                  )
              )
  ```

- [ ] **Step 4: Commit parser logic**

  Run:
  ```bash
  git add src/ostorlab/runtimes/definitions.py
  git commit -m "feat(runtime): parse and load ticket assets in asset group from yaml"
  ```

---

### Task 3: Update Unit Tests and Verify End-to-End

**Files:**
- Modify: `tests/runtimes/definitions_test.py`

- [ ] **Step 1: Import `ticket as ticket_asset` in definitions_test.py**

  Add the import at the top of `tests/runtimes/definitions_test.py`:
  
  ```python
  from ostorlab.assets import ticket as ticket_asset
  ```

- [ ] **Step 2: Add `ticket` block to the test `valid_yaml` definition**

  In `testAssetGroupDefinitionFromYaml_whenYamlIsValid_returnsValidAssetGroupDefinition`, append `ticket` entries inside the mock `valid_yaml` string:
  
  ```yaml
    ticket:
        - title: "Critical vulnerability"
          description: "Details go here"
          ticket_id: "T-01"
          ticket_key: "PROJ-1"
          comments:
            - author: "sec-ops"
              message: "confirmed reproduction"
  ```

- [ ] **Step 3: Update expected list of assets in `definitions_test.py`**

  Add the expected `ticket_asset.Ticket` instance to the end of the `assets` list in the test:
  
  ```python
          ticket_asset.Ticket(
              title="Critical vulnerability",
              description="Details go here",
              ticket_id="T-01",
              ticket_key="PROJ-1",
              comments=[
                  ticket_asset.Comment(author="sec-ops", message="confirmed reproduction")
              ]
          ),
  ```

- [ ] **Step 4: Update length assertions in the test**

  Assert `len(asset_group_def.targets) == 17` instead of `16`.

- [ ] **Step 5: Run tests and verify success**

  Run: `pytest tests/runtimes/definitions_test.py`
  Expected output: `tests/runtimes/definitions_test.py . [100%] [PASS]`

- [ ] **Step 6: Commit test changes**

  Run:
  ```bash
  git add tests/runtimes/definitions_test.py
  git commit -m "test(definitions): verify validation and parsing of ticket assets"
  ```

---

### Task 4: Linting, Formatting, and Code Quality Checks

**Files:**
- None (verification only)

- [ ] **Step 1: Format codebase**

  Run: `ruff format .`
  Expected: Success without error.

- [ ] **Step 2: Run linter check**

  Run: `ruff check . --fix`
  Expected: Success without error.

- [ ] **Step 3: Type check using mypy**

  Run: `mypy src/ostorlab/utils`
  Expected: Success without error.

- [ ] **Step 4: Run all unit tests**

  Run: `pytest`
  Expected: All tests pass.
