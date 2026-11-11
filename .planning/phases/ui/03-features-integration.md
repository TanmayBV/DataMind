---
phase: ui
plan: 03-features-integration
type: execute
wave: 3
depends_on:
  - 02-frontend-shell
files_modified:
  - frontend/src/components/layout/AppShell.tsx
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
autonomous: true
requirements:
  - UI-04-QUERY-CONSOLE-DATATABLE
  - UI-05-SCHEMA-AUDIT-TELEMETRY
  - UI-06-INTEGRATION-VERIFY
estimate:
  tokens: 28000
  raw_tokens: 18000
  tasks: 4
  confidence: high
must_haves:
  truths:
    - "AppShell.tsx imports and renders real Query Console, Schema Explorer, and Audit Telemetry components, replacing previous placeholder stubs"
    - "Query Console renders prompt starters, animated lifecycle stage stepper, SQL card with AST status pill, and TanStack DataTable with sorting, pagination, and CSV/JSON export"
    - "PII refusal callout displays amber warning banner and remediation guidance when sensitive columns are requested"
    - "Schema Explorer renders searchable table accordion and interactive ReactFlow ER diagram with foreign key edges"
    - "Audit Telemetry renders KPI metric cards, latency breakdown chart, paginated audit log table, and slide-out trace inspection drawer"
    - "scripts/dev.py concurrently launches FastAPI backend and Vite frontend with clean Ctrl+C teardown"
    - "Automated integration test suite tests/test_ui_api.py passes with 100% success rate"
  artifacts:
    - "frontend/src/components/layout/AppShell.tsx"
    - "frontend/src/components/query/DataTable.tsx"
    - "frontend/src/components/schema/SchemaGraph.tsx"
    - "frontend/src/components/audit/AuditTable.tsx"
    - "scripts/dev.py"
    - "tests/test_ui_api.py"
    - "README.md"
  key_links:
    - "AppShell.tsx wires real QueryConsole, SchemaExplorer, and AuditTelemetry components into Radix Tabs"
    - "DataTable.tsx uses TanStack Table to display result rows with sorting, filtering, and export"
    - "SchemaGraph.tsx uses ReactFlow to display table nodes and foreign key edges"
    - "scripts/dev.py coordinates subprocesses for uvicorn and vite dev servers"
---

<objective>
Implement the full interactive features and complete end-to-end integration for the DataMind UI:
- Query Console with starter prompts, animated AST lifecycle stepper, SQL card, TanStack DataTable (sorting, filtering, pagination, CSV/JSON export), and policy refusal callouts
- Schema Explorer with searchable table accordion and interactive ReactFlow entity relationship graph
- Audit Telemetry with KPI cards, latency breakdown chart, audit log table, and slide-out trace drawer
- Progressive assembly: Update `AppShell.tsx` to replace placeholder tab stubs with real feature components
- Concurrent dev server orchestrator (`scripts/dev.py`), automated integration test suite (`tests/test_ui_api.py`), and documentation update (`README.md`)

Output:
- All feature components implemented in `frontend/src/components/`
- `AppShell.tsx` wired with real tab components
- `scripts/dev.py` and `tests/test_ui_api.py` operational and verified
</objective>

<execution_context>
@~/.gemini/antigravity/gsd-core/workflows/execute-plan.md
@~/.gemini/antigravity/gsd-core/templates/summary.md
</execution_context>

<context>
@d:/nl2sql-rag-project/UI-SPEC.md
@.planning/phases/ui/01-backend-bridge.md
@.planning/phases/ui/02-frontend-shell.md
@d:/nl2sql-rag-project/query_engine/api_server.py
@d:/nl2sql-rag-project/frontend/src/App.tsx
@d:/nl2sql-rag-project/frontend/src/components/layout/AppShell.tsx
</context>

<tasks>

<task type="auto">
  <name>Task 1: Query Console, AST Lifecycle Stepper & TanStack DataTable</name>
  <files>frontend/src/components/query/SamplePrompts.tsx, frontend/src/components/query/ChatFeed.tsx, frontend/src/components/query/SqlCard.tsx, frontend/src/components/query/DataTable.tsx, frontend/src/components/query/QueryInput.tsx</files>
  <action>
1. Build `SamplePrompts.tsx`:
   - Render 4 starter chips per UI-SPEC Section 9.2:
     - `👷 Active Engineers` ("How many active civil engineers are there?")
     - `📂 GPP Project Staff` ("Who is working on the GPP project?")
     - `🌐 Multilingual (Spanish)` ("¿Cuántos empleados activos trabajan en Dubái?")
     - `🛡️ Test Blocked Salary` ("What is the average salary of employees?")
   - Clicking any chip populates query input and triggers execution.
2. Build `ChatFeed.tsx`:
   - Empty state when no queries: "Ready to Query Your Data" headline with explanatory copy.
   - User message bubble with natural language question and formatted timestamp.
   - Assistant response card:
     - Lifecycle Stage Stepper: Animated progress indicators for `[1. Retrieving FAISS] ──> [2. Generating SQL] ──> [3. AST Validation] ──> [4. DB Execution]` with latency millisecond badges.
     - `SqlCard.tsx`:
       - Dialect badge (`POSTGRES` / `SQLITE`), `Copy SQL` CTA (with 2000ms "Copied!" feedback), format SQL toggle.
       - Monospace code block with syntax coloring.
       - AST Status Pill: `AST Validated Safe` (emerald), `Policy Refusal` (amber), `AST Syntax Error` (red).
     - Response Visualizations:
       - Scalar KPI Card (for COUNT/SUM single value): 24px bold font, uppercase label, duration badge.
       - `DataTable.tsx` powered by TanStack Table: column header sorting, cell text filtering, pagination (10/25/50), row count, `Export CSV` (downloads .csv), and `Export JSON` (downloads .json).
       - Policy Refusal Callout: Amber warning shield, headline `Blocked by Business Safety Policy`, and remediation guidance per Section 9.3.
       - AST Validation Rejection: Red error callout detailing rejected AST clauses.
       - Empty set: Informational callout "No Records Found".
3. Build `QueryInput.tsx`:
   - Fixed bottom container with auto-growing textarea (14px font, accent focus ring).
   - Enter to submit, Shift+Enter for newline.
   - CTA button: `Execute Query` with `CornerDownLeft` icon (`min-h-[44px]`).
   - Clear history button triggering confirmation modal.
  </action>
  <verify>
    <automated>npm --prefix frontend run build</automated>
    <fails_when>TypeScript compilation failure in query components or TanStack table typing errors</fails_when>
  </verify>
  <done>
    Query Console components render starter prompts, lifecycle stepper, SQL card with AST badges, TanStack DataTable with pagination/sorting/export, and refusal callouts.
  </done>
</task>

<task type="auto">
  <name>Task 2: Schema Explorer (ReactFlow ER Graph) & Audit Telemetry (Trace Drawer)</name>
  <files>frontend/src/components/schema/TableList.tsx, frontend/src/components/schema/SchemaGraph.tsx, frontend/src/components/audit/TelemetryKpis.tsx, frontend/src/components/audit/LatencyChart.tsx, frontend/src/components/audit/AuditTable.tsx, frontend/src/components/audit/TraceDrawer.tsx</files>
  <action>
1. Build Tab 2: Schema Explorer & Entity Graph:
   - Split layout: Left subpanel (35% width), Right subpanel (65% width).
   - `TableList.tsx` (Left subpanel):
     - Search filter input ("Filter tables or columns...").
     - Accordion of discovered tables with column count and row count badges.
     - Expanded table view showing column list, data type pills (`INTEGER`, `TEXT`, `DATE`), `PK` badges, and `FK` pointers (`FK ➔ departments.department_id`).
     - "Sample Rows Preview" tab: renders first 3 sanitized rows in a compact table.
     - `Refresh Schema` CTA button with loading state.
   - `SchemaGraph.tsx` (Right subpanel):
     - Interactive ER diagram built using `@xyflow/react`.
     - Custom Table Node displaying table name in colored header, column items with type pills, and PK/FK markers.
     - Directed bezier edges connecting foreign key relationships between tables.
     - Controls: Zoom In/Out, Fit View, Reset Layout.
     - Clicking a table node highlights connected edges and synchronizes selection with `TableList.tsx`.
2. Build Tab 3: Query Audit Trail & Lifecycle Telemetry:
   - `TelemetryKpis.tsx`: 4 metric cards (`Total Queries Logged`, `Success Rate %`, `Average Latency ms`, `Policy Refusals & AST Rejections`).
   - `LatencyChart.tsx`: Horizontal stacked bar visualization showing average latency breakdown: `Retrieval (FAISS)` vs `LLM Generation` vs `Database Execution`.
   - `AuditTable.tsx`: TanStack Table displaying audit records from `GET /api/audit/logs` with columns: Query ID (with copy CTA), Timestamp, Question, Status badge, SQL snippet, Rows Returned, Total Latency, and `View Trace` CTA.
   - `TraceDrawer.tsx` (Slide-out drawer, z-40):
     - Full trace inspection: exact prompt sent to LLM, generated SQL & AST report, stage latencies breakdown, auto-masked PII summary, and `Dismiss Alert` CTA to close.
  </action>
  <verify>
    <automated>npm --prefix frontend run build</automated>
    <fails_when>ReactFlow, chart rendering, or drawer component build errors</fails_when>
  </verify>
  <done>
    Schema Explorer with ReactFlow and Audit Telemetry with Trace Drawer components build cleanly.
  </done>
</task>

<task type="auto">
  <name>Task 3: Progressive Tab Wiring into AppShell</name>
  <files>frontend/src/components/layout/AppShell.tsx</files>
  <action>
1. Update `frontend/src/components/layout/AppShell.tsx` to replace the placeholder stub tab panels created in Plan 02 with the real feature components:
   - Tab 1 ("Query Console"): Render `SamplePrompts`, `ChatFeed`, and `QueryInput`.
   - Tab 2 ("Schema Explorer"): Render `TableList` and `SchemaGraph` split pane.
   - Tab 3 ("Audit Telemetry"): Render `TelemetryKpis`, `LatencyChart`, `AuditTable`, and `TraceDrawer`.
2. Connect tab switching, drawer state, and synchronize active table selection between Schema Explorer components.
3. Ensure responsive layout adjustments for desktop and mobile screen widths.
4. Verify that running `npm run build` succeeds without unresolved imports or type errors.
  </action>
  <verify>
    <automated>npm --prefix frontend run build</automated>
    <fails_when>Unresolved component imports, broken props, or type mismatches in AppShell</fails_when>
  </verify>
  <done>
    `AppShell.tsx` wires all full feature components into tabs, replacing placeholder stubs; `npm run build` succeeds cleanly.
  </done>
</task>

<task type="auto">
  <name>Task 4: Concurrent Dev Launcher, Automated E2E Verification & Documentation</name>
  <files>scripts/dev.py, tests/test_ui_api.py, README.md</files>
  <action>
1. Create `scripts/dev.py` concurrent launcher:
   - Starts FastAPI backend (`uvicorn query_engine.api_server:app --port 8000 --reload`) using Python subprocess.
   - Starts Vite frontend (`npm --prefix frontend run dev -- --port 5173`) using Node subprocess.
   - Handles clean SIGINT / Ctrl+C teardown of both processes.
   - Logs welcoming instructions with port assignments (`Backend: http://localhost:8000`, `Frontend: http://localhost:5173`).
2. Implement comprehensive automated test suite `tests/test_ui_api.py`:
   - Test 1: `GET /api/health` asserts healthy status and default SQLite dialect.
   - Test 2: `GET /api/schema` verifies table metadata, column types, and sample rows for `employees_clean`, `departments`, `projects`, `project_assignments`.
   - Test 3: `POST /api/query/ask` with "How many active civil engineers are there?" verifies `status="ready"`, `is_valid=True`, and non-empty result rows.
   - Test 4: `POST /api/query/ask` with "What is the average salary?" verifies `status="refused"`, `is_valid=False`, and PII refusal message.
   - Test 5: `GET /api/audit/logs` asserts query audit entries are correctly written and retrieved.
3. Update `README.md` to document the new modern React UI:
   - Prerequisites (Python 3.10+, Node.js 18+)
   - 1-command startup: `python scripts/dev.py`
   - UI Architecture summary, design token compliance, and feature showcase.
  </action>
  <verify>
    <automated>.venv\Scripts\python.exe -m pytest tests/test_ui_api.py -v && npm --prefix frontend run build</automated>
    <fails_when>Integration tests fail or frontend build fails</fails_when>
  </verify>
  <done>
    Unified dev runner starts both tiers cleanly, automated API integration tests pass with 100% success rate, and frontend build passes cleanly.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Client Browser -> TanStack Table Export | User requests CSV/JSON file export generated from database result rows. |
| Client Browser -> ReactFlow Canvas | Database column and table names rendered into SVG/DOM canvas nodes. |
| Subprocess Dev Runner -> OS Shell | `scripts/dev.py` manages uvicorn and vite processes via OS signals. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-ui-10 | Tampering / Code Injection | `DataTable.tsx` CSV Export | medium | mitigate | Sanitize CSV export values: prefix cells starting with `=, +, -, @` with a single quote to prevent CSV formula injection in Microsoft Excel. |
| T-ui-11 | Denial of Service | `DataTable.tsx` & `SchemaGraph.tsx` | medium | mitigate | Virtualize or paginate large tables (max 50 rows per page); render schema graph with layout node culling for high table counts. |
| T-ui-12 | Denial of Service | `scripts/dev.py` Subprocess Lifecycle | low | mitigate | Subprocess manager traps SIGINT, SIGTERM, and unexpected exits to ensure child processes on port 8000 and 5173 are killed cleanly. |
| T-ui-SC | Tampering | npm dependencies | high | mitigate | Strict package legitimacy audit: Only official `@xyflow/react` and `@tanstack/react-table` packages used. |
</threat_model>

<verification>
.venv\Scripts\python.exe -m pytest tests/test_ui_api.py -v && npm --prefix frontend run build
</verification>

<success_criteria>
Query Console, Schema Explorer, and Audit Telemetry features fully operational in AppShell tabs. Concurrent launcher scripts/dev.py operational. All integration tests pass with 0 errors.
</success_criteria>

<output>
Create `.planning/phases/ui/03-features-integration-SUMMARY.md` when execution completes.
</output>
