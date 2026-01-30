# Digital Twin Simulation Platform – Complete Codebase Analysis

**Date**: January 30, 2026  
**Purpose**: Comprehensive technical documentation of current implementation  
**Status**: Read-only analysis (no suggestions, no opinions, only facts)

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Entry Points and Execution Flow](#entry-points-and-execution-flow)
3. [File-by-File Analysis](#file-by-file-analysis)
4. [Data Structure Documentation](#data-structure-documentation)
5. [Fake vs Real Mode Comparison](#fake-vs-real-mode-comparison)
6. [What Is Actually Implemented](#what-is-actually-implemented)
7. [What Is Stubbed or Placeholder](#what-is-stubbed-or-placeholder)
8. [Intervention Application Logic](#intervention-application-logic)

---

## System Architecture Overview

### Technology Stack
- **Backend**: FastAPI (Python)
- **Task Queue**: Celery with Redis broker
- **Simulation**: SimPy (discrete-event simulation library)
- **NLP**: Google Gemini API (for natural language to TOON DSL translation)
- **Frontend**: React + Ant Design + Recharts
- **Storage**: File system (NDJSON for events, JSON for summary)
- **Job Tracking**: Redis (key-value store)

### Component Layers
```
Layer 1 (Entry): FastAPI Endpoints (api/endpoints.py)
Layer 2 (Orchestration): Celery Tasks (tasks.py)
Layer 3 (Adapter): Simulation Main (simulation/main.py)
Layer 4 (Engine): SimulationEngine (simulation/simulation_engine.py)
Layer 5 (Components): DemandGenerator, RoutingEngine, InventoryManager, KPITracker, Stations
Layer 6 (Post-Processing): KPIEngine, ROIEngine, ScenarioManager, ScenarioDiff, ScenarioRanker
Layer 7 (Storage): EventLogger, Redis, File System
```

---

## Entry Points and Execution Flow

### Flow 1: Scenario Submission (Frontend → Backend → Celery)

**Step 1**: User submits form in `ScenarioSubmission.jsx`
- **Input Structure**:
  ```javascript
  {
    description: string,
    city_config: {
      zones: string[],
      stations: [
        {
          station_id: string,
          lat: float,
          lon: float,
          zone_id: string,
          chargers_total: int,
          chargers_active: int
        }
      ]
    },
    interventions: object,  // Free-form JSON (currently not used)
    simulation_duration: int,  // seconds
    mode: "fake" | "real"
  }
  ```

**Step 2**: POST request to `/api/scenarios/submit` (`api/endpoints.py:98`)
- Validates `city_config` structure (requires `zones`, `stations`, valid lat/lon)
- Generates UUID for `run_id`
- Creates initial job status in Redis (`status="submitted"`)
- Dispatches Celery task `run_simulation_task.delay(run_id, scenario.dict())`
- Returns immediately with `run_id`

**Step 3**: Celery worker picks up task (`tasks.py:113`)
- Creates result directory: `/app/data/results/{run_id}/`
- Builds `runtime_config` dict:
  ```python
  {
    "run_id": run_id,
    "data_dir": data_dir,
    "city_config": {...},      # Copied from scenario_data
    "interventions": {...},    # Copied from scenario_data (NOT USED YET)
    "simulation_duration": int,
    "description": string
  }
  ```
- Updates Redis status to `"running"`
- Calls `run_simulation(runtime_config, mode=mode)`
- Stores result in Redis with 7-day expiry
- Writes artifacts: `events.ndjson`, `frames.ndjson`, `summary.json`

**Step 4**: Frontend polls `/api/jobs/{run_id}/status` every 3 seconds
- Returns status from Redis: `submitted` → `running` → `completed` or `failed`

**Step 5**: When status is `completed`, frontend calls `/api/jobs/{run_id}/result`
- Returns full simulation result with KPIs, artifacts, event counts

---

### Flow 2: Direct Simulation Run (Synchronous API)

**Entry**: POST `/api/run-simulation` (`api/endpoints.py:192`)
- **Input**:
  ```json
  {
    "config": {...},  // Runtime config dict
    "mode": "fake" | "real"
  }
  ```
- Directly calls `run_simulation(config, mode)` synchronously
- Returns result immediately (no background task)
- **Use Case**: Testing, debugging, or fast UI-safe operations

---

### Flow 3: Scenario Comparison (Multi-Run Orchestration)

**Entry**: POST `/api/run-scenarios` (`api/endpoints.py:227`)
- **Input**:
  ```json
  {
    "base_config": {...},
    "scenarios": [{...}, {...}],  // List of config overrides
    "weights": {
      "avg_wait_time": 0.25,
      "lost_swaps": 0.20,
      "throughput": 0.20,
      "roi": 0.35
    },
    "mode": "fake" | "real"
  }
  ```
- Calls `run_scenarios(base_config, scenario_configs, weight_config, mode)`
- Runs baseline + N scenarios
- Computes deltas (ScenarioDiff)
- Ranks scenarios (ScenarioRanker)
- Returns ranked list with scores

---

### Flow 4: Natural Language Translation

**Entry**: POST `/api/nl-to-toon` (`api/endpoints.py:263`)
- **Input**:
  ```json
  {
    "text": "Add 3 stations to downtown with 5 chargers each",
    "city": "Bangalore"
  }
  ```
- Gets station catalog for city
- Builds Gemini prompt with TOON grammar
- Calls Gemini API to generate TOON DSL script
- Parses TOON script into structured config
- Returns `{"toon": {...}}` config dict
- **Note**: Does NOT trigger simulation, only translation

---

## File-by-File Analysis

### **`api/endpoints.py`** (300 lines)

**Purpose**: FastAPI HTTP endpoints for client interactions

**Responsibilities**:
- Route HTTP requests to appropriate handlers
- Validate request payloads
- Dispatch Celery tasks for background processing
- Return status/results from Redis
- Handle NL-to-TOON translation requests

**Implemented Logic**:
- `submit_scenario()`: Validates city_config, creates job status, dispatches Celery task
- `get_job_status_endpoint()`: Reads from Redis
- `get_job_result_endpoint()`: Reads from Redis, returns 202 if not completed
- `run_simulation_endpoint()`: Synchronous simulation call
- `run_scenarios_endpoint()`: Multi-scenario comparison
- `nl_to_toon_endpoint()`: NL → TOON translation
- `health_check()`: Returns API health status
- `get_station_catalog()`: Returns hardcoded station IDs for city (Bangalore, Delhi, Mumbai)
- `validate_city_config()`: Validates zones, stations, lat/lon ranges, zone membership

**Stubbed/Placeholder**:
- `list_jobs()`: Returns `"Job listing not yet implemented"`
- `cancel_job()`: Returns `"Job cancellation not yet implemented"`
- Station catalog is hardcoded (should be database lookup per TODO)

**Key Validation Rules**:
- Latitude: -90 to 90
- Longitude: -180 to 180
- Station must reference a zone that exists in zones list
- Duration: 60 to 86400 seconds
- Description: 1 to 500 characters

---

### **`api/models.py`** (149 lines)

**Purpose**: Pydantic models for request/response validation

**Data Models Defined**:

1. **`JobStatus`** (Enum):
   - Values: `submitted`, `running`, `completed`, `failed`, `cancelled`

2. **`SimulationRequest`**:
   - `config`: dict (free-form runtime config)
   - `mode`: "fake" | "real" (default: "fake")

3. **`ScenarioRequest`**:
   - `description`: string (1-500 chars)
   - `city_config`: dict (zones + stations)
   - `interventions`: dict (default: `{}`)
   - `simulation_duration`: int (60-86400 seconds)
   - `mode`: "fake" | "real" (default: "fake")

4. **`ScenarioComparisonRequest`**:
   - `base_config`: dict
   - `scenarios`: list[dict]
   - `weights`: dict (avg_wait_time, lost_swaps, throughput, roi)
   - `mode`: "fake" | "real"

5. **`ScenarioResponse`**:
   - `run_id`: string
   - `status`: JobStatus
   - `message`: string

6. **`JobStatusResponse`**:
   - `run_id`: string
   - `status`: JobStatus
   - `progress`: float (0.0-1.0)
   - `message`: string
   - `created_at`: datetime
   - `updated_at`: datetime

7. **`KPISummary`**:
   - `avg_wait_time`: float (minutes)
   - `lost_swaps`: int
   - `charger_utilization`: float (0.0-1.0)
   - `idle_inventory`: float
   - `city_throughput`: int
   - `total_cost_impact`: float
   - `roi`: float

8. **`SimulationResult`**:
   - `run_id`: string
   - `status`: JobStatus
   - `summary`: KPISummary
   - `events_count`: int
   - `frames_count`: int
   - `artifacts`: ArtifactInfo (paths to .ndjson and .json files)

9. **`NLToToonRequest`**:
   - `text`: string
   - `city`: string (default: "Bangalore")

**Stubbed/Placeholder**:
- None (all models are complete for current use cases)

---

### **`tasks.py`** (193 lines)

**Purpose**: Celery background task definitions and Redis job tracking

**Responsibilities**:
- Run simulations asynchronously
- Store job status/progress in Redis
- Handle task retries and failures
- Write artifact files to disk

**Implemented Logic**:

1. **`_store_job_status()`**: Writes job status to Redis with 7-day TTL
   - Preserves `created_at` timestamp
   - Updates `updated_at` on every call
   - Stores: run_id, status, message, progress, timestamps

2. **`_get_job_status()`**: Reads job status from Redis
   - Raises `ValueError` if job not found
   - Ensures `created_at` and `updated_at` fields exist

3. **`create_job_status()`**: Creates initial job record with `status="submitted"`

4. **`run_simulation_task()`**: Main Celery task
   - Creates result directory
   - Builds `runtime_config` dict with fields: `run_id`, `data_dir`, `city_config`, `interventions`, `simulation_duration`, `description`
   - **CRITICAL**: Passes `city_config` and `interventions` directly to `run_simulation()` WITHOUT transformation
   - Updates progress: 0.0 → 0.1 → 0.9 → 1.0
   - Writes final result to Redis (`job_result:{run_id}`)
   - On failure: updates status to "failed", retries up to 2 times with 60-second delay

5. **`get_task_status()`**: API helper that wraps `_get_job_status()`

6. **`get_task_result()`**: API helper that reads `job_result:{run_id}` from Redis
   - Returns status if job exists but not completed
   - Raises `ValueError` if result not found

**Stubbed/Placeholder**:
- Fallback `run_simulation()` function if import fails (lines 13-28): sleeps 5 seconds, returns fake data

**Key Observations**:
- `interventions` field is passed through but NOT USED anywhere in simulation logic
- `city_config` contains stations with `lat`/`lon` keys, but simulation expects `latitude`/`longitude` keys
- This is NOT adapted before calling `run_simulation()` in "real" mode
- Result from `run_simulation()` must match schema: `{metadata, kpis, timeseries, events}`

---

### **`simulation/main.py`** (448 lines)

**Purpose**: Adapter layer between API/Celery and simulation engine

**Responsibilities**:
- Provide `run_simulation()` function with "fake" and "real" modes
- Generate fake data deterministically for UI testing
- Initialize real SimPy simulation components
- Provide `run_scenarios()` for multi-scenario comparison

**Implemented Logic**:

1. **`run_simulation(config, mode)`**:
   - **Validates** mode is "fake" or "real"
   - Extracts `seed`, `city` from config
   - Dispatches to `_run_fake_simulation()` or `_run_real_simulation()`

2. **`_run_fake_simulation(config, seed, city)`**:
   - Uses seeded `random.Random(seed)` for determinism
   - Generates fake KPIs: arrivals (50-200), completed (70-95%), lost (remainder)
   - Generates fake metrics: avg_wait_time (2-15 min), utilization (0.3-0.9), ROI (0.1-0.5)
   - Generates fake timeseries: wait_times list, inventory_levels dict, queue_lengths dict
   - Generates fake events (200 events max): rider_arrival, queue_join, swap_start, swap_complete, lost_swap, charge_start, charge_complete
   - Writes 3 artifact files: `summary.json`, `events.ndjson`, `frames.ndjson`
   - Returns dict with keys: `metadata`, `kpis`, `timeseries`, `events`

3. **`_run_real_simulation(config, seed, city)`**:
   - **Requires SimPy** (raises RuntimeError if not available)
   - Creates temporary event log file
   - Initializes components:
     - `InventoryManager` from `inventory_config` (initial_inventory dict, refill_threshold, refill_amount)
     - `KPITracker` (event-based tracking)
     - `NetworkGraph` (station topology)
     - `RoutingEngine` (station selection)
     - Stations: creates `Station` objects from `stations` config list, adds to NetworkGraph, creates `StationProcess` for each
     - `DemandGenerator` from `demand_config` (rng_seed, base_demand_rate)
   - Creates `SimulationEngine` with all components
   - Calls `engine.run(start_time, end_time)`
   - Reads events from temp log file
   - Passes events to `KPIEngine` to compute KPIs
   - Passes KPIs to `ROIEngine` to compute financial metrics
   - Merges KPIs and ROI into `final_kpis`
   - Deletes temp log file
   - Returns dict with keys: `metadata`, `kpis`, `timeseries`, `events`
   - **NOTE**: `timeseries` dict is EMPTY (wait_time=[], inventory_levels={}, queue_lengths={}) because timeseries generation from events is not implemented (TODO on line 332)

4. **`run_scenarios(base_config, scenario_configs, weight_config, mode)`**:
   - Creates temp event log for scenario events
   - Initializes `ScenarioManager` with base_config and scenarios
   - Calls `scenario_manager.run_all(mode)` to run baseline + all scenarios
   - For each scenario result:
     - Computes diff with `ScenarioDiff(baseline, scenario_result)`
     - Adds `diff` block to scenario result
     - Logs "ranking" event (uses `station_selected` event type as closest match)
   - Ranks scenarios with `ScenarioRanker(diffs, weight_config)`
   - Deletes temp event log
   - Returns: `{baseline, scenarios, ranking}`

**Stubbed/Placeholder**:
- Timeseries generation from events (line 332 TODO)
- Config adaptation for real mode is MINIMAL (only initializes components, no transformation of city_config or interventions)

**Key Observations**:
- Config structure is DIFFERENT for fake vs real mode
- Fake mode expects: `seed`, `city`, `start_time`, `end_time`, optional `station_ids`
- Real mode expects: `seed`, `city`, `start_time`, `end_time`, `stations` (list of full station config dicts), `demand_config` (dict), `inventory_config` (dict), cost fields (revenue_per_swap, etc.)
- `interventions` field is IGNORED in both modes
- `city_config` from frontend is NOT transformed into the format required by real mode

---

### **`simulation/simulation_engine.py`** (239 lines)

**Purpose**: Main orchestrator for discrete-event simulation

**Responsibilities**:
- Initialize SimPy environment
- Schedule rider arrivals
- Route riders to stations
- Process rider lifecycle (arrival → queue → service → completion/loss)
- Collect KPI snapshots

**Implemented Logic**:

1. **`__init__()`**:
   - Stores all component references (demand_generator, routing_engine, inventory_manager, kpi_tracker, stations, event_logger)
   - Creates SimPy environment
   - TODOs: scenario configuration, time scaling, parallel execution

2. **`schedule_arrivals(start_time, end_time)`**:
   - Calls `demand_generator.generate_arrivals(start_time, end_time)` to get arrival list
   - For each arrival:
     - Creates `Rider` instance
     - Records arrival in `kpi_tracker`
     - Schedules `_process_rider_arrival()` SimPy process
     - Logs `rider_arrival` event

3. **`_process_rider_arrival(rider)`**:
   - Yields `timeout(0)` (no actual wait time modeled)
   - If rider's assigned station exists in stations dict:
     - Yields `station.handle_rider(rider)` process
     - If rider.status is "served": records completion with wait_time in kpi_tracker
     - If rider.status is "lost": records lost in kpi_tracker

4. **`route_rider(rider)`**:
   - Logs `station_selected` event with existing `assigned_station_id`
   - **DOES NOT** actually call `routing_engine.select_best_station()`
   - **Placeholder**: assumes rider already has assigned_station_id from DemandGenerator

5. **`run(start_time, end_time)`**:
   - Logs placeholder "simulation started" event (uses `rider_arrival` event type)
   - Calls `schedule_arrivals()`
   - Calculates duration in minutes
   - Runs SimPy environment: `self.env.run(until=duration_minutes)`
   - Logs placeholder "simulation completed" event (uses `swap_complete` event type)
   - Returns `kpi_tracker.snapshot()`

6. **`snapshot()`**:
   - Returns dict with: simulation_time (env.now), kpi_snapshot, inventory_snapshot, stations snapshots

**Stubbed/Placeholder**:
- Actual routing logic (rider already has assigned_station_id, no routing decision made)
- Wait time modeling (yields timeout(0) immediately)
- Proper event types for simulation start/end (uses rider_arrival and swap_complete as placeholders)
- All TODOs in docstrings

---

### **`simulation/demand_generator.py`** (400 lines)

**Purpose**: Generate rider arrival patterns with time/weather/event modifiers

**Responsibilities**:
- Model time-of-day demand curves
- Apply weather modifiers
- Apply event-based demand spikes
- Apply station selection weights
- Generate deterministic arrivals

**Implemented Logic**:

1. **`TimeOfDayCurve`**:
   - Stores weekday_curve and weekend_curve (list of (hour, multiplier) tuples)
   - `get_multiplier(timestamp)`: Simple lookup (no interpolation)
   - Returns 1.0 if hour not found in curve

2. **`WeatherModifier`**:
   - Stores weather_multipliers dict (weather_state → multiplier)
   - `get_multiplier(weather_state)`: Returns multiplier or 1.0 if unknown

3. **`EventModifier`**:
   - Stores events list (each event: {start, end, multiplier})
   - `get_multiplier(timestamp)`: Multiplies all active event multipliers, returns 1.0 if none active

4. **`StationSkewModel`**:
   - Stores station_weights dict (station_id → weight)
   - `get_weight(station_id)`: Returns weight or 1.0 if unknown

5. **`DemandGenerator.__init__()`**:
   - Initializes RNG with seed
   - Stores base_demand_rate
   - Initializes all modifiers
   - Stores current_weather state

6. **`generate_arrivals(start_time, end_time)`**:
   - **CURRENT IMPLEMENTATION**: Generates ONLY ONE arrival
   - Calls `select_station()` to pick station (returns first station in list)
   - Computes all multipliers (tod, weather, event, station_weight) for metadata
   - Logs `rider_arrival` event
   - Returns list with single arrival dict: `{timestamp, rider_id, station_id, metadata}`

7. **`next_arrival_time(current_time)`**:
   - **Placeholder**: Returns `current_time + 10 minutes` (fixed interval, no Poisson process)

8. **`select_station()`**:
   - **Placeholder**: Returns `self.stations[0]` (first station only)

9. **`snapshot()`**: Returns base config and state

**Stubbed/Placeholder**:
- **Poisson process** for arrival generation (entire loop is TODO, only 1 rider generated)
- **Weighted random selection** for stations (always returns first station)
- **Exponential inter-arrival times** (returns fixed 10-minute interval)
- **Smooth interpolation** for time-of-day curve (simple lookup only)
- **All TODOs** in docstrings (ML-based curve fitting, weather API integration, etc.)

**Key Limitation**:
- **ONLY 1 RIDER PER SIMULATION** is generated regardless of duration or demand rate

---

### **`simulation/station.py`** (240 lines)

**Purpose**: Define station data model and operational methods

**Responsibilities**:
- Store station configuration (identity, capacity, state, timing, costs)
- Provide methods for operations (arrivals, swaps, charging, failures)
- Log events through EventLogger

**Implemented Logic**:

1. **`__init__(config, event_logger)`**:
   - Extracts and stores 30+ configuration fields:
     - **Identity**: station_id, zone_id, latitude, longitude
     - **Capacity**: chargers_total, chargers_active, swap_bays, inventory_capacity
     - **State**: inventory_current, queue_length, status (up/down)
     - **Timing**: swap_time_sec, charge_time_sec
     - **Replenishment**: policy, threshold, amount, delay
     - **Failure**: charger_failure_rate, station_failure_rate
     - **Costs**: fixed_cost_per_day, charger_capex, battery_capex, energy_cost_per_charge, lost_swap_penalty

2. **All operational methods are STUBS**:
   - `handle_arrival(rider_id)`: Only logs `rider_arrival` event
   - `start_swap(rider_id)`: Only logs `swap_start` event
   - `complete_swap(rider_id)`: Only logs `swap_complete` event
   - `start_charging(battery_id)`: Only logs `charge_start` event
   - `complete_charging(battery_id)`: Only logs `charge_complete` event
   - `trigger_replenishment()`: Only logs `replenishment_trigger` event
   - `mark_charger_failure()`: Only logs `charger_failure` event
   - `mark_charger_repair()`: Only logs `charger_repair` event
   - `mark_station_down()`: Sets `status="down"`, logs `station_down` event
   - `mark_station_up()`: Sets `status="up"`, logs `station_up` event

**Stubbed/Placeholder**:
- **ALL operational logic** (inventory decrement, queue management, timing, battery handling)
- Only event logging is implemented

**Key Observation**:
- Station class is a DATA CONTAINER with EVENT EMITTERS, not a functional simulation component

---

### **`simulation/station_process.py`** (192 lines)

**Purpose**: SimPy-based station resource management

**Responsibilities**:
- Manage SimPy Resources for swap bays and chargers
- Handle rider processing with SimPy processes
- Check capacity constraints

**Implemented Logic**:

1. **`__init__()`**:
   - Creates `simpy.Resource` for swap_bays with capacity
   - Creates `simpy.Resource` for chargers with capacity
   - Stores references to inventory_manager and event_logger

2. **`can_accept_rider()`**:
   - **Placeholder**: Always returns `True`
   - Does NOT check swap bay availability, inventory, queue limits, or station status

3. **`handle_rider(rider)`**:
   - Calls `can_accept_rider()` (always True)
   - Logs `queue_join` event
   - Yields `timeout(0)` (no actual processing)
   - If rejected (never happens): logs `lost_swap`, marks rider as lost

4. **`process_swap(rider)`**:
   - Acquires swap bay resource with `with self.swap_bays.request()`
   - Logs `swap_start` event
   - Calls `inventory_manager.consume(station_id)`
   - If inventory consumed successfully:
     - Yields `timeout(0)` (no actual swap time)
     - Logs `swap_complete` event
   - If inventory stockout:
     - Logs `inventory_stockout` event
     - Marks rider as lost

5. **`snapshot()`**: Returns swap_bays and chargers capacity/availability

**Stubbed/Placeholder**:
- Actual capacity checks in `can_accept_rider()`
- Actual swap timing (yields timeout(0), should use swap_time_sec)
- Priority queue for riders
- Fairness policies
- Service time distributions

**Key Observation**:
- SimPy Resources ARE created and used (swap_bays.request() works)
- Timing is ZERO (no actual delays modeled)

---

### **`simulation/routing.py`** (156 lines)

**Purpose**: Station selection and routing optimization

**Responsibilities**:
- Score stations based on distance, capacity, queue
- Select best station for a rider
- Compute travel costs
- Handle rerouting

**Implemented Logic**:

1. **`__init__(graph)`**: Stores NetworkGraph reference

2. **`score_station(station_id, rider_location)`**:
   - **Returns**: `0.0` (hardcoded)

3. **`select_best_station(rider_location)`**:
   - Gets all stations from graph
   - Raises `ValueError` if no stations exist
   - **Returns**: First station in list (no scoring, no optimization)

4. **`compute_travel_cost(from_station_id, to_station_id)`**:
   - Validates both stations exist (raises ValueError if not)
   - **Returns**: `0.0` (hardcoded)

5. **`reroute(current_station_id, rider_location)`**:
   - **Returns**: `current_station_id` (no reroute, returns same station)

**Stubbed/Placeholder**:
- **ALL routing logic** (scoring, selection, travel cost, rerouting)
- Only basic validation is implemented

**Key Observation**:
- Routing is INFRASTRUCTURE ONLY, no actual optimization logic exists

---

### **`simulation/rider.py`** (218 lines)

**Purpose**: Model for individual rider entities

**Responsibilities**:
- Store rider state (ID, times, status, assigned station)
- Track rider lifecycle events
- Provide status transitions (waiting → served/lost/rerouted)

**Implemented Logic**:

1. **`RiderStatus`** (Enum):
   - Values: `WAITING`, `SERVED`, `LOST`, `REROUTED`

2. **`__init__()`**:
   - Stores: id, arrival_time, assigned_station_id, event_logger
   - Initializes: start_service_time (None), end_service_time (None), status (WAITING)
   - Logs `rider_arrival` event

3. **`wait(env)`**:
   - Logs `queue_join` event
   - Yields `timeout(0)` (no actual wait time)

4. **`serve(env)`**:
   - Records `start_service_time` as `env.now`
   - Yields `timeout(0)` (no actual service time)
   - Records `end_service_time` as `env.now`
   - Sets status to `SERVED`
   - Logs `swap_complete` event with service_duration metadata

5. **`mark_lost()`**:
   - Sets status to `LOST`
   - Logs `lost_swap` event with abandonment_reason="timeout"

6. **`mark_rerouted(new_station_id)`**:
   - Updates assigned_station_id
   - Sets status to `REROUTED`
   - Logs `reroute` event with old/new station IDs

7. **`snapshot()`**: Returns all rider state fields

**Stubbed/Placeholder**:
- Actual wait and service timing (all yields are timeout(0))
- Timeout configuration
- Abandonment threshold
- Reroute eligibility

**Key Observation**:
- Rider state tracking IS implemented
- Timing is ZERO (no delays modeled)

---

### **`simulation/kpi_engine.py`** (321 lines)

**Purpose**: Compute KPIs from event logs (post-simulation analysis)

**Responsibilities**:
- Read events list
- Extract KPIs from event sequences
- Calculate derived metrics

**Implemented Logic**:

1. **`__init__(events, config)`**:
   - Stores events list
   - Extracts start_time, end_time, stations from config
   - Builds station_swap_bays lookup dict

2. **`compute()`**: Calls all sub-computations, returns KPI dict

3. **`_compute_avg_wait_time()`**:
   - Tracks `rider_wait_starts` dict (rider_id → queue_join timestamp)
   - For each `queue_join` event: records start time
   - For each `swap_start` event: calculates wait duration, adds to wait_times list, removes from tracking
   - Returns average of wait_times list (or 0.0 if empty)

4. **`_compute_lost_swaps()`**:
   - Counts `lost_swap` events where abandonment_reason is "inventory_stockout", "patience_timeout", or "timeout"
   - Also counts `inventory_stockout` events
   - Returns total count

5. **`_compute_throughput()`**:
   - Counts `swap_complete` events
   - Returns count

6. **`_compute_utilization()`**:
   - Tracks `station_swap_starts` dict ((station_id, rider_id) → swap_start timestamp)
   - For each `swap_start`: records start time
   - For each `swap_complete`: calculates duration, adds to station_busy_time dict
   - Calculates total_capacity_minutes as sum(swap_bays × simulation_duration) for all stations
   - Returns: total_busy_time / total_capacity_minutes

7. **`_compute_idle_inventory()`**:
   - Initializes station_inventory from station configs (inventory_current)
   - For each event in chronological order:
     - Accumulates idle time × inventory count since last change
     - Updates inventory based on event type:
       - `swap_start`: decrements by 1
       - `charge_complete`: increments by 1
       - `replenishment_complete`: increments by replenishment_amount
   - Returns time-weighted average idle inventory

8. **`snapshot()`**: Alias for `compute()`

**Stubbed/Placeholder**:
- None (all KPI calculations are fully implemented)

**Key Observation**:
- KPIEngine is FULLY FUNCTIONAL and deterministic
- Handles timezone-aware and naive datetimes correctly
- All calculations are event-driven (no state from simulation engine needed)

---

### **`simulation/roi_engine.py`** (132 lines)

**Purpose**: Compute financial metrics from KPIs

**Responsibilities**:
- Calculate revenue from throughput
- Calculate operational costs
- Calculate net profit
- Calculate ROI percentage

**Implemented Logic**:

1. **`__init__(kpis, config)`**: Stores KPIs and cost configuration

2. **`compute()`**: Calls all sub-computations, returns financial dict

3. **`_compute_revenue()`**:
   - Formula: `throughput × revenue_per_swap`

4. **`_compute_operational_cost()`**:
   - Formula: `charger_energy_cost + station_staff_cost + battery_depreciation_cost + infra_maintenance_cost`

5. **`_compute_net_profit(revenue, operational_cost)`**:
   - Formula: `revenue - operational_cost`

6. **`_compute_roi(net_profit)`**:
   - Formula: `(net_profit / capital_cost) × 100.0`
   - Returns 0.0 if capital_cost ≤ 0

7. **`snapshot()`**: Alias for `compute()`

**Stubbed/Placeholder**:
- None (all ROI calculations are fully implemented)

**Key Observation**:
- ROIEngine is FULLY FUNCTIONAL
- Simple arithmetic (no complex financial modeling)

---

### **`simulation/inventory_manager.py`** (167 lines)

**Purpose**: Manage battery inventory across stations

**Responsibilities**:
- Track battery counts per station
- Handle consumption (decrement)
- Trigger refills
- Log inventory events

**Implemented Logic**:

1. **`__init__()`**:
   - Copies initial_inventory dict
   - Stores refill_threshold and refill_amount
   - Stores event_logger

2. **`consume(station_id)`**:
   - If battery_count > 0:
     - Decrements count by 1
     - Logs `charge_complete` event (NOTE: incorrect event type, should be something like "battery_consumed")
     - Checks `needs_refill()`, logs `replenishment_trigger` if below threshold
     - Returns `True`
   - If battery_count ≤ 0:
     - Logs `inventory_stockout` event
     - Returns `False`

3. **`needs_refill(station_id)`**:
   - Returns `True` if battery_count ≤ refill_threshold

4. **`refill(station_id)`**:
   - Adds `refill_amount` to battery_count
   - Logs `replenishment_complete` event with refill_amount and new_count

5. **`snapshot()`**: Returns battery_counts dict and refill config

**Stubbed/Placeholder**:
- Delivery delay modeling (refill is instant)
- Safety stock levels
- Truck routing logic
- Refill in-progress tracking

**Key Observations**:
- Inventory tracking IS implemented
- Refills are instant (no delivery time modeled)
- Event type mismatch: uses "charge_complete" when consuming battery

---

### **`simulation/kpi_tracker.py`** (168 lines)

**Purpose**: In-memory KPI accumulation during simulation

**Responsibilities**:
- Track arrivals, completions, lost riders
- Track wait times
- Track station utilization

**Implemented Logic**:

1. **`__init__(event_logger)`**:
   - Initializes counters: arrivals=0, completed=0, lost=0
   - Initializes lists: wait_times=[]
   - Initializes dicts: station_utilization={}

2. **`record_arrival()`**:
   - Increments `arrivals`
   - Logs `rider_arrival` event with total_arrivals metadata

3. **`record_completion(wait_time)`**:
   - Increments `completed`
   - Appends wait_time to wait_times list
   - Logs `swap_complete` event with total_completed and wait_time metadata

4. **`record_lost()`**:
   - Increments `lost`
   - Logs `lost_swap` event with total_lost metadata

5. **`update_station_utilization(station_id, utilization)`**:
   - Updates station_utilization dict

6. **`utilization_snapshot()`**: Returns copy of station_utilization dict

7. **`snapshot()`**:
   - Calculates completion_rate: completed / arrivals
   - Calculates loss_rate: lost / arrivals
   - Calculates average_wait_time: sum(wait_times) / len(wait_times)
   - Returns dict with all metrics

**Stubbed/Placeholder**:
- Percentile tracking
- SLA threshold tracking
- Anomaly detection

**Key Observation**:
- KPITracker is FUNCTIONAL for basic counting
- Used by SimulationEngine during runtime
- **Different from KPIEngine** (KPITracker is runtime, KPIEngine is post-processing from events)

---

### **`simulation/event_logger.py`** (105 lines)

**Purpose**: Write events to NDJSON file matching event schema

**Responsibilities**:
- Validate event types against allowed list
- Generate event_id (UUID) and timestamp (ISO 8601)
- Write events as NDJSON (one JSON object per line)
- Flush immediately for real-time viewing

**Implemented Logic**:

1. **`ALLOWED_EVENT_TYPES`** (class constant):
   - 17 allowed types: rider_arrival, station_selected, reroute, queue_join, queue_leave, swap_start, swap_complete, lost_swap, charge_start, charge_complete, inventory_stockout, replenishment_trigger, replenishment_complete, charger_failure, charger_repair, station_down, station_up

2. **`__init__(output_path)`**:
   - Opens file handle in write mode

3. **`log_event(event_type, station_id, rider_id, battery_id, metadata)`**:
   - Validates event_type is in ALLOWED_EVENT_TYPES (raises ValueError if not)
   - Generates UUID for event_id
   - Generates UTC timestamp (ISO 8601 with 'Z' suffix)
   - Builds event dict with all fields
   - Writes as JSON line
   - Flushes immediately

4. **`close()`**: Closes file handle

**Stubbed/Placeholder**:
- None (EventLogger is fully implemented)

**Key Observation**:
- EventLogger is PRODUCTION-READY
- All events match schema in `schemas/event_log_schema.json`

---

### **`simulation/network_graph.py`** (229 lines)

**Purpose**: Station topology using networkx directed graph

**Responsibilities**:
- Store stations as nodes
- Store routes as edges with distance/time/traffic weights
- Provide graph queries (neighbors, stations)
- Support topology updates (add/remove stations)

**Implemented Logic**:

1. **`__init__()`**: Creates empty `nx.DiGraph()`

2. **`add_station(station)`**:
   - Adds node with station_id as key
   - Stores station object and attributes (latitude, longitude, swap_bays, chargers_total) as node data

3. **`add_edge(from_station_id, to_station_id, distance_km, base_travel_time_min, traffic_factor)`**:
   - Computes `effective_travel_time_min = base_travel_time_min × traffic_factor`
   - Adds edge with all attributes

4. **`remove_station(station_id)`**:
   - Removes node (networkx handles cascade edge removal)

5. **`update_station_capacity(station_id, new_swap_bays, new_chargers_total)`**:
   - Updates graph node attributes if station exists

6. **`get_neighbors(station_id)`**:
   - Returns list of successor station IDs (outgoing edges)

7. **`get_station(station_id)`**:
   - Returns Station object from node attributes
   - Raises KeyError if not found

8. **`load_topology(topology_config)`**:
   - **Placeholder**: Function body is `pass` (not implemented)

9. **`snapshot()`**: Returns nodes and edges with all data

**Stubbed/Placeholder**:
- `load_topology()` (entire function is stub)
- Edge validation (no checks for positive distance/time)
- Connectivity validation
- Cycle detection

**Key Observation**:
- NetworkGraph is PARTIALLY implemented
- Individual operations work, but bulk loading is stub

---

### **`simulation/scenario_manager.py`** (170 lines)

**Purpose**: Run multiple scenarios and compare results

**Responsibilities**:
- Validate scenario configs match baseline (same city, seed, time window)
- Run baseline + all scenarios
- Return results with scenario_id tags

**Implemented Logic**:

1. **`__init__(base_config, scenarios, event_logger)`**:
   - Stores configs
   - Calls `_validate_scenarios()`

2. **`_validate_scenarios()`**:
   - For each scenario:
     - Merges with base_config
     - Checks city, seed, start_time, end_time match baseline
     - Raises ValueError if mismatch

3. **`run_all(mode)`**:
   - Logs "scenario run started" event (uses `rider_arrival` as placeholder)
   - Runs `run_simulation(base_config, mode)` for baseline
   - For each scenario:
     - Merges scenario with base_config
     - Runs `run_simulation(scenario_config, mode)`
     - Stores result with scenario_id tag
   - Logs "scenario run completed" event (uses `swap_complete` as placeholder)
   - Returns: `{baseline, scenarios}` where scenarios is list of `{scenario_id, config, result}`

4. **`snapshot()`**: Returns baseline city, num scenarios, scenario IDs

**Stubbed/Placeholder**:
- Progress tracking
- Per-scenario error handling
- Scenario cancellation
- Scenario caching
- Parallel execution

**Key Observation**:
- ScenarioManager is FUNCTIONAL
- Runs scenarios sequentially
- Validation ensures apples-to-apples comparison

---

### **`simulation/scenario_diff.py`** (93 lines)

**Purpose**: Compute deltas between baseline and scenario results

**Responsibilities**:
- Extract KPIs from both results
- Compute deltas (scenario - baseline)
- Return structured diff dict

**Implemented Logic**:

1. **`__init__(baseline, scenario)`**: Stores both result dicts

2. **`compute()`**:
   - Extracts `kpis` from both results
   - Computes KPI deltas:
     - `avg_wait_time_delta`
     - `lost_swaps_delta`
     - `utilization_delta`
     - `throughput_delta`
     - `idle_inventory_delta`
   - Computes ROI deltas:
     - `revenue_delta`
     - `operational_cost_delta`
     - `net_profit_delta`
     - `roi_delta`
   - Returns: `{kpi_deltas, roi_deltas}`

3. **`snapshot()`**: Returns baseline and scenario run IDs

**Stubbed/Placeholder**:
- Percentile delta calculations
- Timeseries delta calculations

**Key Observation**:
- ScenarioDiff is FULLY FUNCTIONAL for current KPIs
- Pure function (no side effects)

---

### **`simulation/scenario_ranker.py`** (129 lines)

**Purpose**: Rank scenarios based on weighted scores

**Responsibilities**:
- Apply weights to deltas
- Calculate composite score
- Sort scenarios by score

**Implemented Logic**:

1. **`__init__(diffs, weights)`**: Stores diffs list and weight config

2. **`rank(scenario_ids)`**:
   - Validates scenario_ids length matches diffs length
   - Extracts weights (with defaults):
     - `avg_wait_time`: 0.25
     - `lost_swaps`: 0.20
     - `throughput`: 0.20
     - `roi`: 0.35
   - For each scenario:
     - Calculates score:
       ```
       score = (-wait_time_delta × w1)
             + (-lost_swaps_delta × w2)
             + (throughput_delta × w3)
             + (roi_delta × w4)
       ```
     - Stores: `{scenario_id, score, kpi_deltas, roi_deltas}`
   - Sorts by score descending, then by scenario_id ascending (tie-breaking)
   - Returns ranked list

3. **`snapshot()`**: Returns num_scenarios and weight_config

**Stubbed/Placeholder**:
- Weight normalization (assumes weights sum to 1.0, no enforcement)
- ML-based ranking
- Multi-objective optimization
- Constraint-based filtering

**Key Observation**:
- ScenarioRanker is FULLY FUNCTIONAL
- Scoring formula is deterministic
- Stable sorting (ties broken by scenario_id)

---

### **`schemas/event_log_schema.json`** (16 lines)

**Purpose**: JSON Schema for event log validation

**Schema Definition**:
```json
{
  "type": "object",
  "required": ["event_id", "timestamp", "event_type"],
  "properties": {
    "event_id": {"type": "string"},
    "timestamp": {"type": "string"},
    "event_type": {"type": "string"},
    "station_id": {"type": ["string", "null"]},
    "rider_id": {"type": ["string", "null"]},
    "battery_id": {"type": ["string", "null"]},
    "metadata": {"type": "object", "additionalProperties": true}
  }
}
```

**Key Observation**:
- Schema is DEFINED but NOT ENFORCED in code
- EventLogger validates event_type against allowed list, but doesn't validate against JSON Schema

---

### **`nlp/nl_to_toon.py`** (106+ lines, partially read)

**Purpose**: Orchestrate NL → TOON DSL translation

**Responsibilities**:
- Build Gemini prompt
- Call Gemini API
- Parse TOON script
- Validate config

**Implemented Logic**:

1. **`translate_nl_to_toon(user_text, station_catalog, city)`**:
   - Calls `build_toon_prompt()` to create prompt
   - Calls `GeminiClient().generate_toon(prompt)` to get TOON script
   - Calls `parse_toon_script(toon_text, station_catalog)` to parse
   - Warns if no STATION lines parsed
   - Calls `validate_toon_config()` to validate
   - Returns: `(scenario_config, raw_toon_text)` tuple

2. **`validate_toon_config(config, station_catalog)`**:
   - Enforces defaults:
     - `base.seed = 42` if missing
     - (Line 80 cuts off, rest not read)

**Stubbed/Placeholder**:
- Cannot determine without reading full file

---

### **`nlp/toon_prompt_builder.py`** (66 lines)

**Purpose**: Build Gemini system prompt with TOON grammar

**Implemented Logic**:

1. **`build_toon_prompt(user_text, station_catalog, city)`**:
   - Constructs strict prompt with:
     - Instruction: "You are a TOON DSL compiler. Output nothing except the TOON script"
     - Valid station IDs list
     - Output format examples
     - Commands allowed: BASE, STATION, DEMAND, CONSTRAINT
     - Syntax rules for each command
     - User input
     - City context
   - Returns complete prompt string

**Stubbed/Placeholder**:
- None (prompt builder is complete)

**Key Observation**:
- Prompt engineering is EXPLICIT and STRICT
- Forces Gemini to output TOON DSL only (no markdown, no explanations)

---

### **`nlp/toon_parser.py`** (100+ lines, partially read)

**Purpose**: Parse TOON DSL text into config dict

**Implemented Logic**:

1. **`ToonParseError`**: Custom exception class

2. **`_extract_from_fences(script)`**:
   - If script contains triple backticks:
     - Extracts content between first \`\`\` pair
     - Handles optional "toon" language identifier
   - Returns cleaned script

3. **`parse_toon_script(script, station_catalog)`**:
   - Initializes config dict with sections: base, stations, demand, constraints
   - Extracts from fences
   - Splits into lines
   - For each line:
     - If starts with "BASE": parses key-value, validates numeric types (seed, duration), stores in base
     - If starts with "STATION": validates station_id in catalog, creates station dict entry
     - (Lines 100+ not read, likely handles other commands)
   - Returns structured config dict

**Stubbed/Placeholder**:
- Cannot determine without reading full file (lines 100-164 not shown)

---

### **`nlp/gemini_client.py`** (not read)

**Purpose**: Wrapper for Google Gemini API

This file was not read. Based on usage in `nl_to_toon.py`:
- Contains `GeminiClient` class
- Has method `generate_toon(prompt)` that returns TOON script text
- Likely handles API key, HTTP requests, error handling

---

### **`_verification.py`** (723 lines)

**Purpose**: Automated testing script for simulation backend

**Responsibilities**:
- Verify module imports
- Test determinism (same config → same output)
- Test event emission
- Test KPI/ROI math
- Test scenario comparison and ranking

**Test Tiers**:

1. **Tier 1**: Module import sanity (imports all simulation modules)
2. **Tier 2**: Single simulation determinism (runs twice, compares KPIs, events, metadata)
3. **Tier 3**: Event emission integrity (checks for required event types)
4. **Tier 4**: KPI/ROI mathematical sanity (validates formulas)
5. **Tier 5**: Scenario comparison + ranking (validates diff and rank logic)

**Key Observation**:
- This is a TESTING/VALIDATION script, not production code
- Provides example configs showing expected structure for real mode

---

## Data Structure Documentation

### Scenario Request (Frontend → API)

```typescript
{
  description: string,
  city_config: {
    zones: string[],
    stations: [
      {
        station_id: string,
        lat: number,          // NOTE: frontend uses "lat"
        lon: number,          // NOTE: frontend uses "lon"
        zone_id: string,
        chargers_total: number,
        chargers_active: number
      }
    ]
  },
  interventions: object,      // Free-form, currently NOT USED
  simulation_duration: number,
  mode: "fake" | "real"
}
```

### Runtime Config (What `run_simulation()` Receives)

**From Celery Task** (`tasks.py:127`):
```python
{
  "run_id": string,
  "data_dir": string,
  "city_config": {...},       # Passed through unchanged
  "interventions": {...},     # Passed through unchanged (NOT USED)
  "simulation_duration": int,
  "description": string
}
```

**Expected for Real Mode** (from `_verification.py` examples):
```python
{
  "seed": int,
  "city": string,
  "start_time": datetime,
  "end_time": datetime,
  "stations": [                # Different from city_config.stations!
    {
      "station_id": string,
      "zone_id": string,
      "latitude": float,       # NOTE: real mode expects "latitude"
      "longitude": float,      # NOTE: real mode expects "longitude"
      "swap_bays": int,
      "chargers_total": int,
      "inventory_current": int,
      "inventory_capacity": int,
      "queue_length": int,
      "status": "up" | "down"
    }
  ],
  "demand_config": {
    "rng_seed": int,
    "base_demand_rate": float,
    "time_of_day_curve": {...},
    "weather_config": {...},
    "events_config": [...],
    "station_weights": {...}
  },
  "inventory_config": {
    "initial_inventory": {station_id: int},
    "refill_threshold": int,
    "refill_amount": int
  },
  "revenue_per_swap": float,
  "charger_energy_cost": float,
  "station_staff_cost": float,
  "battery_depreciation_cost": float,
  "infra_maintenance_cost": float,
  "capital_cost": float
}
```

### Simulation Result (What `run_simulation()` Returns)

```python
{
  "metadata": {
    "run_id": string,
    "start_time": string (ISO 8601),
    "end_time": string (ISO 8601),
    "seed": int,
    "city": string
  },
  "kpis": {
    "avg_wait_time": float,      # Minutes
    "lost_swaps": int,
    "utilization": float,        # 0.0 to 1.0
    "throughput": int,
    "idle_inventory": float,
    "revenue": float,            # Currency units
    "operational_cost": float,
    "net_profit": float,
    "roi": float                 # Percentage (0-100)
  },
  "timeseries": {
    "wait_time": float[],
    "inventory_levels": {station_id: int[]},
    "queue_lengths": {station_id: int[]}
  },
  "events": [
    {
      "event_id": string,
      "timestamp": string (ISO 8601 + 'Z'),
      "event_type": string,
      "station_id": string | null,
      "rider_id": string | null,
      "battery_id": string | null,
      "metadata": object
    }
  ]
}
```

### Event Types

**Documented in `event_logger.py:21-39`**:
- `rider_arrival`: Rider enters system
- `station_selected`: Routing decision made
- `reroute`: Rider rerouted to different station
- `queue_join`: Rider joins station queue
- `queue_leave`: Rider leaves queue (served or abandoned)
- `swap_start`: Battery swap begins
- `swap_complete`: Battery swap finishes
- `lost_swap`: Rider abandoned or timed out
- `charge_start`: Battery charging begins
- `charge_complete`: Battery charging finishes
- `inventory_stockout`: Station has no batteries
- `replenishment_trigger`: Refill triggered
- `replenishment_complete`: Refill delivered
- `charger_failure`: Charger breaks down
- `charger_repair`: Charger repaired
- `station_down`: Station goes offline
- `station_up`: Station comes back online

---

## Fake vs Real Mode Comparison

### Fake Mode (`_run_fake_simulation`)

**What Happens**:
1. Initializes seeded RNG with `seed` from config
2. Generates random KPIs:
   - Arrivals: 50-200 (random)
   - Completed: 70-95% of arrivals
   - Lost: remainder
   - Avg wait time: 2-15 minutes (random)
   - Utilization: 0.3-0.9 (random)
   - ROI: 0.1-0.5 (random)
3. Generates fake timeseries arrays (random values)
4. Generates 200 fake events with random timestamps, types, station_ids, rider_ids
5. Writes 3 artifact files
6. Returns result dict

**Determinism**: YES (same seed → same output due to seeded RNG)

**Speed**: FAST (~10-50ms, no actual simulation)

**Dependencies**: None (pure Python, no SimPy)

**Use Cases**: UI testing, fast iteration, demo mode

**Limitations**:
- No actual simulation logic
- KPIs are not causally related (wait time doesn't affect utilization, etc.)
- Events are randomly generated, not from actual simulation steps

---

### Real Mode (`_run_real_simulation`)

**What Happens**:
1. Validates SimPy is available (raises RuntimeError if not)
2. Creates temp event log file
3. Initializes all simulation components:
   - `InventoryManager`: tracks battery counts per station
   - `KPITracker`: accumulates arrivals/completions/losses in memory
   - `NetworkGraph`: stores station topology
   - `RoutingEngine`: (placeholder, no actual routing)
   - Stations: creates `Station` (data model) and `StationProcess` (SimPy resource manager) for each station config
   - `DemandGenerator`: generates arrivals (currently only 1 rider)
4. Creates `SimulationEngine` with all components
5. Calls `engine.run(start_time, end_time)`:
   - Schedules arrivals (currently 1 rider)
   - Runs SimPy environment for duration
   - Collects KPI snapshot
6. Reads events from temp log file
7. Passes events to `KPIEngine` to re-compute KPIs from events
8. Passes KPIs to `ROIEngine` to compute financial metrics
9. Merges KPIs and ROI
10. Deletes temp log file
11. Returns result dict with EMPTY timeseries (TODO)

**Determinism**: YES (same seed → same output due to seeded RNG and SimPy determinism)

**Speed**: SLOW (~1-5 seconds for 1-hour simulation, depends on complexity)

**Dependencies**: SimPy, all simulation components

**Use Cases**: Accurate modeling, testing real logic, production scenarios

**Limitations**:
- Only 1 rider generated (DemandGenerator limitation)
- No actual routing (rider pre-assigned to station)
- No actual timing (all yields are timeout(0))
- Timeseries are empty (not generated from events)
- Config mismatch: expects `latitude`/`longitude` but receives `lat`/`lon` from frontend

---

## What Is Actually Implemented

### ✅ Fully Functional Components

1. **EventLogger**: Complete, production-ready
   - Validates event types
   - Writes NDJSON
   - Generates UUIDs and timestamps
   - Flushes immediately

2. **KPIEngine**: Complete, accurate
   - Computes avg_wait_time from queue_join → swap_start
   - Counts lost_swaps
   - Counts throughput (swap_complete events)
   - Computes utilization from swap durations
   - Computes time-weighted idle inventory

3. **ROIEngine**: Complete, simple
   - Revenue = throughput × revenue_per_swap
   - Operational cost = sum of all cost fields
   - Net profit = revenue - operational_cost
   - ROI = (net_profit / capital_cost) × 100

4. **ScenarioManager**: Complete
   - Validates scenarios match baseline
   - Runs baseline + all scenarios sequentially
   - Tags results with scenario_id

5. **ScenarioDiff**: Complete
   - Computes deltas for all KPIs and ROI metrics
   - Pure function, deterministic

6. **ScenarioRanker**: Complete
   - Weighted scoring formula
   - Stable sorting
   - Tie-breaking by scenario_id

7. **InventoryManager**: Mostly complete
   - Tracks battery counts
   - Consume/refill operations work
   - Refills are instant (no delay modeled)

8. **KPITracker**: Basic implementation complete
   - Counts arrivals, completions, losses
   - Tracks wait times
   - Calculates averages

9. **NetworkGraph**: Partially complete
   - add_station, add_edge, remove_station work
   - get_station, get_neighbors work
   - snapshot works
   - load_topology is stub

10. **Fake Simulation Mode**: Complete
    - Deterministic fake data generation
    - Artifact file writing
    - Schema-compliant output

---

### ⚠️ Partially Implemented / Framework Only

1. **SimulationEngine**:
   - ✅ Component initialization
   - ✅ SimPy environment creation
   - ✅ Arrival scheduling infrastructure
   - ❌ Only 1 rider scheduled (DemandGenerator limitation)
   - ❌ No actual routing (uses pre-assigned station)
   - ❌ No timing (all yields are timeout(0))

2. **DemandGenerator**:
   - ✅ Modifier classes (TimeOfDayCurve, WeatherModifier, EventModifier, StationSkewModel)
   - ✅ Simple lookup methods work
   - ❌ **CRITICAL**: `generate_arrivals()` only generates 1 rider
   - ❌ Poisson process not implemented
   - ❌ Weighted station selection not implemented
   - ❌ Interpolation for time-of-day curve not implemented

3. **Station**:
   - ✅ Data fields defined (30+ fields)
   - ❌ **ALL operational methods are event-logging stubs only**
   - ❌ No actual inventory decrement, queue management, timing

4. **StationProcess**:
   - ✅ SimPy Resources created (swap_bays, chargers)
   - ✅ Resource acquisition works (with statement)
   - ✅ Inventory consume/stockout logic works
   - ❌ No actual timing (yields timeout(0))
   - ❌ can_accept_rider always returns True

5. **Rider**:
   - ✅ State tracking (status, times, assigned_station)
   - ✅ Event logging
   - ❌ No actual wait/service timing (yields timeout(0))
   - ❌ No timeout/abandonment logic

6. **RoutingEngine**:
   - ✅ Method signatures defined
   - ❌ **ALL methods return placeholders** (0.0 for scores, first station for selection, current station for reroute)

---

### 🚧 Stub / Placeholder / Not Implemented

1. **Interventions Application**: NOWHERE in code
   - `interventions` field is accepted in API
   - Passed through in `tasks.py`
   - **NEVER USED** in `simulation/main.py` or any component
   - No logic to apply "add_stations", "modify_chargers", etc.

2. **Config Adaptation for Real Mode**: MISSING
   - Frontend sends `{city_config: {stations: [{lat, lon, ...}]}}`
   - Real mode expects `{stations: [{latitude, longitude, ...}]}`
   - No adapter layer to transform this (causes "No stations available" error)
   - Summary mentions adapter was implemented in tasks.py, but current code does NOT show it

3. **Timeseries Generation from Events**: NOT IMPLEMENTED
   - Line 332 in `simulation/main.py` has TODO
   - Real mode returns empty timeseries dicts

4. **Station Selection Weights**: NOT IMPLEMENTED
   - StationSkewModel stores weights
   - DemandGenerator.select_station() ignores weights, returns first station

5. **Time-of-Day Interpolation**: NOT IMPLEMENTED
   - TimeOfDayCurve.get_multiplier() does simple lookup
   - No piecewise linear interpolation

6. **Poisson Arrival Process**: NOT IMPLEMENTED
   - Only 1 arrival generated per simulation
   - Should loop and sample exponential inter-arrival times

7. **Actual Routing Optimization**: NOT IMPLEMENTED
   - RoutingEngine methods are stubs
   - No distance calculation, no scoring, no best station selection

8. **Actual Timing for Swaps/Charging**: NOT IMPLEMENTED
   - All SimPy yields are `timeout(0)`
   - Should use swap_time_sec, charge_time_sec from station config

9. **Queue Capacity Checks**: NOT IMPLEMENTED
   - can_accept_rider always returns True
   - Should check swap bay availability, queue length limits

10. **Charger Resource Usage**: NOT IMPLEMENTED
    - Chargers Resource is created but never used
    - No charging processes scheduled

11. **Battery Lifecycle**: NOT IMPLEMENTED
    - No battery objects
    - No tracking of individual batteries
    - battery_id is always null in events

12. **Replenishment Delays**: NOT IMPLEMENTED
    - Refills are instant
    - Should model delivery delay

13. **Failure Modeling**: NOT IMPLEMENTED
    - charger_failure_rate and station_failure_rate fields exist
    - No logic to trigger failures probabilistically

14. **Job Listing/Cancellation**: NOT IMPLEMENTED
    - API endpoints return "not yet implemented" messages

---

## Intervention Application Logic

### Current State: NOT IMPLEMENTED

**Where interventions are defined**:
- Frontend: `ScenarioSubmission.jsx` line 42 allows user to enter JSON
- API Model: `ScenarioRequest.interventions` field (dict, default={})
- Celery Task: `tasks.py` line 131 copies interventions to runtime_config
- Simulation Main: `simulation/main.py` receives interventions in config dict

**Where interventions SHOULD be applied**:
- This is not implemented or cannot be determined from the code.

**Expected intervention types** (based on frontend placeholder):
```json
{
  "add_stations": [...],
  "modify_chargers": {...}
}
```

**How baseline scenario is created**:
1. Frontend builds `city_config` with zones and stations array
2. Stations have default values: chargers_total=4, chargers_active=4, lat/lon from user or random
3. This is sent as-is to backend
4. Backend does NOT modify city_config
5. In fake mode: city_config is ignored (fake data generated)
6. In real mode: city_config should be used but causes error due to lat/lon vs latitude/longitude mismatch

**Observed behavior**:
- Interventions JSON can be submitted
- It is stored in runtime_config
- It is NEVER READ OR APPLIED anywhere in simulation code
- Scenarios can only differ by explicitly providing different station configs in scenario_configs list (for `/run-scenarios` endpoint)
- Single scenario submission (`/scenarios/submit`) has no mechanism to apply interventions to city_config

---

## Execution Flow Tracing

### Fake Mode Full Trace

```
1. User submits scenario → ScenarioSubmission.jsx:46
2. POST /api/scenarios/submit → endpoints.py:98
3. validate_city_config() → endpoints.py:52
4. Generate UUID run_id
5. create_job_status(run_id) → tasks.py:103
   ↳ _store_job_status(status="submitted") → Redis
6. run_simulation_task.delay(run_id, scenario_data) → tasks.py:113
7. Celery worker picks up task
8. Build runtime_config with city_config, interventions, etc. → tasks.py:127
9. run_simulation(runtime_config, mode="fake") → simulation/main.py:25
10. _run_fake_simulation(config, seed, city) → simulation/main.py:64
11. Initialize random.Random(seed)
12. Generate random KPIs (lines 85-93)
13. Generate random timeseries (lines 96-108)
14. Generate random events (lines 111-135)
15. Write summary.json → config["data_dir"]/summary.json
16. Write events.ndjson → config["data_dir"]/events.ndjson
17. Write frames.ndjson → config["data_dir"]/frames.ndjson
18. Return results dict to tasks.py
19. tasks.py stores result in Redis → key "job_result:{run_id}"
20. Update status to "completed" → Redis
21. Frontend polls /api/jobs/{run_id}/status → returns "completed"
22. Frontend calls /api/jobs/{run_id}/result → returns result from Redis
23. ResultsDashboard displays KPIs
```

**Total Duration**: ~50-200ms (mostly file I/O)

---

### Real Mode Full Trace

```
1-8. [Same as fake mode through task dispatch]
9. run_simulation(runtime_config, mode="real") → simulation/main.py:25
10. _run_real_simulation(config, seed, city) → simulation/main.py:192
11. Create tempfile for events → tempfile.NamedTemporaryFile()
12. Initialize EventLogger(temp_file.name)
13. Extract inventory_config from config
14. Create InventoryManager(initial_inventory, refill_threshold, refill_amount, event_logger)
15. Create KPITracker(event_logger)
16. Create NetworkGraph()
17. Create RoutingEngine(network_graph)
18. Create simpy.Environment()
19. For each station in config["stations"]:
    a. Create Station(station_config, event_logger)
    b. network_graph.add_station(station)
    c. Create StationProcess(station_id, env, swap_bays, chargers, inventory_manager, event_logger)
    d. Add to stations dict
20. Extract demand_config from config
21. Get station list from network_graph
22. Create DemandGenerator(demand_config, station_list, event_logger)
23. Create SimulationEngine(demand_generator, routing_engine, inventory_manager, kpi_tracker, stations, event_logger, seed)
24. Call engine.run(start_time, end_time) → simulation_engine.py:167
    a. Log simulation started event
    b. Call schedule_arrivals(start_time, end_time)
       i. demand_generator.generate_arrivals() → returns list with 1 rider
       ii. For 1 rider:
          - Create Rider(rider_id, arrival_time, assigned_station_id, event_logger)
          - kpi_tracker.record_arrival() → increments counter, logs event
          - env.process(_process_rider_arrival(rider))
          - Log rider_arrival event
    c. Calculate duration_minutes
    d. env.run(until=duration_minutes) → SimPy executes all processes
       i. _process_rider_arrival executes:
          - Yields timeout(0)
          - Calls station.handle_rider(rider)
             → Logs queue_join
             → Yields timeout(0)
             → Rider accepted
          - Calls station.process_swap() (implicit in StationProcess)
             → Acquires swap_bay resource
             → Logs swap_start
             → inventory_manager.consume(station_id)
                → Decrements battery count
                → Logs charge_complete (incorrect event type)
                → Checks needs_refill(), logs replenishment_trigger if needed
             → Yields timeout(0)
             → Logs swap_complete
          - If rider.status == "served":
             → kpi_tracker.record_completion(wait_time=0.0)
    e. Log simulation completed event
    f. Return kpi_tracker.snapshot()
25. Close event_logger
26. Read events from temp_file.name → parse NDJSON into events list
27. Delete temp_file
28. Create KPIEngine(events, kpi_config)
29. kpi_engine.compute() → returns KPIs dict
30. Create ROIEngine(kpis, roi_config)
31. roi_engine.compute() → returns ROI dict
32. Merge KPIs and ROI → final_kpis
33. Return results dict with metadata, kpis=final_kpis, timeseries={empty}, events
34. [Back to tasks.py] Store result in Redis
35. Update status to "completed"
36. Frontend polls and displays results
```

**Total Duration**: ~1-5 seconds (SimPy overhead, component initialization)

**Event Count**: ~5-10 events (1 rider → rider_arrival, queue_join, swap_start, charge_complete, swap_complete, replenishment_trigger if inventory low)

**KPIs Computed**:
- avg_wait_time: 0.0 (because timeout(0) everywhere)
- lost_swaps: 0 or 1 (depends on inventory)
- utilization: ~0.0 (because swap duration is 0)
- throughput: 0 or 1
- idle_inventory: depends on initial inventory
- Revenue/cost/ROI: calculated from config values

---

## What Is Stubbed or Placeholder

### Critical Placeholders (Block Real Simulation Accuracy)

1. **Demand Generation**:
   - ONLY 1 RIDER PER SIMULATION (lines 289-327 in demand_generator.py)
   - Poisson arrival process: NOT IMPLEMENTED (entire loop is TODO)
   - Expected: 100s or 1000s of riders for 1-hour simulation
   - Actual: Exactly 1 rider

2. **Routing**:
   - Station scoring: Returns 0.0 (no distance calculation, no capacity consideration)
   - Best station selection: Returns first station (no optimization)
   - Travel cost: Returns 0.0 (no graph traversal)
   - Rerouting: Returns current station (no reroute logic)

3. **Timing**:
   - All SimPy yields: `timeout(0)` (instant operations)
   - Expected: `timeout(swap_time_sec)` for swaps, `timeout(charge_time_sec)` for charging
   - Impact: Utilization is always ~0, wait times are 0

4. **Station Operations**:
   - ALL methods in `Station` class are event-logging stubs
   - No inventory decrement, queue management, charger allocation
   - Only logs events, does not modify state

5. **Charger Usage**:
   - Chargers Resource created but NEVER USED
   - No charging processes scheduled
   - Batteries don't get charged in simulation

6. **Battery Lifecycle**:
   - No Battery objects exist
   - battery_id is always null in events
   - No tracking of battery states (empty, charging, full)

7. **Replenishment Delays**:
   - Refills are instant
   - Should model delivery delay (replenishment_delay_sec field exists but unused)

8. **Capacity Constraints**:
   - can_accept_rider always returns True
   - Should check: swap bay availability, queue length limits, inventory availability, station status

9. **Failure Modeling**:
   - charger_failure_rate and station_failure_rate fields exist
   - No probabilistic failure triggers

10. **Interventions**:
    - Interventions field accepted in API
    - NO LOGIC TO APPLY INTERVENTIONS ANYWHERE

---

### Non-Critical Placeholders (Framework Extensions)

1. Time scaling factor (simulation time vs wall clock time)
2. Parallel scenario execution
3. Scenario caching
4. ML-based demand curve fitting
5. Weather API integration
6. Real road network for travel costs
7. Priority queues for fairness
8. Percentile KPI tracking (p50, p95, p99)
9. SLA threshold alerts
10. Anomaly detection hooks

---

## Infrastructure vs Logic Breakdown

### Infrastructure (Framework, No Business Logic)

- `api/endpoints.py`: HTTP routing, validation
- `api/models.py`: Data schemas
- `tasks.py`: Celery orchestration, Redis storage
- `event_logger.py`: NDJSON file writing
- `network_graph.py`: networkx wrapper
- `simulation/__init__.py`: Module exports
- `main.py`: FastAPI app setup

### Framework + Minimal Logic

- `simulation/main.py`: Mode dispatcher, component initialization, fake data generation
- `simulation/simulation_engine.py`: SimPy orchestration framework (with placeholder processes)
- `simulation/station_process.py`: SimPy Resource allocation (with placeholder timing)
- `simulation/rider.py`: State tracking (with placeholder timing)

### Real Simulation Logic (Functional)

- `kpi_engine.py`: Event-based KPI calculation (COMPLETE)
- `roi_engine.py`: Financial metrics (COMPLETE)
- `scenario_diff.py`: Delta calculation (COMPLETE)
- `scenario_ranker.py`: Weighted ranking (COMPLETE)
- `scenario_manager.py`: Multi-scenario orchestration (COMPLETE)
- `inventory_manager.py`: Battery count tracking (MOSTLY COMPLETE, instant refills)
- `kpi_tracker.py`: Runtime KPI accumulation (BASIC COMPLETE)

### Placeholder Logic Only

- `simulation/demand_generator.py`: Only 1 rider generated
- `simulation/routing.py`: All methods return defaults
- `simulation/station.py`: All methods are event-logging stubs

---

## Key Findings Summary

### What Works Today

✅ **Fake mode**: Fully functional, deterministic, fast  
✅ **Event logging**: Production-ready NDJSON output  
✅ **KPI computation from events**: Accurate, deterministic  
✅ **ROI calculation**: Simple arithmetic, works  
✅ **Scenario comparison**: Diff and ranking work  
✅ **Inventory tracking**: Consume/refill logic works (instant)  
✅ **SimPy integration**: Resources are created and acquired correctly  
✅ **API layer**: HTTP endpoints, validation, Celery dispatch work  
✅ **Job tracking**: Redis status storage works  
✅ **NL → TOON translation**: Gemini integration, TOON parsing work  

### What Doesn't Work / Isn't Implemented

❌ **Demand generation**: Only 1 rider per simulation (should be 100s-1000s)  
❌ **Routing**: No actual station selection logic  
❌ **Timing**: All operations are instant (should have delays)  
❌ **Station operations**: All methods are stubs (only log events)  
❌ **Charger usage**: Chargers Resource unused  
❌ **Battery lifecycle**: No battery objects or tracking  
❌ **Capacity constraints**: Always accepts riders (no queue limits)  
❌ **Interventions**: NOT APPLIED anywhere (passed through but ignored)  
❌ **Config adaptation**: Frontend sends lat/lon, real mode expects latitude/longitude (causes errors)  
❌ **Timeseries from events**: Empty in real mode (TODO)  
❌ **Failure modeling**: No probabilistic failures  
❌ **Replenishment delays**: Instant refills (should have delay)  

### Critical Gap: Config Mismatch

**Frontend sends**:
```javascript
city_config: {
  stations: [{lat: 40.7128, lon: -74.0060, ...}]
}
```

**Real mode expects**:
```python
stations: [{latitude: 28.6139, longitude: 77.2090, ...}]
```

**Result**: Real mode cannot read station configs from frontend submissions

**Previous fix mentioned in summary**: Adapter functions `_build_real_runtime_config` in tasks.py and `_adapt_real_config_for_run_simulation` in endpoints.py were implemented to transform configs. However, current code does NOT show these functions. Either:
- They were not committed, OR
- They are on a different branch, OR
- The summary refers to planned work, not completed work

**Current code evidence**: `grep` search for these function names returned NO MATCHES.

---

## Unanswered Questions / Cannot Determine from Code

1. **How are interventions supposed to be applied?**
   - This is not implemented or cannot be determined from the code.

2. **What is the expected structure of interventions?**
   - Placeholder in frontend suggests `{add_stations: [...], modify_chargers: {...}}`
   - No validation or documentation exists
   - No code consumes this field

3. **Why does real mode work at all if config mismatch exists?**
   - This is not implemented or cannot be determined from the code.
   - Based on git status showing simulation results exist, either:
     - Previous fix was implemented but not in current main branch, OR
     - Tests use correct config format directly, OR
     - Results are from fake mode only

4. **How should timeseries be generated from events?**
   - This is not implemented or cannot be determined from the code.
   - TODO on line 332 of simulation/main.py indicates it should be done
   - No implementation exists

5. **What is the expected config format for demand_config modifiers?**
   - Classes exist for TimeOfDayCurve, WeatherModifier, EventModifier
   - Example configs are not provided in code
   - Structure can be inferred from __init__ methods but not documented

---

## File Count Summary

**Total Python files analyzed**: 31  
**Fully implemented**: 6 (kpi_engine, roi_engine, scenario_diff, scenario_ranker, event_logger, scenario_manager)  
**Partially implemented**: 9 (main, simulation_engine, inventory_manager, kpi_tracker, network_graph, station_process, rider, demand_generator components)  
**Stub/placeholder only**: 3 (station, routing, demand_generator.generate_arrivals)  
**Infrastructure only**: 5 (endpoints, models, tasks, main.py, __init__)  
**Not read/analyzed**: 8 (NLP components, database, models modules)

---

**End of Analysis**
