## Digital Twin Simulation Sandbox – UI Style & Motion Contract

**Status**: Non‑negotiable baseline for all UI work  
**Scope**: Web frontend (`frontend/`), including any future pages and components  
**Code Constraint**: This document is the single source of truth for visual and motion rules. Any deviation must first update this contract.

---

## 1. Glassmorphism Rules

**1.1 Where glassmorphism is ALLOWED**

- **Observer overlays** (read‑only status/info surfaces that float above primary content)
  - Examples: run metadata overlays, compact KPIs pinned over charts, simulation state badges.
- **Control overlays** (transient controls layered over main content)
  - Examples: map controls, filter trays, scenario quick‑switch palettes, command palettes.

**1.2 Where glassmorphism is FORBIDDEN**

- **Charts** (including but not limited to line, bar, area, pie, scatter, heatmaps)
  - Chart containers, plot areas, axes backgrounds must be fully opaque.
- **Tables and data grids**
  - Header, body, footer, and row backgrounds must be opaque.
- **Core simulation entities**
  - Station cards, KPI tiles, timelines, route traces, node markers, and any element that directly represents a simulated asset or metric must not use frosted glass or translucent surfaces.
- **Global app structure**
  - App shell (header, sidebar, main content background) must not use blur‑based glassmorphism.

**1.3 Glass visual parameters (when allowed)**

- **Max blur radius**: **`backdrop-filter: blur(12px)`**  
  - Hard upper bound. Recommended range: **4–10px**.
- **Opacity range for frosted surfaces**:
  - Background color must be an RGBA value.
  - **Minimum opacity**: **`0.65`**  
  - **Maximum opacity**: **`0.90`**  
  - Recommended default: `rgba(15, 23, 42, 0.75)` or equivalent token.
- **Background contrast requirements**:
  - Text placed on any glass surface must meet **WCAG AA** contrast (4.5:1) against the effective composite background.
  - Dark‑on‑light vs light‑on‑dark:
    - For dark glass (e.g., bluish/grayish background), use **pure or near‑pure white text** with at least **0.75 opacity**.
    - For light glass (if ever used), use **#020617–#111827** text with opacity **≥ 0.9**.
  - A solid, non‑transparent **border** or **inner shadow** is mandatory:
    - Border color opacity **≥ 0.3**.
    - This ensures edge separation regardless of underlying content.

**1.4 Interaction behavior**

- Hover and focus states may adjust:
  - **Opacity** within **±0.05** of base value (never going below 0.60).
  - **Box‑shadow** intensity, but not blur radius beyond **16px**.
- Blur radius must remain fixed per component state; no animated blur pulsing.

---

## 2. Motion System

**2.1 Allowed animation types**

- **Micro‑interactions**:
  - Button hover/focus/pressed states (color, shadow, scale ≤ **1.03x**).
  - Icon emphasis on hover (opacity, subtle rotation ≤ **4°**, scale ≤ **1.05x**).
- **State transitions**:
  - Page transitions (route changes) using opacity and layout shifts.
  - Panel/overlay open‑close (slide + fade).
  - Toasts and transient status banners (slide/fade).
- **Data‑related affordances**:
  - Smooth transitions between **filter states** for charts/tables (fade in/out, simple vertical slide).
  - Animated progress indicators (linear/indeterminate bars, spinner rotation).

**2.2 Forbidden animation types**

- Continuous, decorative motion unrelated to user action or system state:
  - Background parallax, floating particles, looping waves or gradients.
- Excessive or playful transforms:
  - Large bounces, elastic springs, wobble, or overshoot beyond **1.08x** scale.
  - 3D card flips or perspective rotation for primary UI elements.
- Auto‑playing animations longer than **1.5 seconds** that repeat indefinitely (except minimal spinners/progress).
- Color cycling / strobing / flashing.

**2.3 Timing and duration**

- **Global max animation duration**: **`280ms`**
  - Page transitions: **160–240ms**.
  - Overlays and drawers: **160–220ms**.
  - Button and control micro‑interactions: **120–180ms**.
- **Minimum useful duration**: **80ms** for any visible animation (below this, prefer instant state change).

**2.4 Easing curves (only these are allowed)**

- **Entrance / emphasis**: `cubic-bezier(0.2, 0.8, 0.2, 1)`  
  (standard ease‑out)
- **Exit / de‑emphasis**: `cubic-bezier(0.4, 0.0, 1, 1)`  
  (ease‑in)
- **Continuous micro‑interaction (e.g., hover)**: `cubic-bezier(0.25, 0.1, 0.25, 1.0)`  
  (ease‑in‑out)

Any custom easing not numerically equal to one of the above is forbidden.

**2.5 Rules for chained animations**

- At most **two sequential steps** for a single user action:
  - Example: overlay opens (slide+fade, ≤ 220ms) → internal content fades in (≤ 160ms overlap or start).
- Chains must either:
  - **Overlap** by at least **40%** of their durations, OR
  - Run in strict sequence with a total combined duration ≤ **320ms**.
- No more than **one** transform (scale/translate) and **one** opacity animation per element per transition.

**2.6 Reduced‑motion behavior**

- When `prefers-reduced-motion: reduce` is active:
  - All transition durations must be reduced to **≤ 80ms** or disabled.
  - Transform‑based animations (scale, translate, rotate) must be **disabled**; only opacity and color transitions of ≤ **80ms** are allowed.
  - Auto‑playing, looping motion must be turned off; progress indicators should use non‑animated alternatives where possible.

---

## 3. Visual Hierarchy System

**3.1 Layers**

- **Primary focus layer**
  - Contains: active forms, scenario configuration panels, key KPIs, active charts/tables, primary map canvas.
  - Background: solid, opaque surfaces with clear separation from app chrome.
  - Z‑index: forms and primary controls must render **above** charts and maps, but **below** modals/overlays.
- **Secondary context layer**
  - Contains: secondary KPIs, sidebars, historic runs, filters, legends, and non‑blocking insights.
  - May use subtle separation (lighter/darker background, borders, or low‑depth elevation).
  - Glassmorphism allowed here **only** for overlays as defined in section 1.
- **Background layer**
  - Contains: app shell (header/footer), global nav, background textures or flat color.
  - Must not compete with primary content—no high‑contrast patterns or strong gradients immediately behind charts/tables.

**3.2 Hierarchy constraints**

- At any viewport size, the **primary focus layer** must visually dominate:
  - Minimum **60%** of horizontal space on desktop for primary content area (excluding modals).
  - Minimum **40%** of vertical space for main charts/tables on dashboard‑type screens.
- Secondary and background elements:
  - Use **lower saturation** and/or **lower contrast** than primary actions and primary data.
  - Must not use the same accent color as primary CTAs for non‑actionable items.

**3.3 Typography hierarchy (numeric rules)**

- **Primary titles** (page or section headers):
  - Font size: **24–32px**
  - Font weight: **600–700**
- **Secondary headings**:
  - Font size: **18–22px**
  - Font weight: **500–600**
- **Body text**:
  - Font size: **14–16px**
  - Font weight: **400–500**
- **Caption / metadata**:
  - Font size: **12–13px**
  - Font weight: **400–500**

Body text must always meet **WCAG AA** contrast relative to its background.

---

## 4. Verification Checklist (must always be true)

- **Numeric values defined**:
  - Blur: max **12px**; shadow blur max **16px**.
  - Opacity for glass surfaces: **0.65–0.90**.
  - Animation durations: **80–280ms** normal, **≤ 80ms** in reduced‑motion mode.
- **Allowed vs forbidden explicitly defined**:
  - Glassmorphism: only for overlays; forbidden on charts, tables, core simulation entities, and app shell.
  - Motion: only micro‑interactions and state transitions; no decorative, looping, or exaggerated motion.
- **No ambiguity**:
  - Any new pattern must map to one of: primary focus layer, secondary context layer, or background layer.
  - Any new animation must use one of the allowed easing curves and respect duration limits.
- **One source of truth**:
  - This document governs all frontend visual and motion decisions.
  - Divergences require updating this document in the same pull request that changes the UI.

