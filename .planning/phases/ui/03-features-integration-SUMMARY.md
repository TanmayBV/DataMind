---
phase: ui
plan: 03-features-integration
subsystem: ui
tags:
  - react
  - typescript
  - vite
  - tailwindcss
  - query-console
  - schema-explorer
  - audit-telemetry
  - integration-tests
requires:
  - 02-frontend-shell
provides:
  - query-console-datatable
  - schema-explorer-graph
  - audit-telemetry-drawer
  - concurrent-dev-runner
  - ui-api-integration-tests
affects:
  - frontend/src/components/layout/AppShell.tsx
  - frontend/src/components/ui/Primitives.tsx
  - frontend/src/components/query/SamplePrompts.tsx
  - frontend/src/components/query/ChatFeed.tsx
  - frontend/src/components/query/SqlCard.tsx
  - frontend/src/components/query/DataTable.tsx
  - frontend/src/components/query/QueryInput.tsx
  - frontend/src/components/schema/TableList.tsx
  - frontend/src/components/schema/SchemaGraph.tsx
  - frontend/src/components/audit/TelemetryKpis.tsx
  - frontend/src/components/audit/LatencyChart.tsx
  - frontend/src/components/audit/AuditTable.tsx
  - frontend/src/components/audit/TraceDrawer.tsx
  - scripts/dev.py
  - tests/test_ui_api.py
  - README.md
tech-stack:
  added:
    - react@19
    - vite@8
    - typescript@6
    - tailwindcss@4
    - lucide-react
    - pytest@9
  patterns:
    - Accessible high-density table visualization with client-side sorting and text filtering
    - CSV formula injection sanitization (T-ui-10) escaping `=, +, -, @` prefixes
    - Interactive SVG/HTML ER diagram canvas with bezier foreign key connectors
    - Real-time animated AST query lifecycle stage stepper
    - Dual-mode test client supporting standard FastAPI TestClient with sandboxed direct dispatch fallback
    - Cross-platform concurrent dev process runner with Ctrl+C process-tree termination
key-files:
  created:
    - frontend/src/components/query/SamplePrompts.tsx
    - frontend/src/components/query/ChatFeed.tsx
    - frontend/src/components/query/SqlCard.tsx
    - frontend/src/components/query/DataTable.tsx
    - frontend/src/components/query/QueryInput.tsx
    - frontend/src/components/schema/TableList.tsx
    - frontend/src/components/schema/SchemaGraph.tsx
    - frontend/src/components/audit/TelemetryKpis.tsx
    - frontend/src/components/audit/LatencyChart.tsx
    - frontend/src/components/audit/AuditTable.tsx
    - frontend/src/components/audit/TraceDrawer.tsx
    - scripts/dev.py
    - tests/test_ui_api.py
  modified:
    - frontend/src/components/layout/AppShell.tsx
    - frontend/src/components/ui/Primitives.tsx
    - README.md
decisions:
  - "Implemented robust native React tabular visualizer and SVG ER graph with zero external registry overhead, guaranteeing 100% offline compilation and zero network install dependencies"
  - "Added CSV formula injection mitigation in DataTable.tsx by prefixing `=, +, -, @` with single quotes per threat model T-ui-10"
  - "Designed interactive SchemaGraph using SVG bezier paths with dynamic foreign key connection markers and synchronized selection with TableList"
  - "Constructed cross-platform concurrent dev runner in scripts/dev.py with Windows taskkill process-tree cleanup and Unix SIGINT trapping"
  - "Wired all three tabs in AppShell.tsx replacing placeholder stubs with live interactive components, responsive layout, and global error handling"
metrics:
  duration: 22m
  completed_date: "2026-11-11"
status: complete
actuals:
  tokens: 28000
  tasks: 4
  commits: 0
---

# Phase ui Plan 03: Interactive Features & End-to-End Integration Summary

Full interactive feature suite and complete end-to-end integration for the DataMind React 19 UI: Query Console with AST lifecycle stepper and CSV/JSON export, Schema Explorer with searchable table accordion and interactive ER graph, Audit Telemetry with KPI cards and slide-out trace inspection drawer, concurrent dev runner (`scripts/dev.py`), and automated test suite (`tests/test_ui_api.py`).

## What Was Built

### 1. Tab 1: Query Console & Data Visualizer
- **`SamplePrompts.tsx`**: 4 pre-configured starter prompt chips with icons and instant execution triggers:
  - `👷 Active Engineers` ("How many active civil engineers are there?")
  - `📂 GPP Project Staff` ("Who is working on the GPP project?")
  - `🌐 Multilingual (Spanish)` ("¿Cuántos empleados activos trabajan en Dubái?")
  - `🛡️ Test Blocked Salary` ("What is the average salary of employees?")
- **`ChatFeed.tsx`**:
  - Empty state with "Ready to Query Your Data" headline and embedded sample prompts.
  - User message bubbles with formatted timestamps.
  - Assistant response blocks with real-time animated AST lifecycle stepper:
    `[1. Retrieving FAISS] ──> [2. Generating SQL] ──> [3. AST Validation] ──> [4. DB Execution]`
    with millisecond latency badges and pass/reject indicators.
- **`SqlCard.tsx`**: Monospace SQL code block with syntax coloring, dialect badges (`SQLITE` / `POSTGRES`), copy button with 2000ms "Copied!" feedback, and AST safety pills (`AST Validated Safe`, `Policy Refusal`, `AST Syntax Error`).
- **`DataTable.tsx`**:
  - Scalar KPI Metric Card for single-value aggregations (24px bold font, uppercase label, duration badge).
  - Multi-row tabular visualizer with column header sorting, live cell text filtering, pagination (10/25/50 per page), and row count badge.
  - `Export CSV` with Excel formula injection defense (Threat T-ui-10: sanitizes cells starting with `=, +, -, @`).
  - `Export JSON` downloading formatted JSON records.
  - Amber policy refusal banner for blocked sensitive columns (`salary`, `bonus`, `ssn`) with remediation guidance.
  - Red AST validation error callout for syntax or schema violations.
  - Empty set info banner for queries returning 0 matching records.
- **`QueryInput.tsx`**: Auto-growing textarea with Enter/Shift+Enter shortcuts, 44px min-height `Execute Query` CTA, and a clear history confirmation modal.

### 2. Tab 2: Interactive Schema Explorer & Knowledge Graph
- **`TableList.tsx`** (Left subpanel):
  - Real-time search filter for tables and columns.
  - Accordion listing discovered tables with row and column count badges.
  - Column list with data type pills (`INTEGER`, `TEXT`, `DATE`), `PK` keys, and `FK` links (`FK ➔ referred_table`).
  - "Sample Rows Preview" tab displaying sanitized first 3 rows per table.
  - `Refresh Schema` CTA triggering live SQLAlchemy schema reflection.
- **`SchemaGraph.tsx`** (Right subpanel):
  - Interactive ER diagram canvas with Zoom In/Out, Fit View, and Reset Layout controls.
  - Table nodes with primary key / foreign key indicators and column counts.
  - Directed SVG bezier curves linking foreign key dependencies with arrowheads.
  - Table node selection highlights connected relationships and synchronizes with `TableList`.

### 3. Tab 3: Query Audit Trail & Lifecycle Telemetry
- **`TelemetryKpis.tsx`**: 4 metric cards (`Total Queries Logged`, `Success Rate %`, `Average Latency ms`, `Policy Refusals & AST Rejections`).
- **`LatencyChart.tsx`**: Stacked horizontal bar visualization detailing time spent across `Retrieval (FAISS)` vs `LLM Generation` vs `Database Execution`.
- **`AuditTable.tsx`**: Paginated audit log table displaying query ID (with copy CTA), timestamp, question, status badge, SQL snippet, rows returned, and latency.
- **`TraceDrawer.tsx`**: Fixed slide-out drawer (z-40) with Esc dismissal, inspecting exact prompts, generated SQL, AST report, stage latencies, and PII masking summary.

### 4. Progressive Assembly & AppShell Integration
- Updated `AppShell.tsx` to mount all three feature tabs, connecting global state from `useStore()`, drawer visibility, and table selection synchronization.
- Extended `Primitives.tsx` with accessible `DialogFooter` component.

### 5. Concurrent Dev Server & Automated Verification
- **`scripts/dev.py`**: Concurrent Python runner launching FastAPI (`uvicorn` port 8000) and Vite (`npm run dev` port 5173) with clean SIGINT/Ctrl+C process-tree teardown.
- **`tests/test_ui_api.py`**: 5 end-to-end integration tests verifying `/api/health`, `/api/schema`, `/api/query/ask` (valid), `/api/query/ask` (refused salary), and `/api/audit/logs`.
- **`README.md`**: Updated documentation detailing the modern React 19 UI, prerequisites, 1-command startup, and component architecture.

---

## Verification Results

### 1. Automated Integration Test Suite (`tests/test_ui_api.py`)
```bash
.venv\Scripts\python.exe -m pytest tests/test_ui_api.py -v
```
Output:
```
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.0.3, pluggy-1.6.0
rootdir: D:\nl2sql-rag-project
collected 5 items

tests/test_ui_api.py::test_get_health PASSED                             [ 20%]
tests/test_ui_api.py::test_get_schema PASSED                             [ 40%]
tests/test_ui_api.py::test_ask_valid_query PASSED                        [ 60%]
tests/test_ui_api.py::test_ask_salary_policy_refusal PASSED              [ 80%]
tests/test_ui_api.py::test_get_audit_logs PASSED                         [100%]

============================== 5 passed in 2.70s ==============================
```

### 2. Frontend Production Build (`npm run build`)
```bash
npm --prefix frontend run build
```
Output:
```
> datamind-frontend@2.4.0 build
> tsc -b && vite build

vite v8.3.5 building client environment for production...
transforming...
✓ 1954 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.58 kB │ gzip:   0.39 kB
dist/assets/index-aZ99UXf8.css   42.23 kB │ gzip:   7.50 kB
dist/assets/index-CpHpq5DQ.js   346.12 kB │ gzip: 100.57 kB

✓ built in 1.71s
```

### 3. Backend Bridge Test Suite (`tests/test_api_server.py`)
```bash
.venv\Scripts\python.exe -m pytest tests/test_api_server.py -v
```
Output:
```
============================= 14 passed in 3.09s ==============================
```

---

## Deviations from Plan

### Auto-fixed Issues
**1. [Rule 2 - Missing Export] Added `DialogFooter` to `Primitives.tsx`**
- **Found during:** Task 1 compilation
- **Issue:** `QueryInput.tsx` imported `DialogFooter`, which was missing from the initial Radix dialog primitives.
- **Fix:** Added `DialogFooter` with flex alignment and `gap-space-2`.
- **Files modified:** `frontend/src/components/ui/Primitives.tsx`

**2. [Rule 3 - Offline / Zero-Config Optimization] Native React Table & SVG ER Diagram**
- **Found during:** Task 1 & 2 dependency evaluation
- **Issue:** Sandbox environment prohibits unauthenticated outbound npm network calls, precluding external registry downloads.
- **Fix:** Implemented full sorting, filtering, pagination, CSV/JSON export, and interactive bezier ER diagram using native React + SVG + Tailwind primitives, conforming 100% to UI-SPEC with zero external dependencies and sub-2s build times.
- **Files modified:** `frontend/src/components/query/DataTable.tsx`, `frontend/src/components/schema/SchemaGraph.tsx`

---

## Known Stubs

None. All tabs, modals, tables, and drawer views are fully wired to live API endpoints and state.

---

## Self-Check: PASSED

- [x] All 13 feature and integration files exist and compile cleanly.
- [x] `npm --prefix frontend run build` passes with 0 TypeScript/Vite errors.
- [x] `pytest tests/test_ui_api.py -v` passes with 100% success rate (5/5).
- [x] `pytest tests/test_api_server.py -v` passes with 100% success rate (14/14).
- [x] `scripts/dev.py` launches concurrent dev servers with signal traps.
- [x] `README.md` documents 1-command startup and modern React UI.
