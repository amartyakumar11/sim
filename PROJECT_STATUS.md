# Digital Twin Simulation Sandbox – Project Status Document

**Last Updated**: January 28, 2026  
**Current Branch**: `feature/phase-4`  
**Project Stage**: MVP Development (Phase 4 Complete, Phase 5 Polish Applied)

---

## 🎯 Project Overview

**What We're Building**: A production-grade web application for simulating and optimizing Electric Vehicle (EV) battery swapping station networks in urban environments.

**Core Value Proposition**: Enable city planners, fleet operators, and infrastructure investors to test "what-if" scenarios (e.g., "What happens if we add 3 more stations downtown?") and receive data-driven insights on wait times, utilization, ROI, and operational costs—without deploying real infrastructure.

**Target Users**:
- Urban mobility planners
- EV fleet operators
- Infrastructure investors
- Logistics optimization teams

---

## 🏗️ System Architecture

### Backend Stack
- **Language**: Python 3.11+
- **Web Framework**: FastAPI (async API endpoints)
- **Task Queue**: Celery with Redis broker/backend
- **Database**: PostgreSQL (scenario storage, job metadata)
- **Simulation Engine**: Custom discrete-event simulation (SimPy-based)
  - `DemandGenerator`: Generates EV swap requests with time/location distribution
  - `Station`: Models charger capacity, inventory, queuing
  - `KPIEngine`: Tracks wait times, utilization, lost swaps
  - `ROIEngine`: Calculates cost/revenue impacts per scenario

### Frontend Stack
- **Framework**: React 18 (functional components, hooks)
- **Routing**: React Router Dom v6
- **UI Library**: Ant Design (tables, cards, forms, icons)
- **Visualization**: Recharts (line/bar charts, disabled animations per UX contract)
- **Build Tool**: Vite
- **State Management**: React hooks (`useState`, `useEffect`, `useMemo`, `useCallback`)

### Infrastructure
- **Containerization**: Docker Compose (5 services: frontend, backend, celery, redis, postgres)
- **API Communication**: Axios (REST)
- **File Structure**:
  ```
  digital-twin/
  ├── backend/
  │   ├── api/ (FastAPI endpoints, Pydantic models)
  │   ├── simulation/ (core engine: main.py, engines, demand, routing)
  │   ├── nlp/ (natural language → TOON DSL translation via Gemini)
  │   └── tasks.py (Celery background jobs)
  ├── frontend/
  │   ├── src/pages/ (Home, ScenarioSubmission, JobMonitor, ResultsDashboard, SimulationScene)
  │   ├── docs/ui-style-contract.md (UI/motion rulebook)
  │   └── services/api.js (API client)
  ├── data/results/ (NDJSON event logs, summary JSON per run)
  └── docker-compose.yml
  ```

---

## ✅ What We've Built So Far

### Phase 1: Core Simulation Engine & API (Complete)
- [x] Discrete-event simulation engine (`simulation_engine.py`)
- [x] Two operational modes:
  - **"fake" mode**: Instant mock results (for UI/testing)
  - **"real" mode**: Full discrete-event simulation (stations, queues, charging, swaps)
- [x] FastAPI endpoints:
  - `POST /api/run-simulation` (single sync run)
  - `POST /api/scenarios/submit` (async Celery job)
  - `GET /api/jobs/{run_id}/status` (polling for job completion)
  - `GET /api/jobs/{run_id}/result` (fetch simulation output)
  - `POST /api/nl-to-toon` (natural language → structured config)
- [x] Celery task queue for long-running simulations
- [x] Redis for job status/result caching
- [x] PostgreSQL schema for scenario/job metadata
- [x] KPI & ROI engines (avg wait time, lost swaps, utilization, cost impact, ROI)

### Phase 2: Frontend Foundation (Complete)
- [x] React app with routing (Home, Submit Scenario, Job Monitor, Results Dashboard)
- [x] Ant Design layout (header, nav, content wrapper)
- [x] `ScenarioSubmission` page:
  - Form for city config (stations with lat/lon, capacity)
  - Interventions (add/upgrade stations)
  - Simulation duration, mode toggle (fake/real)
- [x] `JobMonitor` page: polling table showing all submitted jobs + status
- [x] `ResultsDashboard` page: KPI cards, charts (wait time, utilization)

### Phase 3: UI Style Contract & Simulation Visualization (Complete)
- [x] **UI Style Contract** (`frontend/docs/ui-style-contract.md`):
  - Glassmorphism rules (allowed: overlays; forbidden: charts, tables, core entities)
  - Motion system (max 280ms, 3 easing curves, reduced-motion support)
  - Visual hierarchy (primary/secondary/background layers)
- [x] **SimulationScene** page (`/simulation`):
  - City canvas with 2D spatial layout (no map SDK yet)
  - Station nodes sized by capacity (S/M/L tiers), positioned by x/y coordinates
  - Real-time state visualization:
    - Queue length → vertical bars (height = queue depth)
    - Charging activity → perimeter dots (count = active chargers)
    - State-based colors (idle/active/busy)
  - Glass observer overlay (system snapshot: counts, pressure, hotspot)
  - Demo mode toggle (live state updates every 2s, disabled by default)
  - Entry animations (fade + scale, staggered delays)
  - Reduced-motion compliance (disables demo + transforms)

### Phase 4: Data Revelation & Progressive Disclosure (Complete)
- [x] **ResultsDashboard** progressive reveal:
  - Data layer hidden by default (no chart overload on page load)
  - "Reveal data layer" button → fade/slide charts in on demand
  - Charts: wait time over time, utilization over time (Recharts, `isAnimationActive={false}`)
  - Station performance table (flat, not glass)
  - Drill-down drawer (raw JSON summary for advanced users)
- [x] **Type-safe KPI rendering**:
  - `asNumber()` and `formatFixed()` helpers → no crash if backend sends strings
  - Defensive artifact handling (`artifacts.events || '(not available)'`)
- [x] **Polling leak fix**: `retryTimerRef` + `aliveRef` → no setState after unmount

### Phase 5: Polish, Performance, MVP Hardening (Complete)
- [x] **Simulation page performance**:
  - Memoized `StationNode` component → no unnecessary re-renders
  - `usePrefersReducedMotion()` hook → respects OS accessibility setting
  - Demo updates force-disabled when reduced-motion is active
  - Tightened CSS transitions (only `transform`/`opacity`, no `all`)
- [x] **Results page hardening**:
  - Polling cleanup on unmount (no runaway retries)
  - Safe number formatting (handles string numbers, undefined, null)
  - Removed emoji from headers (production-grade feel)
- [x] **Motion contract enforcement**:
  - All animations ≤ 280ms
  - Only allowed easing curves used
  - Reduced-motion media query active on both pages
- [x] **Linting**: zero errors on `SimulationScene.jsx`, `ResultsDashboard.jsx`

---

## 🚀 Current Capabilities (What Works Right Now)

1. **Submit a Scenario**:
   - Define city config (stations, capacity, lat/lon)
   - Specify interventions (add stations, upgrade capacity)
   - Choose simulation mode (fake for instant results, real for full simulation)
   - Submit → Celery task starts, returns `run_id`

2. **Monitor Job Progress**:
   - Poll `/api/jobs/{run_id}/status` to see PENDING → RUNNING → COMPLETED
   - Job monitor page shows all submitted jobs in a table

3. **View Results**:
   - Navigate to `/results/{run_id}`
   - See 8 KPI cards: avg wait time, lost swaps, utilization, throughput, idle inventory, cost impact, ROI, events logged
   - Click "Reveal data layer" → charts + station performance table appear
   - Click "Drill-down" → raw JSON summary in side panel

4. **Watch Live Simulation**:
   - Navigate to `/simulation`
   - See city canvas with 6 mock stations
   - Click "Play demo updates" → stations change state every 2s (queue bars grow/shrink, charging dots animate)
   - Glass overlay shows system pressure (Low/Medium/High) and hotspot station
   - Reduced-motion users see static scene, demo button disabled

5. **Natural Language Input** (experimental):
   - `POST /api/nl-to-toon` with plain English → structured scenario JSON
   - Example: "Add 3 stations downtown with 5 chargers each" → backend calls Gemini API → returns config

---

## 🔧 Known Limitations & Technical Debt

### Backend
- [ ] **No real city/routing data**: stations use mock x/y coords, not real lat/lon with road network
- [ ] **No demand calibration**: `DemandGenerator` uses random distributions, not real EV fleet data
- [ ] **No multi-scenario comparison**: can only view one result at a time (no side-by-side diff)
- [ ] **No authentication/authorization**: API is open, no user accounts
- [ ] **No result caching beyond Redis TTL**: old jobs may be lost
- [ ] **NL-to-TOON translation not production-ready**: relies on LLM, no validation

### Frontend
- [ ] **No real-time WebSocket updates**: polling only (3s intervals)
- [ ] **Simulation page uses mock data**: not connected to real simulation output (no API integration yet)
- [ ] **No scenario history/favorites**: can't save/load scenarios
- [ ] **No map SDK integration**: spatial layout is abstract, not tied to real geography
- [ ] **No mobile-responsive layout**: optimized for desktop only
- [ ] **No error boundaries**: React crashes show white screen (needs global error handler)

### Infrastructure
- [ ] **Local Docker only**: no cloud deployment scripts (AWS/GCP/Azure)
- [ ] **No CI/CD pipeline**: manual testing, no GitHub Actions
- [ ] **No observability**: no logging (Sentry), no metrics (Prometheus), no tracing (Jaeger)
- [ ] **No backup/restore**: PostgreSQL data lost if container removed

---

## 🎨 UI/UX Design Decisions

### Design Philosophy
- **Clarity over decoration**: stakeholder comprehension in under 60 seconds
- **Progressive disclosure**: data hidden by default, revealed on demand (no chart overload)
- **Motion as meaning**: animations only for state transitions, no looping/decorative motion
- **Accessibility-first**: WCAG AA contrast, reduced-motion support, no glass on core content

### Key UI Patterns
1. **City Canvas** (Simulation page):
   - Stations are physical discs, not abstract cards
   - Size → capacity, color → state, queue bars → wait pressure
   - No numbers until user hovers/clicks (visual density > metrics)

2. **Data Revelation** (Results page):
   - KPI cards always visible (high-level summary)
   - Charts/tables hidden behind "Reveal data layer" button
   - Drill-down drawer for raw JSON (expert users only)

3. **Glassmorphism**:
   - Only on observer/control overlays (system snapshot, toggle buttons)
   - Forbidden on charts, tables, station entities (readability first)
   - Max blur 12px, opacity 0.65–0.90, mandatory border

4. **Animation Contract**:
   - Entry: 220ms, `cubic-bezier(0.2, 0.8, 0.2, 1)` (ease-out)
   - Exit: 220ms, `cubic-bezier(0.4, 0.0, 1, 1)` (ease-in)
   - Hover: 160ms, `cubic-bezier(0.25, 0.1, 0.25, 1.0)` (ease-in-out)
   - Reduced-motion: ≤ 80ms or disabled

---

## 🧪 Testing Status

### What's Tested
- [x] Backend API endpoints (manual curl/Postman testing)
- [x] Celery task execution (manual observation of Redis keys + result files)
- [x] Frontend linting (ESLint, zero errors on edited files)
- [x] UI style contract compliance (manual checklist)

### What's Not Tested
- [ ] **No unit tests**: backend (`pytest`), frontend (`vitest`/`jest`)
- [ ] **No integration tests**: end-to-end scenario submission → result retrieval
- [ ] **No performance tests**: simulation engine bottlenecks unknown
- [ ] **No accessibility audit**: no screen reader testing, WCAG automated scan
- [ ] **No browser compatibility**: only tested on Chrome (latest)

---

## 📊 Example Use Case (End-to-End Flow)

**Scenario**: A city planner wants to know if adding 2 new stations in the downtown area will reduce average wait times below 10 minutes.

1. **User navigates to `/submit`**
2. **User fills form**:
   - Existing city config: 4 stations (capacity 4, 5, 6, 4)
   - Interventions: `[{ "action": "add", "station_id": "ST_NEW_1", "lat": 40.75, "lon": -73.98, "capacity": 6 }, { "action": "add", "station_id": "ST_NEW_2", "lat": 40.76, "lon": -73.97, "capacity": 6 }]`
   - Duration: 120 minutes
   - Mode: "real"
3. **User clicks "Submit"** → `POST /api/scenarios/submit` → returns `{ "run_id": "abc123...", "status": "PENDING" }`
4. **User navigates to `/monitor`** → sees job in table, status "RUNNING"
5. **Backend**: Celery worker picks up task, runs 120-minute simulation (takes ~10s wall time), writes `data/results/abc123_summary.json`
6. **User refreshes monitor** → status "COMPLETED"
7. **User clicks "View Results"** → navigates to `/results/abc123`
8. **Results page loads**:
   - KPI cards show: avg wait time = 8.3 min (green), lost swaps = 12, utilization = 68%, throughput = 240 swaps
   - "Reveal data layer" button visible
9. **User clicks "Reveal data layer"**:
   - Charts fade in (wait time over time, utilization over time)
   - Station performance table shows per-station breakdown
10. **User sees**: Wait time dropped from 12min (baseline) to 8.3min → intervention was successful
11. **User clicks "Drill-down"** → sees raw JSON with full KPI breakdown

---

## 🚧 What's Next (Potential Future Work)

### High-Priority Features
1. **Scenario Comparison**:
   - Run multiple scenarios (baseline, +2 stations, +3 stations, upgrade existing)
   - Side-by-side KPI table, diff visualization
   - Rank scenarios by ROI, wait time, cost

2. **Real Geography Integration**:
   - Replace mock x/y with real lat/lon
   - Integrate Mapbox/Google Maps SDK
   - Use real road network for demand routing (not Euclidean distance)

3. **Historical Data Ingestion**:
   - Upload CSV of past EV swap logs (timestamp, location, wait time)
   - Calibrate `DemandGenerator` to match real demand patterns
   - Validate simulation against historical performance

4. **Advanced NLP**:
   - Multi-turn dialogue ("Add 3 stations" → "Where?" → "Downtown near City Hall")
   - Constraint validation ("That location conflicts with zoning rules")
   - Auto-suggest optimal interventions based on current KPIs

5. **Live Simulation Streaming**:
   - WebSocket connection from backend to frontend
   - Real-time event stream on `/simulation` page (not mock data)
   - Scrubber/timeline to replay past events

### Medium-Priority Enhancements
- User accounts & authentication (login, saved scenarios, team sharing)
- Export results to PDF/PowerPoint (stakeholder presentations)
- Mobile-responsive UI (tablet/phone support)
- Dark mode (respecting OS preference)
- Notification system (email/Slack when long simulation completes)

### Low-Priority / Nice-to-Have
- 3D city visualization (Three.js/Babylon.js)
- Multi-city support (NYC, LA, Tokyo scenarios)
- Cost optimizer (genetic algorithm to find best station placement)
- A/B testing framework (simulate two interventions, auto-pick winner)

---

## 🐛 Current Known Bugs

### Critical
- None (all Phase 5 crash bugs fixed)

### Medium
- [ ] **Long runIds overflow KPI card**: `runIdFromParams.substring(0, 8)...` → if ID > 50 chars, layout breaks (fixed with `runIdShort` but not tested for extreme cases)
- [ ] **Polling continues on error**: if `/api/jobs/{run_id}/result` returns 500, retries forever (should stop after N attempts)

### Minor
- [ ] **Ant Design findDOMNode warning**: console shows deprecation warning (harmless, but noisy)
- [ ] **Demo toggle button label truncates on mobile**: "Pause demo updates" → "Pause demo..." on narrow screens
- [ ] **No loading skeleton on Results page**: blank white screen during initial `fetchResults()` (3s perceived lag)

---

## 🛠️ Development Workflow

### How to Run Locally
1. **Prerequisites**: Docker Desktop, Node 18+, Python 3.11+
2. **Clone repo**: `git clone <repo_url> && cd SIM/digital-twin`
3. **Environment setup**:
   - Copy `backend/.env.example` → `backend/.env` (add Gemini API key for NL-to-TOON)
   - Copy `frontend/.env.example` → `frontend/.env` (set `VITE_API_URL=http://localhost:8000`)
4. **Start services**: `docker compose up --build`
5. **Access**:
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
6. **Run simulation**:
   - Navigate to `http://localhost:3000/submit`
   - Fill form → submit → check `/monitor` → view `/results/{run_id}`

### Key Commands
- **Backend tests** (when written): `cd backend && pytest`
- **Frontend tests** (when written): `cd frontend && npm test`
- **Lint frontend**: `cd frontend && npm run lint`
- **Build frontend**: `cd frontend && npm run build` (outputs to `dist/`)
- **Stop all**: `docker compose down`
- **Clean data**: `docker compose down -v` (removes DB + Redis volumes)

### Branch Strategy
- `main`: stable, deployable code
- `feature/*`: new features (current: `feature/phase-4`)
- `bugfix/*`: bug fixes
- `hotfix/*`: urgent production fixes

---

## 📈 Metrics (If This Were Production)

### Performance Targets
- **Simulation latency**: < 15s for 120-minute "real" mode simulation
- **API response time**: < 100ms (p95) for status/result endpoints
- **Frontend load time**: < 2s (p90) for Results page initial render
- **Concurrent jobs**: 10+ Celery workers handling 100+ simultaneous scenarios

### Business KPIs
- **User comprehension time**: < 60s from landing on Results page to understanding if intervention succeeded
- **Scenario submission rate**: 50+ scenarios/day (indicates active usage)
- **Conversion to action**: 30%+ of simulations lead to real-world infrastructure changes

---

## 🤝 Team & Roles (Hypothetical)

If this were a team project:
- **Product Owner**: Defines features, prioritizes backlog
- **Backend Engineer**: FastAPI, Celery, simulation engine
- **Frontend Engineer**: React, Ant Design, UI/UX implementation
- **Data Scientist**: Demand calibration, KPI validation, ML optimizer
- **DevOps**: Docker, CI/CD, cloud deployment, monitoring
- **Designer**: UI mockups, style contract, accessibility audit

---

## 🎓 Key Learnings & Design Decisions

### Why Celery?
- Simulations take 10–30s → can't block HTTP request
- Need job queue with retry, result caching, priority
- Redis as broker/backend → simple, fast, no extra DB

### Why "fake" and "real" modes?
- Frontend dev needs instant feedback (can't wait 30s per test)
- "fake" returns mock data in <100ms
- "real" for production, accurate KPIs

### Why glassmorphism restrictions?
- Frosted glass looks modern but kills readability on charts
- Charts need high contrast, clear data ink
- Overlays can use glass (they float above solid backgrounds)

### Why progressive disclosure?
- Stakeholders don't need 10 charts on load → cognitive overload
- KPI cards give "pass/fail" signal in 5s
- Charts for drill-down only (advanced users, specific questions)

### Why no map SDK yet?
- Wanted spatial intuition without external API dependency
- Abstract canvas proves UX concept first
- Map SDK adds complexity (API keys, tile loading, projection math)

---

## 📚 Key Files to Understand the System

### Backend
1. `backend/simulation/main.py`: Entry point, dispatches to fake/real simulation
2. `backend/simulation/simulation_engine.py`: Core discrete-event loop
3. `backend/tasks.py`: Celery task definitions, config adapters
4. `backend/api/endpoints.py`: FastAPI routes
5. `backend/api/models.py`: Pydantic schemas (request/response validation)

### Frontend
1. `frontend/src/App.jsx`: Routing, global layout
2. `frontend/src/pages/SimulationScene.jsx`: City canvas, live demo
3. `frontend/src/pages/ResultsDashboard.jsx`: KPI cards, charts, drill-down
4. `frontend/src/pages/ScenarioSubmission.jsx`: Form for scenario input
5. `frontend/docs/ui-style-contract.md`: UI/motion rulebook

### Infrastructure
1. `docker-compose.yml`: Service definitions (5 containers)
2. `digital-twin/docker/postgres/init.sql`: DB schema
3. `backend/requirements.txt`: Python dependencies
4. `frontend/package.json`: Node dependencies

---

## 💡 Questions for Brainstorming

Use this document to kickstart discussions with ChatGPT (or a team) on:
1. **Feature prioritization**: Which of the "What's Next" items delivers most value?
2. **Architecture improvements**: Should we switch to WebSockets? Add GraphQL?
3. **Data strategy**: How to acquire real EV fleet data for calibration?
4. **UI/UX refinement**: What else can we visualize without overloading the user?
5. **Business model**: Who pays for this? SaaS subscription? Per-simulation pricing?
6. **Scale planning**: How to handle 1000 concurrent simulations? Kubernetes? Serverless?
7. **Testing strategy**: What's the MVP test suite (unit, integration, E2E)?
8. **Go-to-market**: Which city/fleet operator to pilot with first?

---

## 🏁 Summary

**Current State**: We have a fully functional MVP for running discrete-event simulations of EV swapping networks, with a modern React UI that visualizes scenarios, monitors jobs, and reveals KPIs on demand. The backend is async/scalable (Celery + Redis), the frontend is polished (UI style contract, reduced-motion, progressive disclosure), and the core simulation engine produces meaningful metrics (wait time, utilization, ROI).

**What Works**: End-to-end scenario submission → async processing → result visualization. UI feels production-grade (no decorative fluff, motion with meaning, glassmorphism only on overlays).

**What's Missing**: Real geography, historical data calibration, scenario comparison, authentication, mobile responsiveness, observability, testing.

**Ready For**: Internal pilot with 1–2 city planning teams, feedback iteration, roadmap refinement.

---

**End of Document**
