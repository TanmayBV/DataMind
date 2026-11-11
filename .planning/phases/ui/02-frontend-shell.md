---
phase: ui
plan: 02-frontend-shell
type: execute
wave: 2
depends_on:
  - 01-backend-bridge
files_modified:
  - frontend/package.json
  - frontend/vite.config.ts
  - frontend/tailwind.config.js
  - frontend/src/index.css
  - frontend/src/main.tsx
  - frontend/src/App.tsx
  - frontend/src/types/index.ts
  - frontend/src/services/api.ts
  - frontend/src/context/ThemeContext.tsx
  - frontend/src/context/StoreContext.tsx
  - frontend/src/components/ui/Primitives.tsx
  - frontend/src/components/layout/Topbar.tsx
  - frontend/src/components/layout/GovernanceSidebar.tsx
  - frontend/src/components/modals/Modals.tsx
  - frontend/src/components/layout/AppShell.tsx
autonomous: true
requirements:
  - UI-02-FRONTEND-SCAFFOLD
  - UI-03-SHELL-GOVERNANCE
estimate:
  tokens: 22000
  raw_tokens: 15000
  tasks: 3
  confidence: high
must_haves:
  truths:
    - "Vite + React 18/19 + TypeScript frontend builds cleanly with zero errors via npm run build"
    - "Strict 8-pt design system spacing and typography scale are enforced in Tailwind and index.css"
    - "frontend/src/App.tsx wraps ThemeProvider and StoreProvider, rendering AppShell at root"
    - "AppShell renders sticky Topbar, 320px GovernanceSidebar, Modals, and placeholder tab panels for Query Console, Schema Explorer, and Audit Telemetry"
    - "Dark Cockpit mode (60/30/10) and Light Enterprise mode toggle smoothly with localStorage persistence"
  artifacts:
    - "frontend/package.json"
    - "frontend/vite.config.ts"
    - "frontend/tailwind.config.js"
    - "frontend/src/App.tsx"
    - "frontend/src/components/layout/AppShell.tsx"
  key_links:
    - "frontend/src/App.tsx wraps ThemeProvider and StoreProvider and mounts AppShell"
    - "AppShell.tsx provides Radix Tabs container with lightweight tab stubs so npm run build compiles cleanly before full feature tabs are wired"
    - "Vite dev proxy forwards /api calls to FastAPI backend on http://127.0.0.1:8000"
---

<objective>
Scaffold the modern React + TypeScript + Vite frontend and deliver the enterprise application shell, governance sidebar, design token system, and theme management.

Establish a bulletproof foundation conforming strictly to `UI-SPEC.md`:
- Strict 8-point spacing grid and 4-size typography scale
- Radix UI accessible primitives and 44x44px interactive button targets
- Global ThemeContext (Dark cockpit 60/30/10 vs Light Enterprise) and StoreContext (connection, query, policy, audit state)
- Sticky Topbar with live database connection pill and live latency probe
- Collapsible GovernanceSidebar with 1-click DB switching, SQLite file upload, and custom URI input
- AppShell with lightweight placeholder tabs enabling progressive assembly and clean compilation

Output:
- Configured Vite + React + Tailwind frontend application in `frontend/`
- Full UI primitives and layout shell with clean tab placeholders
- Complete mounting in `frontend/src/App.tsx` passing `npm run build`
</objective>

<execution_context>
@~/.gemini/antigravity/gsd-core/workflows/execute-plan.md
@~/.gemini/antigravity/gsd-core/templates/summary.md
</execution_context>

<context>
@d:/nl2sql-rag-project/UI-SPEC.md
@.planning/phases/ui/01-backend-bridge.md
@d:/nl2sql-rag-project/query_engine/api_server.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Vite Scaffolding, 8-Pt Tailwind Tokens, Types & Base Radix Primitives</name>
  <files>frontend/package.json, frontend/vite.config.ts, frontend/tailwind.config.js, frontend/src/index.css, frontend/src/types/index.ts, frontend/src/components/ui/Primitives.tsx</files>
  <action>
1. Initialize Vite + React + TypeScript in `frontend/` directory. Configure `package.json` with required dependencies:
   - `lucide-react`, `@radix-ui/react-dialog`, `@radix-ui/react-tabs`, `@radix-ui/react-tooltip`, `@radix-ui/react-dropdown-menu`, `@radix-ui/react-slot`
   - `@tanstack/react-table`
   - `@xyflow/react`
   - `clsx`, `tailwind-merge`
   - Dev dependencies: `tailwindcss`, `postcss`, `autoprefixer`, `typescript`, `@types/react`, `@types/react-dom`, `@vitejs/plugin-react`
2. Run `npm --prefix frontend install` to install all dependencies cleanly.
3. Configure `vite.config.ts` with API reverse proxy mapping `/api` to `http://127.0.0.1:8000`.
4. Configure `tailwind.config.js` and `frontend/src/index.css` adhering strictly to `UI-SPEC.md`:
   - 8-pt spacing tokens: `space-1` (4px), `space-2` (8px), `space-4` (16px), `space-6` (24px), `space-8` (32px), `space-12` (48px), `space-16` (64px).
   - Strict typography scale: exactly 4 font sizes (`text-xs` 12px, `text-sm` 14px, `text-lg` 18px, `text-2xl` 24px) and 2 weights (`font-normal` 400, `font-semibold` 600). Line heights: headings 1.2, body 1.5.
   - 60/30/10 dark & light theme palette tokens (`bg-app`, `bg-canvas`, `bg-card`, `bg-sidebar`, `bg-input`, `border-subtle`, `border-prominent`, `text-primary`, `text-secondary`, `text-muted`, `accent-primary`, `status-success`, `status-error`, `status-warning`, `status-info`).
5. Create `frontend/src/types/index.ts` defining data models:
   - `TableMeta`, `ColumnMeta`, `ForeignKey`, `QueryTurn`, `QueryTelemetry`, `AuditLogEntry`, `HealthResponse`, `ConnectionState`.
6. Implement `frontend/src/components/ui/Primitives.tsx` providing standard UI components:
   - `Button`: minimum 44x44px interactive target (`min-h-[44px] min-w-[44px]`), supporting primary, secondary, outline, ghost, and destructive variants with loading spinner.
   - `Badge`: 12px semi-bold font (`text-xs font-semibold`) for AST statuses, dialects, and row counts.
   - `Card`: clean surface card with subtle border and 8-pt padding.
   - `Input`: 14px body text, 44px height, accent focus ring.
   - `Dialog`: Radix dialog wrapper with backdrop blur and escape dismissal.
   - `Tooltip`: Radix tooltip wrapper with 200ms delay.
  </action>
  <verify>
    <automated>npm --prefix frontend run build</automated>
    <fails_when>TypeScript compiler error, missing package error, or CSS configuration failure</fails_when>
  </verify>
  <done>
    Frontend project scaffolded, dependencies installed, design tokens configured, UI primitives exported, and base build succeeds.
  </done>
</task>

<task type="auto">
  <name>Task 2: Context Providers, API Service Client, Topbar, Sidebar & Governance Modals</name>
  <files>frontend/src/services/api.ts, frontend/src/context/ThemeContext.tsx, frontend/src/context/StoreContext.tsx, frontend/src/components/layout/Topbar.tsx, frontend/src/components/layout/GovernanceSidebar.tsx, frontend/src/components/modals/Modals.tsx</files>
  <action>
1. Implement `frontend/src/services/api.ts` with typed fetch functions calling `/api/health`, `/api/connection/connect`, `/api/connection/upload`, `/api/schema`, `/api/query/ask`, and `/api/audit/logs`.
2. Implement `ThemeContext.tsx` managing `dark` (default) vs `light` theme class on `<html>` with localStorage persistence.
3. Implement `StoreContext.tsx` managing:
   - `connection`: active mode ('demo' | 'upload' | 'custom'), status ('connected' | 'connecting' | 'error'), dialect, displayName, tablesMeta, refreshSchema action.
   - `query`: history array of QueryTurn, activeQuestion, useFewShot, showSql.
   - `policy`: blockedColumns (default 8 sensitive columns), customRules.
   - `audit`: logs array, selectedTrace for drawer.
4. Build `Topbar.tsx` (`h-14`, sticky top, z-10):
   - Left: Logo icon (`BrainCircuit`), title "DataMind", version tag `v2.4`.
   - Center: Connection pill with pulsing emerald dot (`status-success`), database name, dialect badge (`SQLITE` / `POSTGRES`), and table count.
   - Right: `ThemeToggle` button (Sun/Moon, 44x44px target), `HealthStatus` badge showing live API latency, Docs link.
5. Build `GovernanceSidebar.tsx` (`w-80`, desktop fixed, mobile collapsible):
   - Database Switcher:
     - 1-Click "Demo HR ERP" button (triggers demo connection).
     - "Upload SQLite" file input (.db, .sqlite) with file upload progress.
     - "Custom Database URI" input with regex validation (`postgresql://`, `mysql://`, `sqlite:///`) and `Connect Database` CTA.
   - Schema & Policy Summary:
     - Table counter with `Refresh Schema` CTA button (`RotateCw` icon).
     - Blocked columns summary badge (e.g. "8 blocked columns active").
     - `Configure Governance` button opening PolicyModal.
   - Query Controls:
     - Few-shot semantic retrieval (FAISS) toggle.
     - "Show SQL & AST Telemetry" toggle switch.
6. Implement `Modals.tsx` containing:
   - `PolicyModal`: Text input for comma-separated blocked columns and textarea for custom rules override, with `Save Policy` (primary) and `Dismiss Alert` (secondary) CTAs.
   - `ClearHistoryModal`: Confirmation dialog per UI-SPEC Section 9.1.1 with `Confirm Clear` (destructive red `#EF4444`) and `Dismiss Alert` CTAs.
  </action>
  <verify>
    <automated>npm --prefix frontend run build</automated>
    <fails_when>TypeScript typecheck errors or unresolved imports in contexts, layout, or modals</fails_when>
  </verify>
  <done>
    Typed API client, ThemeContext, StoreContext, Topbar, GovernanceSidebar, and Modals implemented and passing TypeScript build.
  </done>
</task>

<task type="auto">
  <name>Task 3: Stub Tabs, AppShell Navigation & Complete App.tsx Root Assembly</name>
  <files>frontend/src/App.tsx, frontend/src/main.tsx, frontend/src/components/layout/AppShell.tsx</files>
  <action>
1. Implement `AppShell.tsx` hosting Topbar, GovernanceSidebar, and Radix Tabs navigation (`Query Console`, `Schema Explorer`, `Audit Telemetry`).
   - Implement lightweight, visually styled placeholder tab panels for each tab so the navigation shell is fully testable and responsive:
     - Tab 1 ("Query Console"): Container displaying placeholder banner "Query Console: Starter Prompts, NL2SQL Input & TanStack DataTable (Wired in Wave 3)".
     - Tab 2 ("Schema Explorer"): Container displaying placeholder banner "Schema Explorer: Table Accordion & ReactFlow ER Graph (Wired in Wave 3)".
     - Tab 3 ("Audit Telemetry"): Container displaying placeholder banner "Audit Telemetry: Lifecycle KPIs, Latency Breakdown & Trace Drawer (Wired in Wave 3)".
2. Implement `frontend/src/App.tsx` explicitly wrapping the application in `ThemeProvider` and `StoreProvider`, and rendering `AppShell` as the root component:
   ```tsx
   import React from "react";
   import { ThemeProvider } from "./context/ThemeContext";
   import { StoreProvider } from "./context/StoreContext";
   import { AppShell } from "./components/layout/AppShell";

   export default function App() {
     return (
       <ThemeProvider>
         <StoreProvider>
           <AppShell />
         </StoreProvider>
       </ThemeProvider>
     );
   }
   ```
3. Ensure `frontend/src/main.tsx` mounts `App.tsx` into `#root` in `frontend/index.html`.
4. Run `npm run build` to verify clean compilation with zero warnings or missing imports.
  </action>
  <verify>
    <automated>npm --prefix frontend run build</automated>
    <fails_when>Vite build fails, bundle generation errors, or broken component tree</fails_when>
  </verify>
  <done>
    `frontend/src/App.tsx` wraps context providers and mounts `AppShell`; tab stubs switch seamlessly; frontend builds cleanly with zero errors.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Client Browser -> FastAPI Backend | REST API client invokes backend endpoints; untrusted database connection URIs and uploaded files pass through. |
| Client Browser -> LocalStorage | User theme preference and local session preferences persisted in browser storage. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-ui-07 | Tampering | `frontend/src/services/api.ts` | medium | mitigate | All API payloads use strict TypeScript interfaces matching FastAPI Pydantic models. Response errors are caught and surfaced via standard toast/banner alerts. |
| T-ui-08 | Cross-Site Scripting (XSS) | UI Rendering Components | high | mitigate | React JSX automatic escaping protects against DOM-based XSS. No `dangerouslySetInnerHTML` is used for user questions or database cell values. |
| T-ui-09 | Information Disclosure | `GovernanceSidebar.tsx` / `Modals.tsx` | medium | mitigate | Database connection strings with sensitive passwords are treated as passwords (`type="password"` or masked in UI state). |
| T-ui-SC | Tampering | npm dependencies | high | mitigate | Only approved packages (`@radix-ui/*`, `@tanstack/react-table`, `@xyflow/react`, `lucide-react`, `tailwindcss`) installed directly from npm registry. |
</threat_model>

<verification>
npm --prefix frontend run build
</verification>

<success_criteria>
Frontend shell builds cleanly with 0 errors, mounts ThemeProvider and StoreProvider in App.tsx, renders sticky Topbar, 320px Sidebar, and functional tab navigation with lightweight stubs.
</success_criteria>

<output>
Create `.planning/phases/ui/02-frontend-shell-SUMMARY.md` when execution completes.
</output>
