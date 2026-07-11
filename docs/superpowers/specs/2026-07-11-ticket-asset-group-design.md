# Spec: Ticket Asset Group Support in Ostorlab

## Context & Requirements
- **Goal:** Enable users to scan ticket assets using the YAML Asset Group (`--assets` / `-a` file) rather than being limited to the `oxo scan run asset ticket` CLI command.
- **Scope:** 
  1. Add `ticketType` and `commentType` schemas to `target_group_schema.json`.
  2. Parse the YAML-loaded `ticket` assets and construct native `Ticket` and `Comment` objects inside `AssetsDefinition.from_yaml` in `definitions.py`.
  3. Validate using unit tests inside `tests/runtimes/definitions_test.py`.

---

## 1. Schema Updates (`target_group_schema.json`)

We will add structural JSON schema definitions under `CustomTypes` in [target_group_schema.json](file:///home/asm/PycharmProjects/oxo/src/ostorlab/agent/schema/target_group_schema.json):

### commentType
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
}
```

### ticketType
```json
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

We will also register `ticket` in the top-level `assets` list:
```json
"ticket": {
  "type": "array",
  "items": {
    "$ref": "#/CustomTypes/ticketType"
  }
}
```

---

## 2. Parser Logic (`definitions.py`)

In [src/ostorlab/runtimes/definitions.py](file:///home/asm/PycharmProjects/oxo/src/ostorlab/runtimes/definitions.py), we will:
1. Import `ticket as ticket_asset` from `ostorlab.assets`.
2. Extract the `ticket` array from the validated YAML configuration:
   ```python
   ticket_assets = assets.get("ticket", [])
   ```
3. Loop through `ticket_assets` and construct the instances:
   ```python
   for asset in ticket_assets:
       parsed_comments = []
       for comment in asset.get("comments", []):
           parsed_comments.append(
               ticket_asset.Comment(
                   author=comment.get("author"),
                   message=comment.get("message")
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

---

## 3. Verification Strategy

We will update [tests/runtimes/definitions_test.py](file:///home/asm/PycharmProjects/oxo/tests/runtimes/definitions_test.py):
1. Update `valid_yaml` to include a sample `ticket` block:
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
2. Update the expected list of `assets` in `testAssetGroupDefinitionFromYaml_whenYamlIsValid_returnsValidAssetGroupDefinition` to contain the matching `ticket_asset.Ticket` instance.
3. Verify that all tests pass: `pytest tests/runtimes/definitions_test.py`
4. Format and lint code to ensure exact compliance with `AGENTS.md`: `ruff format .` and `ruff check .`
