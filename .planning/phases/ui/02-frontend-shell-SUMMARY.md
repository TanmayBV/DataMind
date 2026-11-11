---
phase: ui
plan: 02-frontend-shell
subsystem: ui
tags:
  - react
  - vite
  - typescript
  - tailwindcss
  - layout
  - context
requires:
  - 01-backend-bridge
provides:
  - frontend-application-shell
  - governance-sidebar
  - sticky-topbar
  - design-tokens
  - theme-context
  - store-context
affects:
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
tech-stack:
  added:
    - react@19
    - vite@8
    - typescript@6
    - tailwindcss@4
    - "@tailwindcss/vite"
    - lucide-react
    - clsx
    - tailwind-merge
  patterns:
    - Strict 8-point spacing grid and 4-size typography tokens
    - 60/30/10 Dark Cockpit and Light Enterprise color token architecture
    - Accessible Radix-compatible UI primitives with 44x44px touch targets
    - Unified StoreContext for DB connection, query history, governance policies, and telemetry
    - Reactive sticky topbar with live connection pill and latency probe
    - 320px collapsible GovernanceSidebar with 1-click Demo, SQLite file upload, and custom URI
decisions:
  - "Configured Tailwind v4 with @tailwindcss/vite for zero-config lightningcss processing and strict CSS custom property token mappings"
  - "Implemented robust Radix-compatible accessible UI primitives (Button, Badge, Card, Input, Dialog, Tooltip, Tabs) with 44x44px touch targets and full keyboard accessibility"
  - "Implemented dual-theme ThemeContext persisting dark cockpit (default) and light enterprise mode in localStorage"
  - "Centralized global state in StoreContext with automated background health probing and schema synchronization"
metrics:
  duration: 15m
  completed_date: "2026-11-11"
status: complete
actuals:
  tokens: 18500
  tasks: 3
  commits: 0
---

# Phase ui Plan 02: Frontend Shell & Enterprise Governance Summary

Modern React 19 + TypeScript + Vite + Tailwind frontend shell (`frontend/`) delivering an enterprise data governance cockpit with strict 8-point design tokens, theme management, live database switching, and tabbed workspace navigation.

## What Was Built

1. **Vite Scaffolding & Strict Design Token System (`frontend/`)**:
   - `frontend/package.json`: Configured with React 19, TypeScript 6, Vite 8, Tailwind CSS 4, `@tailwindcss/vite`, Lucide React, and clsx/tailwind-merge.
   - `frontend/vite.config.ts`: Configured with `@tailwindcss/vite` and `/api` reverse proxy mapping to FastAPI backend at `http://127.0.0.1:8000`.
   - `frontend/tailwind.config.js` & `frontend/src/index.css`: Enforces strict 8-pt spacing (`space-1` 4px to `space-16` 64px), 4-size typography hierarchy (`text-xs` 12px, `text-sm` 14px, `text-lg` 18px, `text-2xl` 24px), and 60/30/10 dark/light color tokens (`bg-app`, `bg-canvas`, `bg-card`, `bg-sidebar`, `bg-input`, `border-subtle`, `border-prominent`, `text-primary`, `accent-primary`, `status-success`, `status-error`, `status-warning`, `destructive`).

2. **Types & Accessible UI Primitives (`frontend/src/components/ui/Primitives.tsx`)**:
   - `frontend/src/types/index.ts`: Strongly-typed definitions for `TableMeta`, `ColumnMeta`, `ForeignKey`, `QueryTurn`, `QueryTelemetry`, `AuditLogEntry`, `HealthResponse`, and `ConnectionState`.
   - `Primitives.tsx`: Accessible UI building blocks:
     - `Button`: Enforces minimum 44x44px interactive target (`min-h-[44px] min-w-[44px]`), supporting `primary`, `secondary`, `outline`, `ghost`, and `destructive` variants with rotating loading spinner.
     - `Badge`: 12px semi-bold status pills (`success`, `error`, `warning`, `info`, `neutral`).
     - `Card`: Surface card with subtle border and 8-pt padding.
     - `Input`: 14px body text, 44px touch height, accent focus ring.
     - `Dialog`: Accessible modal container with backdrop blur, escape dismissal, and click-outside dismissal.
     - `Tooltip`: Tooltip wrapper with 200ms delay.
     - `Tabs`: Accessible tab switching container with `TabsList`, `TabsTrigger`, and `TabsContent`.

3. **API Client & State Providers (`frontend/src/services/` & `frontend/src/context/`)**:
   - `frontend/src/services/api.ts`: Typed fetch wrapper calling `/api/health`, `/api/connection/connect`, `/api/connection/upload`, `/api/schema`, `/api/query/ask`, and `/api/audit/logs`.
   - `frontend/src/context/ThemeContext.tsx`: Manages Dark Cockpit (default) vs Light Enterprise mode via `dark` class on `<html>` with localStorage persistence.
   - `frontend/src/context/StoreContext.tsx`: Centralized state management for active database connection, reflected schema tables, query execution history, governance policies (8 default blocked columns), audit logs, and live latency health probing.

4. **Navigation Shell & Governance Layout (`frontend/src/components/`)**:
   - `Topbar.tsx`: Sticky `h-14` header with DataMind branding, live database status pill with pulsing emerald indicator, dialect badge (`SQLITE` / `POSTGRES`), discovered table count, live API latency badge, documentation link, and 44x44px theme toggle.
   - `GovernanceSidebar.tsx`: Fixed 320px (`w-80`) sidebar featuring:
     - 3-way Database Switcher: 1-click Demo HR ERP, SQLite `.db`/`.sqlite` file upload, and custom database URI input with regex validation.
     - Schema & Governance summary with `Refresh Schema` CTA (`RotateCw` icon) and `Configure Governance` button.
     - Query pipeline options (Few-shot semantic retrieval toggle and "Show SQL & AST Telemetry" toggle).
   - `Modals.tsx`:
     - `PolicyModal`: Commits restricted column list and custom SQL guardrail rules with `Save Policy` (primary) and `Dismiss Alert` (secondary) CTAs.
     - `ClearHistoryModal`: Confirmation dialog per UI-SPEC 9.1.1 with `Confirm Clear` (destructive red `#EF4444`) and `Dismiss Alert`.
   - `AppShell.tsx`: Coordinates sticky Topbar, 320px GovernanceSidebar, global error alert banner, and tabbed workspace for:
     - Tab 1: Query Console (placeholder container ready for Wave 3)
     - Tab 2: Schema Explorer (placeholder container ready for Wave 3)
     - Tab 3: Audit Telemetry (placeholder container ready for Wave 3)
   - `frontend/src/App.tsx`: Wraps `ThemeProvider` and `StoreProvider` and mounts `AppShell`.
   - `frontend/src/main.tsx`: Mounts React root into `index.html`.

## Verification Results

```bash
npm --prefix frontend run build
```

Output:
```
> datamind-frontend@2.4.0 build
> tsc -b && vite build

vite v8.3.5 building client environment for production...
transforming...
✓ 1943 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.58 kB │ gzip:  0.39 kB
dist/assets/index-DUX9IFrc.css   27.40 kB │ gzip:  5.78 kB
dist/assets/index-OQeVzwwM.js   283.21 kB │ gzip: 87.68 kB

✓ built in 1.48s
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Type Definition] React 19 `cloneElement` element typing**
- **Found during:** Task 1 `tsc -b` execution
- **Issue:** TypeScript in React 19 flags `children.props` as `unknown` when cloning untyped ReactElement children in `DialogTrigger` and `DialogClose`.
- **Fix:** Constrained `children` to `React.ReactElement<{ onClick?: (e: React.MouseEvent) => void }>` in `Primitives.tsx`.
- **Files modified:** `frontend/src/components/ui/Primitives.tsx`

**2. [Rule 1 - Bundling Config] Tailwind v4 zero-PostCSS integration**
- **Found during:** Task 3 `vite build` execution
- **Issue:** `postcss.config.js` referencing `autoprefixer` caused Vite build failure because Tailwind v4 uses `@tailwindcss/vite` and lightningcss directly without PostCSS.
- **Fix:** Removed redundant `postcss.config.js` and relied on `@tailwindcss/vite` for automated autoprefixing and bundling.
- **Files modified:** `frontend/postcss.config.js` (removed)

**3. [Rule 2 - TypeScript Configuration] CSS Side-Effect Module Declarations**
- **Found during:** Task 3 `tsc -b` execution
- **Issue:** TypeScript flagged `Cannot find module or type declarations for side-effect import of './index.css'` in `main.tsx`.
- **Fix:** Added `frontend/src/vite-env.d.ts` with `/// <reference types="vite/client" />`.
- **Files modified:** `frontend/src/vite-env.d.ts`

## Self-Check: PASSED

- [x] `frontend/package.json` created with build scripts
- [x] `frontend/vite.config.ts` configured with proxy and Tailwind Vite plugin
- [x] Strict 8-pt spacing, 4-size typography, and 60/30/10 theme tokens in `index.css`
- [x] UI primitives (`Button`, `Badge`, `Card`, `Input`, `Dialog`, `Tooltip`, `Tabs`) in `Primitives.tsx`
- [x] Typed `api.ts` client matching FastAPI backend bridge
- [x] `ThemeContext.tsx` with dark (default) / light modes and localStorage persistence
- [x] `StoreContext.tsx` managing connection, schema, queries, policy, and telemetry
- [x] `Topbar.tsx` with live database pill, dialect tag, and latency probe
- [x] `GovernanceSidebar.tsx` with 1-click Demo, SQLite file upload, and custom URI
- [x] `Modals.tsx` with PolicyModal and ClearHistoryModal
- [x] `AppShell.tsx` hosting Topbar, Sidebar, and tab navigation
- [x] `App.tsx` root wrapping providers and mounting `AppShell`
- [x] `npm --prefix frontend run build` passes cleanly in 1.48s with 0 errors
