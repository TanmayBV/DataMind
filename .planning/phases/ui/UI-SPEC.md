---
status: approved
phase: ui
title: DataMind NL2SQL Data Governance Engine UI Specification
date: 2026-11-11
reviewed_at: 2026-11-11T14:13:00Z
tool: manual (React + Vite + Tailwind CSS + Radix UI Primitives + Lucide Icons)
---

# UI Design Contract: DataMind Universal NL2SQL Data Governance Engine

## 1. Executive Summary & Scope

This specification defines the visual and interaction contract for replacing and augmenting the Streamlit interface (`query_engine/app.py`) with a modern, high-performance, interactive Single Page Application (SPA) built with **React 18/19**, **Vite**, **Tailwind CSS**, **Radix UI / shadcn-compatible primitives**, and **Lucide React**.

DataMind is a RAG-driven natural language query engine for enterprise databases. It incorporates dynamic schema reflection, multi-dialect SQL generation (PostgreSQL, SQLite, MySQL), sqlglot AST-level safety validation, sensitive column PII masking/refusal, and fine-grained lifecycle telemetry. The UI must transition DataMind from a prototype feel into an enterprise-grade data cockpit.

---

## 2. Spacing & Layout Tokens

### 2.1 8-Point Scale
All layout margins, paddings, gaps, and structural dimensions MUST adhere strictly to the 8-point grid scale standard set (4, 8, 16, 24, 32, 48, 64 px). Arbitrary pixel values and off-grid values (such as 12px) are forbidden.

| Token | Pixels | Tailwind Class | Primary Application |
|---|---|---|---|
| `space-1` | 4px | `p-1`, `gap-1`, `m-1` | Icon padding, tight badge margins, inline tags |
| `space-2` | 8px | `p-2`, `gap-2`, `m-2` | Button inner padding (compact), chip spacing, table cell vertical padding, form input vertical padding |
| `space-4` | 16px | `p-4`, `gap-4`, `m-4` | Standard card padding, modal content gap, toolbar padding, card inner margins |
| `space-6` | 24px | `p-6`, `gap-6`, `m-6` | Section headers, panel padding, grid column gaps |
| `space-8` | 32px | `p-8`, `gap-8`, `m-8` | Main canvas margins, empty-state containers, dashboard block spacing |
| `space-12` | 48px | `p-12`, `gap-12`, `m-12` | Major section separations, hero banners |
| `space-16` | 64px | `p-16`, `gap-16`, `m-16` | Top-level layout framing, full-page onboarding empty states |

### 2.2 Layout Sizing & Touch Targets
- **Minimum Interactive Touch Target:** `44px` height and `44px` minimum width for all clickable icon buttons, dropdown triggers, and mobile controls (`min-h-[44px] min-w-[44px]`).
- **Sidebar Width:** Desktop collapsed: `64px` (`w-16`), Desktop expanded: `320px` (`w-80`).
- **Header/Topbar Height:** `56px` (`h-14`), fixed sticky at top.
- **Max Content Width:** Fluid layout with max-width containment for readable content: `max-w-7xl` (`1280px`) centered on widescreen monitors (>1920px).
- **Z-Index Layering Scale:**
  - `z-base`: `0`
  - `z-elevated`: `10` (sticky headers, table headers)
  - `z-dropdown`: `30` (select menus, tooltips, popovers)
  - `z-drawer`: `40` (slide-out inspector, telemetry details)
  - `z-modal`: `50` (connection modal, confirmation dialogs)
  - `z-toast`: `60` (ephemeral notification toasts)

---

## 3. Typography Hierarchy

To maintain visual rigor and avoid typographical noise, the interface strictly limits typography to **4 font sizes** and **2 font weights**.

- **Primary Font Family:** Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
- **Monospace Font Family:** "JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, monospace (for SQL syntax, column names, table names, API payloads, AST trees)

### 3.1 Size & Weight Contract

| Level | Size | Weight | Line Height | Tracking | Tailwind Utility | Usage |
|---|---|---|---|---|---|---|
| **Title / Heading 1** | `24px` (1.5rem) | `600` (SemiBold) | `1.2` (28.8px) | `-0.02em` | `text-2xl font-semibold leading-tight tracking-tight` | Page titles, major modal headers, scalar metric KPI values |
| **Subheading / Heading 2** | `18px` (1.125rem) | `600` (SemiBold) | `1.2` (21.6px) | `-0.01em` | `text-lg font-semibold leading-tight` | Section titles, panel headers, card headers, table titles |
| **Body / Standard UI** | `14px` (0.875rem) | `400` (Regular) | `1.5` (21px) | `normal` | `text-sm font-normal leading-relaxed` | Chat messages, input controls, table cell text, descriptions |
| **Body SemiBold** | `14px` (0.875rem) | `600` (SemiBold) | `1.5` (21px) | `normal` | `text-sm font-semibold leading-relaxed` | Button labels, table column headers, active tabs, strong emphasis |
| **Caption / Meta** | `12px` (0.75rem) | `400` (Regular) | `1.5` (18px) | `+0.01em` | `text-xs font-normal leading-normal` | Timestamps, status subtitles, badge text, helper tooltips, row counts |
| **Caption SemiBold** | `12px` (0.75rem) | `600` (SemiBold) | `1.5` (18px) | `+0.01em` | `text-xs font-semibold leading-normal` | Status pill badges (`AST VALID`, `REFUSED`), SQL dialect badges |

**Strict Enforcement:** No font sizes of 10px, 11px, 13px, 15px, 20px, 22px, 32px, etc. No font weights of 100, 200, 300, 500, 700, 800, 900.

---

## 4. Color System & 60/30/10 Token Distribution

The interface provides high-contrast, accessibility-tested themes for both **Dark Mode** (default enterprise cockpit mode) and **Light Mode**. The layout strictly follows the **60/30/10 rule** to ensure visual hierarchy without cognitive fatigue.

### 4.1 Distribution Split

- **60% Dominant Surface:** Canvas, root application background, scrollable viewports.
- **30% Secondary Structure:** Sidebars, navigation bars, elevated cards, table frames, input borders, dividers.
- **10% Accent (Strictly Reserved):**
  - Primary Action CTAs (`Execute Query`, `Connect Database`)
  - Active Tab indicator & Active Nav Pill
  - Focused form input rings (2px ring)
  - Interactive Schema Graph node selection
  - Selected data table row highlighting

### 4.2 Color Palette Tokens

```
Dark Theme Tokens (Default)
├── Surface (60%):
│   ├── bg-app:               #0B0F19 (Slate/Zinc ultra-deep 950)
│   └── bg-canvas:            #0E1424 (Canvas depth layer)
├── Secondary Structure (30%):
│   ├── bg-card:              #131B2E (Elevated card & panel surface)
│   ├── bg-sidebar:           #0F172A (Sidebar & topbar slate 900)
│   ├── bg-input:             #1E293B (Form field backplate)
│   ├── border-subtle:        #1E293B (1px dividing borders)
│   ├── border-prominent:     #334155 (Card borders, table borders)
│   ├── text-primary:         #F8FAFC (Slate 50 - High contrast text)
│   ├── text-secondary:       #94A3B8 (Slate 400 - Captions, icons)
│   └── text-muted:           #64748B (Slate 500 - Disabled, placeholders)
└── Accent & Semantics (10%):
    ├── accent-primary:       #3B82F6 (Blue 500 - Interactive CTAs, Active pills)
    ├── accent-hover:         #2563EB (Blue 600 - Hover state)
    ├── accent-subtle:        rgba(59, 130, 246, 0.12) (Selection highlight)
    ├── status-success:       #10B981 (Emerald 500 - AST Valid, Connected)
    ├── status-success-bg:    rgba(16, 185, 129, 0.12)
    ├── status-error:         #EF4444 (Red 500 - AST Syntax Rejection, DB Error)
    ├── status-error-bg:      rgba(239, 68, 68, 0.12)
    ├── destructive:          #EF4444 (Red 500 - Destructive actions e.g. Clear History)
    ├── destructive-hover:    #DC2626 (Red 600 - Destructive hover state)
    ├── destructive-bg:       rgba(239, 68, 68, 0.12)
    ├── status-warning:       #F59E0B (Amber 500 - Policy Refusal, PII Restricted)
    ├── status-warning-bg:    rgba(245, 158, 11, 0.12)
    └── status-info:          #38BDF8 (Sky 400 - FAISS Retrieval, Info chips)
```

```
Light Theme Tokens
├── Surface (60%):
│   ├── bg-app:               #F8FAFC (Slate 50 clean light background)
│   └── bg-canvas:            #F1F5F9 (Slate 100 secondary backplate)
├── Secondary Structure (30%):
│   ├── bg-card:              #FFFFFF (Pure white elevated cards)
│   ├── bg-sidebar:           #FFFFFF (Crisp white sidebar & header)
│   ├── bg-input:             #F8FAFC (Light slate input background)
│   ├── border-subtle:        #E2E8F0 (Slate 200 light borders)
│   ├── border-prominent:     #CBD5E1 (Slate 300 divider lines)
│   ├── text-primary:         #0F172A (Slate 900 - High contrast text)
│   ├── text-secondary:       #475569 (Slate 600 - Labels, icons)
│   └── text-muted:           #94A3B8 (Slate 400 - Placeholders)
└── Accent & Semantics (10%):
    ├── accent-primary:       #2563EB (Blue 600 - Primary actions)
    ├── accent-hover:         #1D4ED8 (Blue 700 - Hover state)
    ├── accent-subtle:        rgba(37, 99, 235, 0.08)
    ├── status-success:       #059669 (Emerald 600)
    ├── status-success-bg:    rgba(5, 150, 105, 0.10)
    ├── status-error:         #DC2626 (Red 600)
    ├── status-error-bg:      rgba(220, 38, 38, 0.10)
    ├── destructive:          #DC2626 (Red 600 - Destructive actions)
    ├── destructive-hover:    #B91C1C (Red 700 - Destructive hover state)
    ├── destructive-bg:       rgba(220, 38, 38, 0.10)
    ├── status-warning:       #D97706 (Amber 600)
    ├── status-warning-bg:    rgba(217, 119, 6, 0.10)
    └── status-info:          #0284C7 (Sky 600)
```

---

## 5. Component Inventory & Provenance

Could not enumerate: Project frontend not yet initialized (specifying greenfield React 18 + Vite + Tailwind + Radix/Lucide architecture; inventory is non-exhaustive and establishes structural contract).

Below is the prescribed component inventory to be initialized via `@radix-ui` / `shadcn` and custom primitives:

| Component | Library / Primitive | Primary Role | Interactive States |
|---|---|---|---|
| `Button` | `@radix-ui/react-slot` + Tailwind | Primary CTAs, icon actions, chips | Default, Hover, Active, Disabled, Loading (spinner) |
| `Dialog` / `Modal` | `@radix-ui/react-dialog` | DB Connection dialog, Policy rules editor, Query detail | Open, Closed, Backdrop Blur, Esc to Dismiss |
| `DropdownMenu` | `@radix-ui/react-dropdown-menu` | Export options (CSV, JSON, Markdown), Table actions | Closed, Open, Item Hover, Submenu |
| `Tabs` | `@radix-ui/react-tabs` | Main view navigation (Query Console, Schema, Audit) | Active, Inactive, Focus-visible |
| `Tooltip` | `@radix-ui/react-tooltip` | Metric definitions, AST explanations, PII notices | Hover (200ms delay), Touch hold, Hidden |
| `DataTable` | TanStack Table v8 + Virtualizer | Query results viewer & Audit trail viewer | Header sort, Column resize, Paginated, Selected row |
| `SchemaGraph` | ReactFlow / `@xyflow/react` | Interactive ER diagram of database tables and FKs | Zoom, Pan, Node Click, Edge Highlight, Minimap |
| `CodeEditor` / `SQLBlock`| PrismJS / `@monaco-editor` or `shiki` | SQL generation display, syntax highlighting | Syntax tokens, Copy button, Formatted view |
| `Badge` | Custom Tailwind Pill | AST Valid, Dialect (PG/SQLite), Policy Refusal | Success, Warning, Error, Info, Neutral |
| `Toast` | `@radix-ui/react-toast` or `sonner` | Connection success, copy to clipboard, save rules | Enter animation, Swipe to dismiss, Auto-hide 4s |
| `Card` | Custom Tailwind Container | Metric KPI cards, Sample prompt chips, Table meta | Default, Hover-lift, Selected outline |
| `Input` / `Textarea` | Native + Tailwind ring styling | Chat prompt input, Custom URI, Policy rules editor | Focus-visible (accent ring 2px), Error state, Disabled |

### 5.1 Registry Safety
No third-party component registries (such as Aceternity, 21st.dev, or external copy-paste registries) are permitted. All UI components are strictly limited to official Radix UI primitives (`@radix-ui/*`), standard shadcn/ui base patterns, Lucide React icons, and internal custom components. No third-party registry network calls or untrusted component bundles may be introduced.

---

## 6. Component Hierarchy & Page Layout

The application utilizes a multi-panel layout designed for data density, rapid context-switching, and operational clarity.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🧠 DataMind Topbar [Active DB: Demo HR ERP] [Dialect: POSTGRES] [Theme] [Docs]│
├───────────────────┬─────────────────────────────────────────────────────────┤
│                   │ Tabs: [💬 Query Console] [📊 Schema Explorer] [📋 Audit]│
│ 🔌 Connection     ├─────────────────────────────────────────────────────────┤
│ - Demo HR (Active)│                                                         │
│ - Upload SQLite   │ Main Active Workspace View                              │
│ - Custom URI      │                                                         │
│                   │                                                         │
│ 🛡️ Governance     │                                                         │
│ - Blocked: 8 cols │                                                         │
│ - Rules: Custom   │                                                         │
│                   │                                                         │
│ ⚙️ Controls        │                                                         │
│ - Few-shot: ON    │                                                         │
│ - AST Details: ON │                                                         │
└───────────────────┴─────────────────────────────────────────────────────────┘
```

### 6.1 Topbar Header (`h-14`, Sticky)
- **Left:** Brand logo icon (`BrainCircuit` or `DatabaseZap`), product title: `DataMind`, version badge `v2.4`.
- **Center:** Connection indicator pill:
  - Green pulsing dot + `Connected: Local HR ERP (SQLite Demo)`
  - Dialect tag: `SQLITE` or `POSTGRESQL` or `MYSQL`
  - Discovered tables count: `4 tables`
- **Right:**
  - `ThemeToggle` (Sun/Moon icon button, min 44x44px target)
  - `HealthStatus` (Backend API latency badge e.g. `24ms`)
  - `GitHubLink` & `DocsButton`

### 6.2 Left Navigation / Governance Sidebar (`w-80`, Collapsible)
- **Connection Switcher Section:**
  - Segmented control or radio card group:
    1. **Demo HR ERP (1-Click):** Instant preloaded enterprise database.
    2. **Upload SQLite (.db / .sqlite):** Drag-and-drop file upload target with file size indicator.
    3. **Custom Database URI:** Input with instant syntax validation (`postgresql://`, `mysql://`, `sqlite:///`) and "Test Connection" button.
- **Schema & Policy Quick Status:**
  - Total tables counter and "Refresh Schema Cache" icon button (`RotateCw`).
  - Sensitive columns tag summary (e.g. `8 blocked columns active: salary, ssn, ...`).
  - "Configure Governance" button opens Policy & Rules modal.
- **Query Pipeline Options:**
  - Few-shot semantic retrieval toggle (FAISS): switch control with explanatory tooltip. (Automatically disabled with warning tag when connected to custom non-HR schema).
  - "Show SQL & AST Telemetry" toggle.

### 6.3 Main Workspace: Tab 1 — Query Console & Data Visualizer
- **Sample Prompt Chips (Quick Starters):**
  - Row of 4 pre-configured chips for immediate evaluation:
    - `👷 Active Engineers` ("How many active civil engineers are there?")
    - `📂 GPP Project Staff` ("Who is working on the GPP project?")
    - `🌐 Multilingual (Spanish)` ("¿Cuántos empleados activos trabajan en Dubái?")
    - `🛡️ Test Blocked Salary` ("What is the average salary of employees?")
- **Chat Interaction Stream (Reverse chronological or bottom-anchored):**
  - **User Message Bubble:** Clear, right-aligned or branded bubble displaying natural language query and submission timestamp.
  - **Assistant Response Block:**
    - **Progress / Lifecycle Bar:** Real-time stage stepper:
      `[1. Retrieving FAISS] ──> [2. Generating SQL] ──> [3. AST Validation] ──> [4. DB Execution]`
    - **Generated SQL Card (if toggle active):**
      - Header: Dialect badge (`POSTGRES`), copy SQL button (`Copy SQL`), format SQL button.
      - Code block: Prism-highlighted SQL query with line numbers.
      - AST Validation Status Pill:
        - `AST Validated Safe` (Green badge with checkmark)
        - `Policy Refusal` (Amber badge: sensitive financial column blocked)
        - `AST Syntax Error / Unknown Table` (Red badge with error details)
    - **Result Visualization Area:**
      - **Case A: Single Scalar Result (e.g., `COUNT(*)`, sum):**
        - Renders as a prominent Metric Card: Large bold value (`42`), uppercase column title (`TOTAL ACTIVE ENGINEERS`), execution duration (`0.04s`).
      - **Case B: Multi-row Tabular Result:**
        - Interactive TanStack Data Table.
        - Controls: Column search, quick sort on headers, pagination (10 / 25 / 50 rows per page), total row count badge.
        - Toolbar actions: `Export CSV`, `Export JSON`, `Full Screen Expand`.
      - **Case C: Policy Refusal (PII / Salary):**
        - Warning Callout Banner: Amber shield icon, headline: `Blocked by Business Safety Policy`, explanatory copy explaining that compensation/national ID fields are restricted by AST governance.
      - **Case D: AST Validation Rejection:**
        - Error Callout Banner: Red alert icon, detailed breakdown of rejected AST components (e.g. `unknown_column: made_up_column`, `not_a_select: statement is DROP`).
      - **Case E: Empty Set (0 Rows):**
        - Informational Banner: Blue info icon, headline: `Query executed successfully (0 rows returned)`.
- **Query Input Console (Fixed Bottom):**
  - Textarea with auto-grow (max 120px height).
  - Placeholder: `"Ask a question about your database in any language (English, Spanish, Hindi, French, German)..."`
  - Submit Button: `Execute Query` (`CornerDownLeft` icon, 44px min height).
  - Keyboard shortcut note: `"Press Enter to submit, Shift+Enter for new line"`.

### 6.4 Main Workspace: Tab 2 — Interactive Schema Explorer & Entity Graph
- **Split-View Architecture:**
  - **Left Subpanel (35% width):** Table & Column Tree
    - Filter search box (`"Filter tables or columns..."`).
    - Accordion of all discovered tables with row count badges.
    - Expanded table details: column name, data type pill (`INTEGER`, `VARCHAR`, `TIMESTAMP`), Primary Key tag (`PK`), Foreign Key link (`FK ➔ departments.department_id`).
    - "Sample Rows Preview" tab: renders first 3-5 sanitized rows for that table.
  - **Right Subpanel (65% width):** Interactive ER Diagram (`SchemaGraph`)
    - Visual node for each database table showing table name, header color, and column list.
    - SVG bezier connectors representing foreign key relationships.
    - Controls: Zoom In/Out, Fit View, Reset Layout, Minimap toggle.
    - Node click opens table sample inspector.

### 6.5 Main Workspace: Tab 3 — Query Audit Trail & Lifecycle Telemetry
- **Telemetry KPI Summary Row:**
  - `Total Queries Logged` (scalar count e.g. `142`)
  - `Success Rate` (percentage e.g. `94.2%`)
  - `Average Latency` (milliseconds e.g. `842ms`)
  - `Policy Refusals & AST Rejections` (count e.g. `8 blocked`)
- **Latency Breakdown Chart:**
  - Stacked horizontal bar or chart showing average time spent in:
    `Retrieval (FAISS)` vs `LLM Generation` vs `Database Execution`.
- **Audit Logs Data Table:**
  - Columns:
    1. `Query ID` (truncated UUID with copy button)
    2. `Timestamp` (ISO format / relative time)
    3. `Natural Language Question`
    4. `Status` (`READY` / `REFUSED` / `INVALID` / `ERROR`)
    5. `Generated SQL` (truncated with preview tooltip)
    6. `Rows` (returned rows count)
    7. `Total Latency` (ms)
    8. `Actions` ("View Trace" button opens slide-out drawer)
- **Query Detail Slide-out Drawer:**
  - Full trace breakdown:
    - Exact prompt sent to LLM
    - Raw LLM response
    - AST validation output & error logs
    - Database engine execution time
    - Masked PII fields summary

---

## 7. State Management & Lifecycle Architecture

### 7.1 Query Lifecycle State Machine

Each user query progresses through an explicit state machine with guaranteed state transitions:

```
[IDLE]
  │ (User submits natural language prompt)
  ▼
[RETRIEVING] ─── (FAISS semantic retrieval of few-shot examples)
  │
  ▼
[GENERATING] ─── (LLM invocation for SQL formulation)
  │
  ├───────────────────────────────────┐
  │ (Starts with "REFUSED")           │ (Returns SQL)
  ▼                                   ▼
[REFUSED] (Policy refusal)       [VALIDATING] (sqlglot AST inspection)
                                      │
                         ┌────────────┴────────────┐
                         │ (Fails syntax/schema)   │ (Passes all 5 checks)
                         ▼                         ▼
                   [INVALID / REJECTED]       [EXECUTING] (SQLAlchemy execution)
                                                   │
                                      ┌────────────┴────────────┐
                                      │ (Runtime DB error)      │ (Success)
                                      ▼                         ▼
                                   [ERROR]                   [READY]
```

### 7.2 Frontend Client State Stores
Implemented via lightweight Zustand or React Context:

1. **`connectionStore`**:
   - `mode`: `'demo' | 'upload' | 'custom'`
   - `connectionStatus`: `'disconnected' | 'connecting' | 'connected' | 'error'`
   - `dialect`: `'postgres' | 'sqlite' | 'mysql'`
   - `displayName`: string
   - `databaseUrl`: string | null
   - `tablesMeta`: `TableMeta[]`
2. **`queryStore`**:
   - `history`: `QueryTurn[]` (list of completed questions and results)
   - `activeQuery`: `QueryTrackerState | null`
   - `useFewShot`: boolean
   - `showSql`: boolean
3. **`policyStore`**:
   - `blockedColumns`: `string[]` (defaults to `salary, bonus, compensation, wage, premium, adines_number, national_id, ssn`)
   - `customBusinessRules`: string
4. **`auditStore`**:
   - `logs`: `AuditLogEntry[]`
   - `filter`: `{ status?: string; search?: string }`
   - `selectedTrace`: `AuditLogEntry | null`

---

## 8. Backend API Bridge Contract (FastAPI REST Specification)

To power the React frontend, the Python backend will expose clean REST endpoints via FastAPI (`query_engine/api.py`).

### 8.1 API Endpoints Specification

#### `GET /api/health`
- **Description:** Engine health and dependency check.
- **Response:**
  ```json
  {
    "status": "healthy",
    "version": "2.4.0",
    "llm_provider": "gemini",
    "llm_model": "gemini-3.8-flash",
    "database_connected": true,
    "dialect": "postgres"
  }
  ```

#### `POST /api/connection/connect`
- **Description:** Connect to Demo, Upload SQLite, or custom URI.
- **Request Body:**
  ```json
  {
    "mode": "demo" | "custom",
    "custom_uri": "postgresql://user:pass@host:5432/dbname"
  }
  ```
  *(For SQLite file upload, use `POST /api/connection/upload` as `multipart/form-data`)*
- **Response:**
  ```json
  {
    "success": true,
    "dialect": "postgres",
    "display_name": "Cloud Postgres (DATABASE_URL)",
    "table_count": 4
  }
  ```

#### `GET /api/schema`
- **Description:** Returns reflected database schema, columns, foreign keys, row counts, and safe sample rows.
- **Response:**
  ```json
  {
    "tables": [
      {
        "name": "employees_clean",
        "columns": ["employee_id", "full_name", "role", "city", "department_id", "is_payroll", "employee_status", "hire_date"],
        "column_types": {
          "employee_id": "INTEGER",
          "full_name": "TEXT",
          "is_payroll": "BOOLEAN"
        },
        "primary_keys": ["employee_id"],
        "foreign_keys": [
          { "constrained": ["department_id"], "referred_table": "departments", "referred_columns": ["department_id"] }
        ],
        "row_count": 142,
        "sample_columns": ["employee_id", "full_name", "role", "city"],
        "sample_rows": [
          ["1", "Allison Hill", "Project Manager", "Dubai"],
          ["2", "Noah Rhodes", "Accountant", "Istanbul"]
        ]
      }
    ]
  }
  ```

#### `POST /api/query/ask`
- **Description:** Executes natural language query through the 5-stage AST safety pipeline.
- **Request Body:**
  ```json
  {
    "question": "How many active civil engineers are there in Dubai?",
    "use_few_shot": true,
    "blocked_columns": ["salary", "ssn", "bonus"],
    "custom_rules": "Optional rule overrides"
  }
  ```
- **Response Body:**
  ```json
  {
    "query_id": "8f3b2a1c",
    "question": "How many active civil engineers are there in Dubai?",
    "status": "ready",
    "is_valid": true,
    "generated_sql": "SELECT COUNT(*) FROM employees_clean WHERE role = 'Civil Engineer' AND city = 'Dubai' AND employee_status = 'active';",
    "columns": ["count"],
    "rows": [[14]],
    "error_message": null,
    "telemetry": {
      "retrieval_latency_ms": 32.4,
      "llm_latency_ms": 612.8,
      "exec_latency_ms": 4.1,
      "total_latency_ms": 649.3,
      "retrieved_examples_count": 5
    }
  }
  ```
- **Refused Response Example (`status: "refused"`):**
  ```json
  {
    "query_id": "3c9d1e2f",
    "question": "Show me employee salaries",
    "status": "refused",
    "is_valid": false,
    "generated_sql": "REFUSED: sensitive financial data",
    "columns": null,
    "rows": null,
    "error_message": "Policy Refusal: sensitive financial data requested (column 'salary' is restricted).",
    "telemetry": { "retrieval_latency_ms": 12.1, "llm_latency_ms": 480.2, "exec_latency_ms": 0.0, "total_latency_ms": 492.3, "retrieved_examples_count": 5 }
  }
  ```

#### `GET /api/audit/logs`
- **Description:** Fetch query audit trail records.
- **Query Params:** `limit=50&offset=0&status=all`
- **Response:**
  ```json
  {
    "total": 142,
    "logs": [
      {
        "query_id": "8f3b2a1c",
        "timestamp": "2026-11-11T13:45:00Z",
        "question": "How many active civil engineers are there?",
        "status": "ready",
        "generated_sql": "SELECT COUNT(*) FROM employees_clean WHERE role = 'Civil Engineer' AND employee_status = 'active';",
        "is_valid": 1,
        "rows_returned": 1,
        "retrieval_latency_ms": 28.5,
        "llm_latency_ms": 580.1,
        "exec_latency_ms": 3.8,
        "total_latency_ms": 612.4
      }
    ]
  }
  ```

---

## 9. Copywriting Contract & Micro-interactions

### 9.1 Primary CTAs [Strict Verb + Noun Pattern]
All actionable buttons MUST follow the `[Verb] [Noun]` pattern. Vague labels ("Submit", "OK", "Go", "Click here") are strictly prohibited.

- `Execute Query` — Runs the natural language pipeline.
- `Connect Database` — Submits custom database URI credentials.
- `Refresh Schema` — Triggers fresh SQLAlchemy schema reflection.
- `Export CSV` — Downloads current tabular dataset as `.csv`.
- `Export JSON` — Downloads current tabular dataset as `.json`.
- `Save Policy` — Commits changes to blocked column list and rules.
- `Clear History` — Clears active chat conversation.
- `Confirm Clear` — Confirms permanent history deletion in modal.
- `Dismiss Alert` — Closes error banner or modal.

### 9.1.1 Destructive Action Confirmation Pattern
Destructive actions (`Clear History`) MUST trigger an explicit confirmation dialog before execution:
- **Dialog Headline:** "Clear Query History?"
- **Body Copy:** "This will permanently remove all past queries in this session. This action cannot be undone."
- **Confirm CTA:** `Confirm Clear` (styled with `destructive` color token: red `#EF4444`, hover `#DC2626`).
- **Cancel CTA:** `Dismiss Alert` (neutral secondary styling).

### 9.2 Empty States Contract

| Screen / Component | Headline | Explanatory Body Copy | Suggested Action |
|---|---|---|---|
| **Query Assistant (New Session)** | "Ready to Query Your Data" | "Ask questions in plain language across 10+ languages. DataMind translates questions to safe SQL with AST validation." | Click one of the 4 sample prompt chips above |
| **Data Visualizer (0 Rows Returned)** | "No Records Found" | "The query executed safely in {elapsed}s, but no rows matched the specified criteria in '{table}'." | Check filter values or inspect available canonical roles in Schema tab |
| **Schema Explorer (Unconnected)** | "No Database Connected" | "Connect to the preloaded HR demo database or supply a custom database URI to inspect tables." | Click `Connect Database` in the sidebar |
| **Audit Telemetry (Empty Log)** | "No Audit Records Yet" | "Audit logs track query execution stages, latencies, and validation results. Execute a query to view logs." | Submit a test query in the Query Console |

### 9.3 Error States Contract [Problem + Immediate Next Step]

| Condition | Visual Badge | User-Facing Error Message | Remediation Action |
|---|---|---|---|
| **AST Policy Refusal** | Amber Badge: `POLICY REFUSED` | "Query Refused: Your question requests sensitive financial or personal data (salary, SSN, bonus) restricted by policy." | Rephrase question to request non-sensitive operational attributes (e.g. employee count, department). |
| **AST Schema Rejection** | Red Badge: `AST INVALID` | "Validation Error: Referenced unknown table or column '{column_name}'. It does not exist in schema whitelist." | Check table definitions in Schema Explorer or click 'Refresh Schema'. |
| **Database Connection Failure** | Red Badge: `CONNECTION FAILED` | "Connection Failed: Could not connect to '{uri}'. Network timeout or authentication failed." | Verify database credentials, port availability, and network IP allowlist. |
| **LLM Provider API Error** | Red Badge: `LLM ERROR` | "AI Model Unavailable: Failed to generate SQL due to invalid API key or rate limit." | Check `GEMINI_API_KEY` or `GROQ_API_KEY` in environment configuration. |

### 9.4 Micro-Interactions & Transitions
- **Button Hover:** 150ms ease-in-out transition (`transition-colors duration-150`).
- **Modal Opening:** Scaled fade-in (100ms scale `0.98 -> 1.0`, opacity `0 -> 1`).
- **SQL Copy Feedback:** Tooltip changes from `"Copy SQL"` to `"Copied!"` with green check icon for 2000ms.
- **Table Hover:** Subtle background tint on table row (`hover:bg-slate-100/50` or `dark:hover:bg-slate-800/40`).
- **Skeleton Loaders:** Subtle shimmer pulse on metric cards and schema nodes while fetching.

---

## 10. Accessibility (a11y), Keyboard Navigation & Responsive Adaptations

### 10.1 Accessibility Requirements
- **Color Contrast:** All text tokens meet **WCAG 2.1 AA** minimum contrast ratios (4.5:1 for standard body text, 3:1 for large text and interactive components).
- **Keyboard Navigation:**
  - Full tab stop cycle through sidebar inputs, prompt chips, chat input, and table actions.
  - `Enter` submits query; `Shift+Enter` inserts line break in prompt input.
  - `Esc` closes any active modal or slide-out drawer.
  - Arrow keys navigate table pagination and schema tabs.
- **Screen Reader Support:**
  - All icon-only buttons include explicit `aria-label` attributes (e.g. `aria-label="Refresh schema cache"`).
  - Status pills announce status with `aria-live="polite"`.

### 10.2 Responsive Breakpoints
- **Mobile (< 768px):** Sidebar collapses into slide-over sheet drawer triggered by hamburger button. Data tables horizontal scroll enabled.
- **Tablet (768px - 1024px):** Sidebar collapses to compact icon-only rail (`w-16`). Schema graph occupies full view width.
- **Desktop (>= 1024px):** Full dual-pane view with persistent 320px sidebar and expansive workspace.

---

## 11. Verification & Acceptance Criteria

This specification will be verified against the implemented frontend code by `gsd-ui-checker` across the 7 design dimensions:

- [ ] **Dimension 1 (Spacing):** All paddings, gaps, and margins use the strict 8-point scale (multiples of 4 only). Minimum 44x44px touch targets on all interactive triggers.
- [ ] **Dimension 2 (Typography):** Exactly 4 font sizes (12px, 14px, 18px, 24px) and 2 weights (400, 600) used across the application. Body line-height = 1.5, heading line-height = 1.2.
- [ ] **Dimension 3 (Color 60/30/10):** Dominant surface (60%), secondary structure (30%), accent blue (10%) strictly adhered to. Accent reserved only for primary CTAs, active nav, focus rings, selected rows, and graph highlights.
- [ ] **Dimension 4 (Copywriting):** All CTAs follow `[Verb] [Noun]`. Empty states provide helpful context and next action. Error messages state problem and concrete next step.
- [ ] **Dimension 5 (Safety & Policy):** AST validation status explicitly indicated with color-coded badges (`AST Valid`, `Policy Refusal`, `AST Invalid`). PII auto-masking notice visible on query results.
- [ ] **Dimension 6 (Component Hierarchy):** Seamless navigation between Query Console, Schema Explorer, and Audit Telemetry. Data tables support sorting, searching, and CSV export.
- [ ] **Dimension 7 (Component Provenance):** Component inventory explicitly recorded with tool, versions, and states.

---
*End of UI Design Contract — DataMind Universal NL2SQL Data Governance Engine*
