# Implementation Guide: Self-Correcting Agentic SQL Analyst

**Project:** Olist E-commerce Analytics Integration

**Stack:** CrewAI, Snowflake, dbt, Streamlit

## 1. Executive Summary: The "Why"

Traditional BI dashboards are static. If a stakeholder has a question not covered by a chart, they have to wait for a Data Engineer to build a new view. This project implements an **Agentic SQL Analyst** that uses LLMs to "reason" through your **dbt-transformed Snowflake data**, enabling natural language querying with a self-correction loop for 100% accuracy.

---

## 2. The Toolset & Rationale

| Tool | Role | The "Why" (Engineering Logic) |
| --- | --- | --- |
| **CrewAI** | Orchestrator | Unlike simple scripts, CrewAI allows for "Role-Based" agency. We can separate the *writing* of SQL from the *auditing* of SQL, mimicking a real-world peer-review process. |
| **Snowflake** | Data Warehouse | Provides the high-performance compute and structured storage for the Olist dataset. Its JSON error returns are highly descriptive, which helps the agent "self-correct." |
| **dbt (Data Build Tool)** | Metadata Engine | We don't want the agent querying messy raw data. dbt provides the `manifest.json`, which acts as the "Brain" or "Map" for the agent to understand our Gold-layer tables. |
| **Streamlit** | Interface | Provides a professional, lightweight frontend. It allows us to stream the agent's "thoughts" in real-time so the user sees the reasoning process. |

---

## 3. Knowledge Gaps to Bridge

To execute this, you must move beyond linear pipelines and understand:

1. **Iterative Logic (Loops):** Traditional pipelines are Directed Acyclic Graphs (DAGs). Agentic workflows allow for **Cycles**—where the output of a failure goes back to the input for a retry.
2. **Context Injection:** Large Language Models (LLMs) don't know your specific column names (like `order_purchase_timestamp`). You must learn to inject your **dbt Schema** into the LLM's prompt.
3. **Tool Abstraction:** Learning how to wrap a Python function (like a Snowflake connector) into a "Tool" that an AI can understand and trigger.

---

## 4. Step-by-Step Implementation Roadmap

### Phase 1: Metadata Preparation (The "Map")

**Step:** Generate and parse your dbt `manifest.json`.

**Why:** The agent needs to know that `fct_orders` is the source of truth for sales, not `raw_orders`. By parsing your dbt documentation, you give the agent "Business Context."

* **Action:** Run `dbt docs generate` and create a Python script to extract table names and column descriptions.

### Phase 2: Building the "Execution" Tool

**Step:** Create a Python class that connects to Snowflake.

**Why:** An agent is just a brain; it needs "hands" to interact with the world. This tool allows the agent to run code and—most importantly—**capture the error message** if the SQL fails.

* **Action:** Write a function that takes a string (SQL), executes it via `snowflake-connector-python`, and returns either the result or the traceback.

### Phase 3: Defining the Agentic Duo

**Step:** Configure two distinct CrewAI agents.

**Why:** One agent (The Developer) is biased toward "doing." The second agent (The Auditor) is biased toward "skepticism." This friction reduces hallucinations.

* **Agent A (The SQL Architect):** Tasked with generating the most efficient Snowflake SQL.
* **Agent B (The Data Quality Lead):** Tasked with checking the results against the original question and the schema metadata.

### Phase 4: The Self-Correction Loop

**Step:** Set the CrewAI process to `Sequential` with a retry limit.

**Why:** If Agent A writes a query that uses a column name incorrectly, Snowflake will throw an error. Agent B sees this error, explains it to Agent A, and triggers a "Self-Correction" cycle.

* **Action:** Define a Task where the `output` of the SQL tool is fed back into the prompt if an "Error" string is detected.

---

## 5. User Access & Deployment

**How users will interact:**

1. **The Input:** User types: *"Which Brazilian state has the longest average shipping time?"*
2. **The Reasoning:** The Streamlit UI displays: *"Searching dbt metadata... found 'dim_geolocation' and 'fct_orders'. Writing SQL..."*
3. **The Recovery:** If the first attempt fails (e.g., a join error), the UI shows: *"Error detected in join logic. Self-correcting query..."*
4. **The Delivery:** The final table is displayed alongside a Power BI-style visualization.
