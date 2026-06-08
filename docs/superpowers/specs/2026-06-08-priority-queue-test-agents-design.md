# Design Doc: Priority Queue Test Agents

## Overview
This document specifies the design for two new test agents used to verify the RabbitMQ message priority routing of the `v3.report.vulnerability` messages in the OXO agent framework.

The goal is to verify that messages with higher risk ratings (e.g., `CRITICAL` with priority 8) are consumed before messages with lower risk ratings (e.g., `INFO` with priority 1), even if the lower priority messages arrived first.

## Architecture & Communication Flow

```mermaid
sequence_flow
    participant agent_priority_sender
    participant RabbitMQ
    participant agent_priority_receiver

    agent_priority_sender ->> RabbitMQ: Emit 5 messages (INFO, LOW, MEDIUM, HIGH, CRITICAL)
    Note over RabbitMQ: All 5 messages queued.
    RabbitMQ ->> agent_priority_receiver: Deliver INFO (first message to arrive)
    Note over agent_priority_receiver: Receives INFO. Sleeps 2 minutes.
    Note over RabbitMQ: Remaining 4 messages sorted by priority in queue.
    agent_priority_receiver -->> RabbitMQ: Acknowledge INFO (after 2 mins)
    RabbitMQ ->> agent_priority_receiver: Deliver CRITICAL (highest remaining)
    agent_priority_receiver -->> RabbitMQ: Acknowledge CRITICAL
    RabbitMQ ->> agent_priority_receiver: Deliver HIGH
    agent_priority_receiver -->> RabbitMQ: Acknowledge HIGH
    RabbitMQ ->> agent_priority_receiver: Deliver MEDIUM
    agent_priority_receiver -->> RabbitMQ: Acknowledge MEDIUM
    RabbitMQ ->> agent_priority_receiver: Deliver LOW
    agent_priority_receiver -->> RabbitMQ: Acknowledge LOW
```

### Components

### 1. `agent_priority_sender`
* **Purpose:** Emits 5 hardcoded vulnerability messages on startup with different risk ratings in ascending order of priority (lowest priority first).
* **Outgoing selectors:** `v3.report.vulnerability`
* **Flow:**
  * Constructs a standard knowledge base entry (`kb.Entry`).
  * Emits 5 reports via `report_vulnerability`:
    1. `INFO` (Priority 1)
    2. `LOW` (Priority 4)
    3. `MEDIUM` (Priority 5)
    4. `HIGH` (Priority 7)
    5. `CRITICAL` (Priority 8)
  * Sleeps for 10 seconds before terminating to ensure everything is sent.

### 2. `agent_priority_receiver`
* **Purpose:** Receives vulnerability reports, sleeping on the first message to allow RabbitMQ queue accumulation and verify priority-based delivery.
* **Incoming selectors:** `v3.report.vulnerability`
* **Flow:**
  * Keeps a flag `self._first_received = True`.
  * On the first message (`INFO`):
    * Logs the receipt of `INFO`.
    * Sets `_first_received = False`.
    * Sleeps for 120 seconds (`time.sleep(120)`).
  * On subsequent messages:
    * Logs the receipt in order of consumption (should be `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).

## File Layout

### `agent_priority_sender`
* `oxo.yaml` — Configures out_selectors and metadata.
* `Dockerfile` — Builds the sender image.
* `requirements.txt` — Specifies dependencies (`ostorlab[agent]`, `rich`).
* `agent/priority_sender.py` — The agent class logic.

### `agent_priority_receiver`
* `oxo.yaml` — Configures in_selectors and metadata.
* `Dockerfile` — Builds the receiver image.
* `requirements.txt` — Specifies dependencies (`ostorlab[agent]`, `rich`).
* `agent/priority_receiver.py` — The agent class logic.

## Verification Success Criteria
When both agents are run on a local bus or test runtime environment:
1. `agent_priority_receiver` receives the first message (`INFO`) and goes to sleep.
2. During the 2-minute sleep, the remaining 4 messages are queued.
3. Once the receiver wakes up, the logging output of `agent_priority_receiver` MUST show the following consumption sequence exactly:
   * `RECEIVED RISK: CRITICAL`
   * `RECEIVED RISK: HIGH`
   * `RECEIVED RISK: MEDIUM`
   * `RECEIVED RISK: LOW`
