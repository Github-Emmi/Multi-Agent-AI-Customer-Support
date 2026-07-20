# 12 — Software Testing Strategy

> **Project:** Multi-Agent AI Customer Support Assistant  
> **Status:** In Progress  
> **Author:** Gemini AI Agent

---

## 1. Overview

This document outlines the comprehensive software testing strategy for the Multi-Agent AI Customer Support Assistant. The goal is to ensure the system is robust, reliable, and meets all functional and non-functional requirements outlined in the project documentation.

This strategy follows the V-model, incorporating multiple levels and types of testing, building upon the existing test foundation.

## 2. Testing Scope

This strategy covers the entire application stack:
- **Backend:** FastAPI, LangGraph Agents, RAG Pipeline, Database Interactions.
- **Frontend:** Next.js Components, Hooks, and UI/UX.
- **End-to-End (E2E):** Full user journeys simulating real-world scenarios.
- **Non-Functional:** Performance, Load, and basic Security.

## 3. Testing Levels & Types

### 3.1. Unit Testing

- **Objective:** Verify the smallest individual components (functions, classes) of the application work as expected in isolation.
- **Tools:**
    - **Backend:** `pytest`
    - **Frontend:** `Jest` + `React Testing Library (RTL)`
- **Existing Coverage:** Good foundational coverage for RAG pipeline, agent nodes (mocked), and API endpoints (mocked).
- **Planned Additions:**
    - Increase test cases for `detect_intent` to cover more edge cases and linguistic variations.
    - Add unit tests for all utility functions in `backend/agents/utils.py`.
    - Ensure every major UI component in `frontend/components/` has a corresponding `.test.tsx` file covering its different states (loading, error, success).
    - Add unit tests for all frontend hooks in `frontend/hooks/`.

### 3.2. Integration Testing

- **Objective:** Verify that different modules and services work together correctly.
- **Tools:** `pytest`
- **Existing Coverage:** API-level tests exist but mock the core `run_agents` function.
- **Planned Additions:**
    - **New Test Suite (`test_integration_agents.py`):** This suite will be dedicated to testing the full agent orchestration flow.
    - Tests will make an API call to `/chat`.
    - The test will **not** mock `run_agents` or the RAG retriever.
    - It **will** mock the final LLM call (e.g., `ChatOpenAI.invoke`) to ensure deterministic outcomes and avoid external dependencies.
    - This will validate the correct flow of data from the API through the LangGraph router, to the correct agent(s), through the RAG retriever, and to the point of LLM invocation.
    - These tests will be marked with `@pytest.mark.integration`.

### 3.3. System & E2E Testing

- **Objective:** Validate the complete, integrated system from the user's perspective.
- **Tools:** `Playwright`
- **Existing Coverage:** E2E tests for `auth`, `chat`, and `dashboard` exist.
- **Planned Additions:**
    - **Admin Flow:** Add a new E2E test `admin.spec.ts` to cover the admin login and knowledge base PDF upload flow.
    - **Multi-Agent Scenario:** Enhance `chat.spec.ts` to include a test case that triggers multiple agents (e.g., "I paid but my account is not upgraded") and verifies that the response contains distinct sections for each agent.
    - **Error Handling:** Add a test case to simulate a backend API failure and verify that the frontend displays a user-friendly error message.

### 3.4. Acceptance Testing

- **Objective:** Verify the system meets business requirements and is acceptable to the user.
- **Tools:** `pytest`
- **Existing Coverage:** An excellent acceptance test `test_retrieval_precision_80_percent` exists in `test_rag.py`.
- **Planned Additions:**
    - **Intent Classification Accuracy:** Create a new acceptance test that runs a batch of predefined queries against `detect_intent` and asserts that the classification accuracy meets a specific threshold (e.g., >85%).

### 3.5. Non-Functional Testing

- **Objective:** Evaluate system performance, security, and other non-functional attributes.
- **Tools:** `locust` (Performance), `bandit` (Security).
- **Existing Coverage:** None. This is a key area of expansion.
- **Planned Additions:**
    - **Performance Testing (`locust`):**
        - Create a `locustfile.py` in the `backend/tests/performance` directory.
        - Define a `ChatUser` task set that simulates:
            1. Logging in.
            2. Starting a new chat session.
            3. Sending a series of chat messages to the `/chat` endpoint.
        - Run a baseline load test to measure response times and requests per second under concurrent load.
    - **Security Scanning (`bandit`):**
        - Run `bandit -r backend/` to scan the backend codebase for common security vulnerabilities.
        - Report any findings and, if critical, create an issue or fix them.

## 4. Test Execution & CI

- **Unit & Integration Tests:** Will be run on every commit.
- **E2E Tests:** Will be run on every pull request to the `main` or `dev` branch.
- **Performance Tests:** Will be run manually on-demand or as part of a release pipeline to benchmark performance.

---

## 5. Implementation Plan

1.  **Phase 1: Test Plan Creation** (Complete)
    - Create this `12_TESTING_STRATEGY.md` document.

2.  **Phase 2: Enhance Unit & Integration Tests**
    - Create `backend/tests/test_integration_agents.py`.
    - Add more granular unit tests for frontend components and hooks.
    - Add acceptance test for intent classification accuracy.

3.  **Phase 3: Implement Non-Functional Testing**
    - Add `locust` for performance testing.
    - Add `bandit` for security scanning.

4.  **Phase 4: Enhance E2E Tests**
    - Add `admin.spec.ts` for the admin flow.
    - Augment existing E2E tests with more complex scenarios.

5.  **Phase 5: Reporting**
    - Summarize all findings, including test results, performance benchmarks, and security scan outputs.
