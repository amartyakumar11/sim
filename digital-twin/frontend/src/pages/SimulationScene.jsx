import React from 'react'

// Static mock stations for spatial scene (no API, no business logic)
const STATIONS = [
  { id: 'ST_N1', label: 'North Hub', capacity: 6, x: 18, y: 20 },
  { id: 'ST_N2', label: 'Tech Park', capacity: 4, x: 35, y: 18 },
  { id: 'ST_C1', label: 'Central Exchange', capacity: 8, x: 50, y: 45 },
  { id: 'ST_W1', label: 'West Depot', capacity: 3, x: 22, y: 60 },
  { id: 'ST_E1', label: 'Riverfront', capacity: 5, x: 70, y: 38 },
  { id: 'ST_S1', label: 'South Hub', capacity: 7, x: 62, y: 72 },
]

// Map capacity (chargers) to visual size tiers
function getCapacityTier(capacity) {
  if (capacity >= 7) return 'large'
  if (capacity >= 5) return 'medium'
  return 'small'
}

function SimulationScene() {
  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '20px' }}>
      {/* Scene header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, margin: 0, color: '#000' }}>City Simulation Scene</h1>
        <p style={{ margin: '8px 0 0', color: '#555', maxWidth: 640 }}>
          A city-scale view of battery swap stations. Size and spacing suggest capacity and coverage
          across the city, with no interaction required to understand the layout.
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

        {/* Station placeholders */}
        {STATIONS.map((station, index) => {
          const tier = getCapacityTier(station.capacity)
          const baseSize = tier === 'large' ? 64 : tier === 'medium' ? 48 : 36

          return (
            <div
              key={station.id}
              className="sim-station"
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
              }}
            >
              {/* Station disc */}
              <div
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
                  boxShadow: '0 8px 18px rgba(15, 23, 42, 0.35)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
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

              {/* Station label (no metrics, just identity and rough area) */}
              <div
                style={{
                  marginTop: 6,
                  padding: '2px 8px',
                  borderRadius: 999,
                  backgroundColor: 'rgba(15, 23, 42, 0.85)',
                  color: '#f9fafb',
                  fontSize: 11,
                  letterSpacing: 0.2,
                  textTransform: 'uppercase',
                  whiteSpace: 'nowrap',
                }}
              >
                {station.label}
              </div>
            </div>
          )
        })}

        {/* Legend strip (no numbers, only relative semantics) */}
        <div
          style={{
            position: 'absolute',
            left: 16,
            bottom: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            padding: '8px 12px',
            borderRadius: 999,
            backgroundColor: 'rgba(15, 23, 42, 0.9)',
            color: '#e5e7eb',
            fontSize: 11,
          }}
        >
          <span style={{ opacity: 0.8, textTransform: 'uppercase', letterSpacing: 0.12 }}>
            Station Capacity
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: '999px',
                background: 'linear-gradient(135deg, #4b5563, #9ca3af)',
              }}
            />
            <span style={{ opacity: 0.85 }}>Small</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span
              style={{
                width: 12,
                height: 12,
                borderRadius: '999px',
                background: 'linear-gradient(135deg, #0369a1, #38bdf8)',
              }}
            />
            <span style={{ opacity: 0.85 }}>Medium</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span
              style={{
                width: 14,
                height: 14,
                borderRadius: '999px',
                background: 'linear-gradient(135deg, #047857, #22c55e)',
              }}
            />
            <span style={{ opacity: 0.85 }}>Large</span>
          </div>
        </div>
      </div>

      {/* Local keyframes and reduced-motion handling */}
      <style dangerouslySetInnerHTML={{
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

          @media (prefers-reduced-motion: reduce) {
            .sim-station {
              animation: none !important;
            }
          }
        `
      }} />
    </div>
  )
}

export default SimulationScene

