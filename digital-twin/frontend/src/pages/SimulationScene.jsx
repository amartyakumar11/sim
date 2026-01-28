import React, { useState, useEffect } from 'react'

// Static mock stations with live state (simulating existing simulation output)
const STATIONS = [
  { id: 'ST_N1', label: 'North Hub', capacity: 6, x: 18, y: 20, queueLength: 0, activeChargers: 2, state: 'idle' },
  { id: 'ST_N2', label: 'Tech Park', capacity: 4, x: 35, y: 18, queueLength: 3, activeChargers: 4, state: 'busy' },
  { id: 'ST_C1', label: 'Central Exchange', capacity: 8, x: 50, y: 45, queueLength: 5, activeChargers: 7, state: 'busy' },
  { id: 'ST_W1', label: 'West Depot', capacity: 3, x: 22, y: 60, queueLength: 1, activeChargers: 1, state: 'idle' },
  { id: 'ST_E1', label: 'Riverfront', capacity: 5, x: 70, y: 38, queueLength: 2, activeChargers: 3, state: 'busy' },
  { id: 'ST_S1', label: 'South Hub', capacity: 7, x: 62, y: 72, queueLength: 0, activeChargers: 0, state: 'idle' },
]

// Map capacity (chargers) to visual size tiers
function getCapacityTier(capacity) {
  if (capacity >= 7) return 'large'
  if (capacity >= 5) return 'medium'
  return 'small'
}

// Determine station visual state based on queue and activity
function getStationState(queueLength, activeChargers, capacity) {
  const utilization = activeChargers / capacity
  const hasQueue = queueLength > 0

  if (hasQueue && utilization > 0.7) return 'busy'
  if (hasQueue || utilization > 0.4) return 'active'
  return 'idle'
}

function SimulationScene() {
  // Simulate state changes (using existing simulation output structure)
  const [stationStates, setStationStates] = useState(STATIONS)
  const [overlaysVisible, setOverlaysVisible] = useState(true)

  // Periodic state updates to simulate live simulation (no API calls, just visual updates)
  useEffect(() => {
    const interval = setInterval(() => {
      setStationStates(prev =>
        prev.map(station => {
          // Simulate realistic state transitions
          const queueChange = Math.random() > 0.7 ? (Math.random() > 0.5 ? 1 : -1) : 0
          const chargerChange = Math.random() > 0.8 ? (Math.random() > 0.5 ? 1 : -1) : 0

          const newQueueLength = Math.max(0, Math.min(8, station.queueLength + queueChange))
          const newActiveChargers = Math.max(0, Math.min(station.capacity, station.activeChargers + chargerChange))
          const newState = getStationState(newQueueLength, newActiveChargers, station.capacity)

          return {
            ...station,
            queueLength: newQueueLength,
            activeChargers: newActiveChargers,
            state: newState,
          }
        }),
      )
    }, 2000) // Update every 2 seconds

    return () => clearInterval(interval)
  }, [])

  // Derived observer signals (no API calls; derived from existing station state)
  const derived = (() => {
    const counts = { idle: 0, active: 0, busy: 0, queued: 0 }
    let hotspot = null // station with highest queue
    for (const s of stationStates) {
      const st = getStationState(s.queueLength, s.activeChargers, s.capacity)
      counts[st] += 1
      if (s.queueLength > 0) counts.queued += 1
      if (!hotspot || s.queueLength > hotspot.queueLength) hotspot = s
    }

    // Qualitative pressure (no numeric overlay)
    const pressure =
      counts.busy >= 3 || (hotspot?.queueLength ?? 0) >= 5
        ? 'High'
        : counts.active >= 3 || (hotspot?.queueLength ?? 0) >= 3
        ? 'Medium'
        : 'Low'

    const hotspotLabel = hotspot && hotspot.queueLength > 0 ? hotspot.label : 'None'

    return { counts, pressure, hotspotLabel }
  })()

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '20px' }}>
      {/* Scene header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, margin: 0, color: '#000' }}>City Simulation Scene</h1>
        <p style={{ margin: '8px 0 0', color: '#555', maxWidth: 640 }}>
          Live view of battery swap stations. Queue length, charging activity, and station state are visualized
          without numbers. Busy stations appear dense; idle stations appear calm.
        </p>
      </div>

      {/* City canvas */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          maxWidth: 1100,
          aspectRatio: '16 / 9',
          borderRadius: 16,
          border: '1px solid #d4d4d8',
          overflow: 'hidden',
          background:
            'radial-gradient(circle at top left, #e5f2ff 0, #f4f4f5 40%, #e4f5f0 75%, #e4e4f5 100%)',
          boxShadow: '0 10px 30px rgba(15, 23, 42, 0.08)',
        }}
      >
        {/* Subtle grid to imply city blocks (no maps, no metrics) */}
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(to right, rgba(148,163,184,0.12) 1px, transparent 1px),' +
              'linear-gradient(to bottom, rgba(148,163,184,0.12) 1px, transparent 1px)',
            backgroundSize: '40px 40px',
            opacity: 0.7,
          }}
        />

        {/* Observer overlays (glassmorphism allowed here) */}
        {overlaysVisible && (
          <div
            className="glass-overlay overlay-summary"
            style={{
              position: 'absolute',
              right: 16,
              top: 16,
              width: 280,
              padding: 12,
              borderRadius: 14,
              backgroundColor: 'rgba(15, 23, 42, 0.75)', // opacity within 0.65–0.90
              backdropFilter: 'blur(10px)', // <= 12px
              border: '1px solid rgba(248, 250, 252, 0.35)',
              boxShadow: '0 12px 30px rgba(2, 6, 23, 0.35)',
              color: 'rgba(248, 250, 252, 0.95)',
              pointerEvents: 'none', // observer-only
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
              <div style={{ fontSize: 11, letterSpacing: 0.14, textTransform: 'uppercase', opacity: 0.85 }}>
                System Snapshot
              </div>
              <div style={{ fontSize: 11, opacity: 0.9 }}>
                Queue pressure: <span style={{ fontWeight: 700 }}>{derived.pressure}</span>
              </div>
            </div>

            <div style={{ marginTop: 10, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div>
                <div style={{ fontSize: 10, opacity: 0.78, letterSpacing: 0.12, textTransform: 'uppercase' }}>Idle</div>
                <div style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {Array.from({ length: derived.counts.idle }).map((_, i) => (
                    <span
                      key={`i-${i}`}
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: 999,
                        backgroundColor: 'rgba(148, 163, 184, 0.9)',
                      }}
                    />
                  ))}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 10, opacity: 0.78, letterSpacing: 0.12, textTransform: 'uppercase' }}>Active</div>
                <div style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {Array.from({ length: derived.counts.active }).map((_, i) => (
                    <span
                      key={`a-${i}`}
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: 999,
                        backgroundColor: 'rgba(59, 130, 246, 0.95)',
                      }}
                    />
                  ))}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 10, opacity: 0.78, letterSpacing: 0.12, textTransform: 'uppercase' }}>Busy</div>
                <div style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {Array.from({ length: derived.counts.busy }).map((_, i) => (
                    <span
                      key={`b-${i}`}
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: 999,
                        backgroundColor: 'rgba(220, 38, 38, 0.95)',
                      }}
                    />
                  ))}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 10, opacity: 0.78, letterSpacing: 0.12, textTransform: 'uppercase' }}>
                  Hotspot
                </div>
                <div style={{ marginTop: 6, fontSize: 12, fontWeight: 650 }}>
                  {derived.hotspotLabel}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Floating control (glassmorphism allowed; max 2 glass layers at once) */}
        <button
          type="button"
          className="glass-overlay overlay-control"
          onClick={() => setOverlaysVisible(v => !v)}
          style={{
            position: 'absolute',
            right: 16,
            bottom: 16,
            padding: '10px 12px',
            borderRadius: 14,
            backgroundColor: 'rgba(15, 23, 42, 0.70)', // within contract
            backdropFilter: 'blur(10px)', // <= 12px
            border: '1px solid rgba(248, 250, 252, 0.35)',
            color: 'rgba(248, 250, 252, 0.95)',
            fontSize: 12,
            letterSpacing: 0.2,
            cursor: 'pointer',
            boxShadow: '0 12px 30px rgba(2, 6, 23, 0.35)',
          }}
        >
          {overlaysVisible ? 'Hide overlays' : 'Show overlays'}
        </button>

        {/* Station placeholders with queue and state visualization */}
        {stationStates.map((station, index) => {
          const tier = getCapacityTier(station.capacity)
          const baseSize = tier === 'large' ? 64 : tier === 'medium' ? 48 : 36
          const stationState = getStationState(station.queueLength, station.activeChargers, station.capacity)
          const isBusy = stationState === 'busy'
          const isActive = stationState === 'active'
          const isIdle = stationState === 'idle'

          // Visual density: busy = more elements, idle = minimal
          const chargeIndicatorCount = Math.min(station.activeChargers, 4) // Max 4 indicators for clarity
          const queueBarHeight = Math.min(station.queueLength * 6, 30) // Max 30px height

          return (
            <div
              key={station.id}
              className="sim-station"
              data-state={stationState}
              style={{
                position: 'absolute',
                left: `${station.x}%`,
                top: `${station.y}%`,
                transform: 'translate(-50%, -50%)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                animationName: 'sim-station-entry',
                animationDuration: '220ms',
                animationTimingFunction: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
                animationFillMode: 'backwards',
                animationDelay: `${40 * index}ms`,
                transition: 'all 240ms cubic-bezier(0.2, 0.8, 0.2, 1)',
              }}
            >
              {/* Queue visualization: vertical bar below station */}
              {station.queueLength > 0 && (
                <div
                  className="queue-bar"
                  style={{
                    width: 4,
                    height: queueBarHeight,
                    backgroundColor: isBusy ? '#dc2626' : '#f59e0b',
                    borderRadius: '2px 2px 0 0',
                    marginBottom: 4,
                    transition:
                      'height 240ms cubic-bezier(0.2, 0.8, 0.2, 1), background-color 240ms cubic-bezier(0.2, 0.8, 0.2, 1)',
                    boxShadow: isBusy
                      ? '0 2px 8px rgba(220, 38, 38, 0.4)'
                      : '0 2px 6px rgba(245, 158, 11, 0.3)',
                  }}
                />
              )}

              {/* Station disc with charging activity indicators */}
              <div
                className="station-disc"
                style={{
                  width: baseSize,
                  height: baseSize,
                  borderRadius: '999px',
                  background:
                    tier === 'large'
                      ? 'linear-gradient(135deg, #047857, #22c55e)'
                      : tier === 'medium'
                      ? 'linear-gradient(135deg, #0369a1, #38bdf8)'
                      : 'linear-gradient(135deg, #4b5563, #9ca3af)',
                  boxShadow: isBusy
                    ? '0 8px 24px rgba(15, 23, 42, 0.5), 0 0 0 2px rgba(220, 38, 38, 0.3)'
                    : isActive
                    ? '0 8px 20px rgba(15, 23, 42, 0.4), 0 0 0 1px rgba(59, 130, 246, 0.2)'
                    : '0 8px 18px rgba(15, 23, 42, 0.35)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  position: 'relative',
                  transition: 'box-shadow 240ms cubic-bezier(0.2, 0.8, 0.2, 1)',
                }}
              >
                {/* Charging activity indicators: small dots around perimeter */}
                {chargeIndicatorCount > 0 && (
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      borderRadius: '999px',
                    }}
                  >
                    {Array.from({ length: chargeIndicatorCount }).map((_, i) => {
                      const angle = (i / chargeIndicatorCount) * Math.PI * 2
                      const radius = baseSize * 0.42
                      const x = Math.cos(angle) * radius
                      const y = Math.sin(angle) * radius

                      return (
                        <div
                          key={i}
                          className="charge-indicator"
                          style={{
                            position: 'absolute',
                            left: `50%`,
                            top: `50%`,
                            transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`,
                            width: 6,
                            height: 6,
                            borderRadius: '999px',
                            backgroundColor: '#fbbf24',
                            boxShadow: '0 0 4px rgba(251, 191, 36, 0.8)',
                            opacity: isBusy ? 1 : 0.7,
                            transition: 'opacity 240ms cubic-bezier(0.2, 0.8, 0.2, 1)',
                          }}
                        />
                      )
                    })}
                  </div>
                )}

                {/* Capacity implied by inner rings, not explicit numbers */}
                <div
                  style={{
                    width: baseSize * 0.55,
                    height: baseSize * 0.55,
                    borderRadius: '999px',
                    border:
                      tier === 'large'
                        ? '3px solid rgba(248, 250, 252, 0.9)'
                        : '2px solid rgba(248, 250, 252, 0.9)',
                    boxShadow: '0 0 0 2px rgba(15, 23, 42, 0.25)',
                  }}
                />
              </div>

              {/* Station label with state indicator */}
              <div
                style={{
                  marginTop: 6,
                  padding: '2px 8px',
                  borderRadius: 999,
                  backgroundColor: isBusy
                    ? 'rgba(220, 38, 38, 0.9)'
                    : isActive
                    ? 'rgba(59, 130, 246, 0.9)'
                    : 'rgba(15, 23, 42, 0.85)',
                  color: '#f9fafb',
                  fontSize: 11,
                  letterSpacing: 0.2,
                  textTransform: 'uppercase',
                  whiteSpace: 'nowrap',
                  transition: 'background-color 240ms cubic-bezier(0.2, 0.8, 0.2, 1)',
                }}
              >
                {station.label}
              </div>
            </div>
          )
        })}

        {/* Legend strip: capacity and state indicators */}
        <div
          style={{
            position: 'absolute',
            left: 16,
            bottom: 16,
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          {/* Capacity legend */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '6px 10px',
              borderRadius: 999,
              backgroundColor: 'rgba(15, 23, 42, 0.9)',
              color: '#e5e7eb',
              fontSize: 10,
            }}
          >
            <span style={{ opacity: 0.8, textTransform: 'uppercase', letterSpacing: 0.12 }}>
              Capacity
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '999px',
                  background: 'linear-gradient(135deg, #4b5563, #9ca3af)',
                }}
              />
              <span style={{ opacity: 0.85 }}>S</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '999px',
                  background: 'linear-gradient(135deg, #0369a1, #38bdf8)',
                }}
              />
              <span style={{ opacity: 0.85 }}>M</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: '999px',
                  background: 'linear-gradient(135deg, #047857, #22c55e)',
                }}
              />
              <span style={{ opacity: 0.85 }}>L</span>
            </div>
          </div>

          {/* State legend */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '6px 10px',
              borderRadius: 999,
              backgroundColor: 'rgba(15, 23, 42, 0.9)',
              color: '#e5e7eb',
              fontSize: 10,
            }}
          >
            <span style={{ opacity: 0.8, textTransform: 'uppercase', letterSpacing: 0.12 }}>
              State
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '999px',
                  backgroundColor: 'rgba(15, 23, 42, 0.85)',
                }}
              />
              <span style={{ opacity: 0.85 }}>Idle</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '999px',
                  backgroundColor: 'rgba(59, 130, 246, 0.9)',
                }}
              />
              <span style={{ opacity: 0.85 }}>Active</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '999px',
                  backgroundColor: 'rgba(220, 38, 38, 0.9)',
                }}
              />
              <span style={{ opacity: 0.85 }}>Busy</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 4 }}>
              <div
                style={{
                  width: 4,
                  height: 12,
                  backgroundColor: '#f59e0b',
                  borderRadius: '2px',
                }}
              />
              <span style={{ opacity: 0.85 }}>Queue</span>
            </div>
          </div>
        </div>
      </div>

      {/* Local keyframes and reduced-motion handling */}
      <style
        dangerouslySetInnerHTML={{
          __html: `
          @keyframes sim-station-entry {
            from {
              opacity: 0;
              transform: translate(-50%, -50%) scale(0.92);
            }
            to {
              opacity: 1;
              transform: translate(-50%, -50%) scale(1);
            }
          }

          /* State transition animations (one-time, not looping) */
          .queue-bar {
            animation: queue-appear 240ms cubic-bezier(0.2, 0.8, 0.2, 1) backwards;
          }

          @keyframes queue-appear {
            from {
              opacity: 0;
              transform: scaleY(0);
            }
            to {
              opacity: 1;
              transform: scaleY(1);
            }
          }

          .charge-indicator {
            animation: charge-pulse 240ms cubic-bezier(0.2, 0.8, 0.2, 1) backwards;
          }

          @keyframes charge-pulse {
            from {
              opacity: 0;
              transform: translate(calc(-50% + var(--x, 0px)), calc(-50% + var(--y, 0px))) scale(0);
            }
            to {
              opacity: 1;
              transform: translate(calc(-50% + var(--x, 0px)), calc(-50% + var(--y, 0px))) scale(1);
            }
          }

          /* Glass overlays: fade + slide only, strictly timed */
          .glass-overlay {
            animation: overlay-in 220ms cubic-bezier(0.2, 0.8, 0.2, 1) backwards;
          }

          @keyframes overlay-in {
            from {
              opacity: 0;
              transform: translateY(-6px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }

          /* Hover (control only): subtle, no blur changes */
          .overlay-control:hover {
            transform: translateY(-1px);
            transition: transform 160ms cubic-bezier(0.25, 0.1, 0.25, 1.0);
          }

          @media (prefers-reduced-motion: reduce) {
            .sim-station,
            .queue-bar,
            .charge-indicator,
            .glass-overlay {
              animation: none !important;
              transition: opacity 80ms !important;
            }
            .overlay-control:hover {
              transform: none;
            }
          }
        `,
        }}
      />
    </div>
  )
}

export default SimulationScene

