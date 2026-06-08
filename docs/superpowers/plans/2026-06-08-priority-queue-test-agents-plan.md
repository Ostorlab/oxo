# Priority Queue Test Agents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create two independent Ostorlab test agents based on the template agent, where one sender agent emits 5 hardcoded risk reports in ascending priority order, and one receiver agent receives the first message, sleeps for 2 minutes to allow RabbitMQ priority-based queue accumulation, and then consumes the remaining messages in priority order.

**Architecture:** Startup-driven direct emitter for sender (`agent_priority_sender`), and state-driven blocker with `prefetch_count=1` for receiver (`agent_priority_receiver`).

**Tech Stack:** Python 3.11, Ostorlab SDK, RabbitMQ/aio-pika, Rich Logger.

---

### Task 1: Create Agent Priority Sender (`agent_priority_sender`)

**Files:**
- Create: `/home/yasser/Agents/agent_priority_sender/oxo.yaml`
- Create: `/home/yasser/Agents/agent_priority_sender/Dockerfile`
- Create: `/home/yasser/Agents/agent_priority_sender/requirements.txt`
- Create: `/home/yasser/Agents/agent_priority_sender/agent/__init__.py`
- Create: `/home/yasser/Agents/agent_priority_sender/agent/priority_sender.py`

- [ ] **Step 1: Create the directory and config file `oxo.yaml`**
  Write `/home/yasser/Agents/agent_priority_sender/oxo.yaml` with the following content:
  ```yaml
  kind: Agent
  name: agent_priority_sender
  version: 0.1.0
  description: Priority Queue test sender agent.
  in_selectors: []
  out_selectors:
    - v3.report.vulnerability
  docker_file_path: Dockerfile
  docker_build_root: .
  ```

- [ ] **Step 2: Create the `requirements.txt` file**
  Write `/home/yasser/Agents/agent_priority_sender/requirements.txt` with:
  ```
  ostorlab[agent]
  rich
  ```

- [ ] **Step 3: Create the `Dockerfile` file**
  Write `/home/yasser/Agents/agent_priority_sender/Dockerfile` with:
  ```dockerfile
  FROM python:3.11-alpine as base
  FROM base as builder
  RUN apk add build-base
  RUN mkdir /install
  WORKDIR /install
  COPY requirements.txt /requirements.txt
  RUN pip install --prefix=/install -r /requirements.txt
  FROM base
  COPY --from=builder /install /usr/local
  RUN mkdir -p /app/agent
  ENV PYTHONPATH=/app
  COPY agent /app/agent
  COPY oxo.yaml /app/agent/oxo.yaml
  WORKDIR /app
  CMD ["python", "/app/agent/priority_sender.py"]
  ```

- [ ] **Step 4: Create the `agent/__init__.py` module file**
  Write an empty file `/home/yasser/Agents/agent_priority_sender/agent/__init__.py`.

- [ ] **Step 5: Create the agent code `agent/priority_sender.py`**
  Write `/home/yasser/Agents/agent_priority_sender/agent/priority_sender.py` with the following content:
  ```python
  """Priority sender agent implementation."""

  import logging
  import time
  from rich import logging as rich_logging

  from ostorlab.agent import agent
  from ostorlab.agent.kb import kb
  from ostorlab.agent.mixins import agent_report_vulnerability_mixin as vuln_mixin

  logging.basicConfig(
      format="%(message)s",
      datefmt="[%X]",
      level="INFO",
      force=True,
      handlers=[rich_logging.RichHandler(rich_tracebacks=True)],
  )
  logger = logging.getLogger(__name__)
  logger.setLevel("INFO")


  class PrioritySenderAgent(agent.Agent, vuln_mixin.AgentReportVulnMixin):
      """Agent that emits 5 hardcoded vulnerabilities with ascending priority."""

      def __init__(self, agent_definition, agent_settings) -> None:
          agent.Agent.__init__(self, agent_definition, agent_settings)
          vuln_mixin.AgentReportVulnMixin.__init__(self)

      def start(self) -> None:
          """Emit 5 vulnerabilities with different risk ratings."""
          logger.info("Starting priority sender agent...")

          entry = kb.Entry(
              title="Test Priority Queue Vulnerability",
              short_description="Vulnerability used to test message prioritization.",
              description="Vulnerability used to test message prioritization.",
              recommendation="No action needed.",
              security_issue=True,
              privacy_issue=False,
              has_public_exploit=False,
              targeted_by_malware=False,
              targeted_by_ransomware=False,
              targeted_by_nation_state=False,
              references={},
          )

          # We send them from lowest to highest priority so we can verify if the queue reorders them
          risks = [
              (vuln_mixin.RiskRating.INFO, "Risk Info Details"),
              (vuln_mixin.RiskRating.LOW, "Risk Low Details"),
              (vuln_mixin.RiskRating.MEDIUM, "Risk Medium Details"),
              (vuln_mixin.RiskRating.HIGH, "Risk High Details"),
              (vuln_mixin.RiskRating.CRITICAL, "Risk Critical Details"),
          ]

          for rating, detail in risks:
              logger.info("Emitting vulnerability with rating %s", rating.name)
              self.report_vulnerability(
                  entry=entry,
                  technical_detail=detail,
                  risk_rating=rating,
              )

          logger.info("All 5 risks emitted. Sleeping 10 seconds to ensure delivery...")
          time.sleep(10)
          logger.info("Sender execution completed.")


  if __name__ == "__main__":
      logger.info("Starting agent...")
      PrioritySenderAgent.main()
  ```

- [ ] **Step 6: Commit the sender agent files**
  Add files and commit.

---

### Task 2: Create Agent Priority Receiver (`agent_priority_receiver`)

**Files:**
- Create: `/home/yasser/Agents/agent_priority_receiver/oxo.yaml`
- Create: `/home/yasser/Agents/agent_priority_receiver/Dockerfile`
- Create: `/home/yasser/Agents/agent_priority_receiver/requirements.txt`
- Create: `/home/yasser/Agents/agent_priority_receiver/agent/__init__.py`
- Create: `/home/yasser/Agents/agent_priority_receiver/agent/priority_receiver.py`

- [ ] **Step 1: Create the directory and config file `oxo.yaml`**
  Write `/home/yasser/Agents/agent_priority_receiver/oxo.yaml` with the following content:
  ```yaml
  kind: Agent
  name: agent_priority_receiver
  version: 0.1.0
  description: Priority Queue test receiver agent.
  in_selectors:
    - v3.report.vulnerability
  out_selectors: []
  docker_file_path: Dockerfile
  docker_build_root: .
  ```

- [ ] **Step 2: Create the `requirements.txt` file**
  Write `/home/yasser/Agents/agent_priority_receiver/requirements.txt` with:
  ```
  ostorlab[agent]
  rich
  ```

- [ ] **Step 3: Create the `Dockerfile` file**
  Write `/home/yasser/Agents/agent_priority_receiver/Dockerfile` with:
  ```dockerfile
  FROM python:3.11-alpine as base
  FROM base as builder
  RUN apk add build-base
  RUN mkdir /install
  WORKDIR /install
  COPY requirements.txt /requirements.txt
  RUN pip install --prefix=/install -r /requirements.txt
  FROM base
  COPY --from=builder /install /usr/local
  RUN mkdir -p /app/agent
  ENV PYTHONPATH=/app
  COPY agent /app/agent
  COPY oxo.yaml /app/agent/oxo.yaml
  WORKDIR /app
  CMD ["python", "/app/agent/priority_receiver.py"]
  ```

- [ ] **Step 4: Create the `agent/__init__.py` module file**
  Write an empty file `/home/yasser/Agents/agent_priority_receiver/agent/__init__.py`.

- [ ] **Step 5: Create the agent code `agent/priority_receiver.py`**
  Write `/home/yasser/Agents/agent_priority_receiver/agent/priority_receiver.py` with the following content:
  ```python
  """Priority receiver agent implementation."""

  import logging
  import time
  from rich import logging as rich_logging

  from ostorlab.agent import agent
  from ostorlab.agent.message import message as m

  logging.basicConfig(
      format="%(message)s",
      datefmt="[%X]",
      level="INFO",
      force=True,
      handlers=[rich_logging.RichHandler(rich_tracebacks=True)],
  )
  logger = logging.getLogger(__name__)
  logger.setLevel("INFO")


  class PriorityReceiverAgent(agent.Agent):
      """Agent that receives vulnerabilities, sleeping on the first to test priority queues."""

      def __init__(self, agent_definition, agent_settings) -> None:
          super().__init__(agent_definition, agent_settings)
          self._first_received = True

      def start(self) -> None:
          """Start execution of the agent."""
          logger.info("Starting priority receiver agent...")

      def process(self, message: m.Message) -> None:
          """Process incoming vulnerability reports."""
          risk_rating = message.data.get("risk_rating")
          logger.info("RECEIVED RISK: %s", risk_rating)

          if self._first_received is True:
              self._first_received = False
              logger.info("First risk message received (%s). Sleeping for 2 minutes...", risk_rating)
              time.sleep(120)
              logger.info("Woke up from 2-minute sleep. Ready to process other messages...")


  if __name__ == "__main__":
      logger.info("Starting agent...")
      PriorityReceiverAgent.main()
  ```

- [ ] **Step 6: Commit the receiver agent files**
  Add files and commit.

---

### Task 3: Formatting & Quality Check

- [ ] **Step 1: Check formatting with Ruff**
  Run: `ruff check /home/yasser/Agents/agent_priority_sender /home/yasser/Agents/agent_priority_receiver`
  Expected: No violations.
