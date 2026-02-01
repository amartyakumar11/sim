import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import {
  Card,
  Row,
  Col,
  Statistic,
  Alert,
  Spin,
  Typography,
  Divider,
  Tag,
  Empty,
  Button,
  Drawer,
  Table,
  Tooltip,
} from 'antd'
import {
  ClockCircleOutlined,
  ThunderboltOutlined,
  RiseOutlined,
  DollarOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import { simulationAPI } from '../services/api'
import CoverageCard from '../components/CoverageCard'

const { Title, Text, Paragraph } = Typography

function asNumber(value) {
  if (value === null || value === undefined) return null
  const n = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(n) ? n : null
}

function formatFixed(value, digits) {
  const n = asNumber(value)
  if (n === null) return '0'
  return n.toFixed(digits)
}

// Flat station table data (no hooks; safe across renders)
const STATION_DATA = [
  { key: 'st_1', name: 'Station 1', swaps: 45, lost: 5, state: 'active' },
  { key: 'st_2', name: 'Station 2', swaps: 38, lost: 3, state: 'idle' },
  { key: 'st_3', name: 'Station 3', swaps: 52, lost: 7, state: 'busy' },
  { key: 'st_4', name: 'Station 4', swaps: 41, lost: 4, state: 'active' },
]

const STATION_COLUMNS = [
  { title: 'Station', dataIndex: 'name', key: 'name' },
  { title: 'Swaps', dataIndex: 'swaps', key: 'swaps' },
  { title: 'Lost', dataIndex: 'lost', key: 'lost' },
  { title: 'State', dataIndex: 'state', key: 'state' },
]

function ResultsDashboard() {
  const { runId } = useParams()
  const [searchParams] = useSearchParams()
  const runIdFromParams = runId || searchParams.get('runId')

  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showDataLayer, setShowDataLayer] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [timeseriesData, setTimeseriesData] = useState([])
  const retryTimerRef = useRef(null)
  const aliveRef = useRef(true)

  // ALL HOOKS MUST BE AT THE TOP - before any conditional returns
  const runIdShort = useMemo(() => {
    const s = String(runIdFromParams || '')
    return s.length > 10 ? `${s.substring(0, 8)}…` : s
  }, [runIdFromParams])

  useEffect(() => {
    aliveRef.current = true
    return () => {
      aliveRef.current = false
      if (retryTimerRef.current) {
        clearTimeout(retryTimerRef.current)
        retryTimerRef.current = null
      }
    }
  }, [runIdFromParams])

  // Fetch REAL timeseries data from frames.ndjson when user reveals data layer
  useEffect(() => {
    if (!showDataLayer) return
    if (timeseriesData.length > 0) return
    if (!result?.artifacts?.frames) return

    const fetchFrames = async () => {
      try {
        // Fetch the frames.ndjson artifact
        const framesPath = result.artifacts.frames.replace('/app/data/', '')
        // Use relative URL for production compatibility (nginx proxies /data/ to API)
        const apiBase = window.location.hostname === 'localhost' ? 'http://localhost:8000' : ''
        const response = await fetch(`${apiBase}/data/${framesPath}`)
        const text = await response.text()

        // Parse NDJSON (newline-delimited JSON)
        const frames = text
          .trim()
          .split('\n')
          .map(line => JSON.parse(line))

        // Transform to chart format
        const chartData = frames.map(frame => ({
          time: frame.t,
          wait_time: frame.wait_time,
          utilization: frame.utilization || 0
        }))

        setTimeseriesData(chartData)
      } catch (err) {
        console.error('Failed to fetch frames:', err)
        // Fallback to empty array on error
        setTimeseriesData([])
      }
    }

    fetchFrames()
  }, [showDataLayer, timeseriesData.length, result])

  const fetchResults = useCallback(async () => {
    if (!runIdFromParams) return
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current)
      retryTimerRef.current = null
    }
    setLoading(true)
    setError(null)
    try {
      const data = await simulationAPI.getJobResult(runIdFromParams)
      if (!aliveRef.current) return
      setResult(data)
    } catch (err) {
      if (!aliveRef.current) return
      if (err.response?.status === 202) {
        setError('Simulation is still running. Please wait...')
        // Retry after 3 seconds
        retryTimerRef.current = setTimeout(fetchResults, 3000)
      } else {
        setError(err.response?.data?.detail || err.message)
      }
    } finally {
      if (aliveRef.current) setLoading(false)
    }
  }, [runIdFromParams])

  useEffect(() => {
    if (runIdFromParams) fetchResults()
  }, [runIdFromParams, fetchResults])

  // NOW we can have conditional returns AFTER all hooks
  if (!runIdFromParams) {
    return (
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <Card>
          <Empty description="No run ID provided. Please submit a scenario or select a job from the monitor." />
        </Card>
      </div>
    )
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
        <Paragraph style={{ marginTop: 16 }}>Loading results...</Paragraph>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <Alert
          message="Error Loading Results"
          description={error}
          type="warning"
          showIcon
        />
      </div>
    )
  }

  if (!result) {
    return null
  }

  // Defensive: some runs may return partial/older result objects
  const summary = result?.summary || {}
  console.log("Summary Data:", summary)
  const artifacts = result?.artifacts || {}

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 32
      }}>
        <div>
          <h1 style={{
            fontSize: 32,
            fontWeight: 700,
            color: 'var(--color-text-primary)',
            marginBottom: 8,
            letterSpacing: '-0.02em'
          }}>
            Simulation Results
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 13, color: 'var(--color-text-tertiary)' }}>
              Run ID:
            </span>
            <Text code style={{
              fontSize: 13,
              fontFamily: 'monospace',
              background: 'var(--color-bg-subtle)',
              padding: '4px 10px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-light)'
            }}>
              {runIdShort}
            </Text>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '4px 10px',
              background: 'rgba(16, 185, 129, 0.1)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 12,
              fontWeight: 600,
              color: 'var(--color-accent-success)'
            }}>
              <CheckCircleOutlined />
              COMPLETED
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <Button
            type={showDataLayer ? 'default' : 'primary'}
            onClick={() => setShowDataLayer(v => !v)}
            style={{ borderRadius: 'var(--radius-md)', height: 38 }}
          >
            {showDataLayer ? 'Hide Charts' : 'Show Charts'}
          </Button>
          <Button
            onClick={() => setDrawerOpen(true)}
            style={{ borderRadius: 'var(--radius-md)', height: 38 }}
          >
            View Details
          </Button>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 16,
        marginBottom: 24
      }}>
        {/* Coverage Card (New Level 2 Feature) */}
        <div style={{ gridColumn: '1 / -1' }}>
          <CoverageCard scenarioConfig={result ? { city_config: result.city_config } : null} />
        </div>
        {[
          {
            label: 'Avg Wait Time',
            tooltip: 'Average time riders wait in queue before getting a battery swap. Lower is better. Target: <5 min',
            value: formatFixed(summary.avg_wait_time, 2),
            suffix: 'min',
            icon: <ClockCircleOutlined />,
            color: (asNumber(summary.avg_wait_time) ?? 0) > 10 ? '#ef4444' : '#10b981',
            status: (asNumber(summary.avg_wait_time) ?? 0) > 10 ? 'warning' : 'good'
          },
          {
            label: 'Lost Swaps',
            tooltip: 'Riders who left because queues were full. Indicates insufficient capacity. Target: 0',
            value: asNumber(summary.lost_swaps) ?? 0,
            icon: <CloseCircleOutlined />,
            color: '#ef4444',
            status: 'critical'
          },
          {
            label: 'Charger Utilization',
            tooltip: 'Percentage of time swap bays were actively in use. Higher means better asset efficiency. Target: 60-80%',
            value: ((asNumber(summary.utilization || summary.charger_utilization) ?? 0) * 100).toFixed(1),
            suffix: '%',
            icon: <ThunderboltOutlined />,
            color: '#3b82f6',
            status: 'info'
          },
          {
            label: 'City Throughput',
            tooltip: 'Total successful battery swaps completed. Measures service volume and revenue potential.',
            value: asNumber(summary.throughput || summary.city_throughput) ?? 0,
            suffix: 'swaps',
            icon: <RiseOutlined />,
            color: '#10b981',
            status: 'good'
          },
          {
            label: 'Total Revenue',
            tooltip: (
              <div>
                <div style={{ marginBottom: 4 }}>Total earnings from operations</div>
                {summary.financials ? (
                  <div style={{ fontSize: 11, opacity: 0.9 }}>
                    <div>Primary: {summary.financials.primary_swaps} swaps</div>
                    <div>Secondary: {summary.financials.secondary_swaps} swaps</div>
                    <div>Penalties: ₹{summary.financials.total_penalties}</div>
                  </div>
                ) : 'BatterySmart Model'}
              </div>
            ),
            value: `₹${(asNumber(summary.revenue) ?? 0).toLocaleString()}`,
            icon: <DollarOutlined />,
            color: '#10b981',
            status: 'good'
          },
          {
            label: 'Idle Inventory',
            tooltip: 'Average % of batteries sitting unused at stations. Too high = wasted capital, too low = risk of stockouts.',
            value: formatFixed(summary.idle_inventory_pct ?? summary.idle_inventory, 1),
            suffix: '%',
            color: '#71717a',
            status: 'neutral'
          },
          {
            label: 'Cost Impact',
            tooltip: 'Total operational costs: energy, staff, battery depreciation, and maintenance. Impacts profitability.',
            value: formatFixed(summary.operational_cost || summary.total_cost_impact, 2),
            icon: <DollarOutlined />,
            color: '#f59e0b',
            status: 'neutral'
          },
          {
            label: 'ROI',
            tooltip: 'Return on Investment: (Net Profit / Capital Investment) × 100. Measures financial viability of the network.',
            value: ((asNumber(summary.roi) ?? 0) * 100).toFixed(1),
            suffix: '%',
            color: (asNumber(summary.roi) ?? 0) > 0.2 ? '#10b981' : '#f59e0b',
            status: (asNumber(summary.roi) ?? 0) > 0.2 ? 'good' : 'warning'
          },
          {
            label: 'Events Logged',
            tooltip: 'Total simulation events recorded (arrivals, queue joins, swaps, etc). For debugging and analysis.',
            value: asNumber(result.events_count) ?? 0,
            color: '#71717a',
            status: 'neutral'
          }
        ].map((kpi, i) => (
          <Tooltip
            key={i}
            title={
              <div style={{ padding: '4px 0' }}>
                <div style={{
                  fontWeight: 600,
                  fontSize: 13,
                  marginBottom: 6,
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6
                }}>
                  {kpi.icon && <span style={{ fontSize: 14 }}>{kpi.icon}</span>}
                  {kpi.label}
                </div>
                <div style={{
                  fontSize: 12,
                  lineHeight: 1.5,
                  color: 'rgba(255, 255, 255, 0.85)'
                }}>
                  {kpi.tooltip}
                </div>
              </div>
            }
            placement="top"
            overlayStyle={{ maxWidth: 320 }}
            overlayInnerStyle={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: '8px',
              padding: '12px 14px',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)'
            }}
            arrow={{
              pointAtCenter: true,
            }}
          >
            <div
              style={{
                padding: 20,
                background: 'var(--color-bg-elevated)',
                border: '1px solid var(--color-border-light)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: 'var(--shadow-sm)',
                transition: 'all 180ms cubic-bezier(0.2, 0.8, 0.2, 1)',
                cursor: 'help'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = 'var(--shadow-md)'
                e.currentTarget.style.borderColor = 'var(--color-border-medium)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = 'var(--shadow-sm)'
                e.currentTarget.style.borderColor = 'var(--color-border-light)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 12 }}>
                <span style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: 'var(--color-text-tertiary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  {kpi.label}
                </span>
                {kpi.icon && (
                  <div style={{
                    width: 32,
                    height: 32,
                    borderRadius: 'var(--radius-md)',
                    background: `${kpi.color}15`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 16,
                    color: kpi.color
                  }}>
                    {kpi.icon}
                  </div>
                )}
              </div>
              <div style={{
                fontSize: 28,
                fontWeight: 700,
                color: kpi.color,
                letterSpacing: '-0.02em',
                lineHeight: 1
              }}>
                {kpi.value}
                {kpi.suffix && (
                  <span style={{
                    fontSize: 16,
                    fontWeight: 500,
                    color: 'var(--color-text-tertiary)',
                    marginLeft: 4
                  }}>
                    {kpi.suffix}
                  </span>
                )}
              </div>
            </div>
          </Tooltip>
        ))}
      </div>

      {/* Data revelation layer (hidden by default) */}
      {!showDataLayer ? (
        <div style={{
          padding: 48,
          background: 'var(--color-bg-elevated)',
          border: '1px solid var(--color-border-light)',
          borderRadius: 'var(--radius-xl)',
          textAlign: 'center',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <p style={{
            margin: 0,
            color: 'var(--color-text-secondary)',
            fontSize: 15,
            lineHeight: 1.6
          }}>
            Charts and tables are hidden by default to reduce cognitive load.<br />
            Click <strong style={{ color: 'var(--color-accent-primary)' }}>Show Charts</strong> above to reveal detailed analytics.
          </p>
        </div>
      ) : (
        <div className="data-layer-reveal">
          <div style={{ display: 'grid', gap: 20 }}>
            {/* Charts Row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: 20 }}>
              <div style={{
                padding: 24,
                background: 'var(--color-bg-elevated)',
                border: '1px solid var(--color-border-light)',
                borderRadius: 'var(--radius-xl)',
                boxShadow: 'var(--shadow-sm)'
              }}>
                <h3 style={{
                  fontSize: 16,
                  fontWeight: 600,
                  color: 'var(--color-text-primary)',
                  marginBottom: 20,
                  letterSpacing: '-0.01em'
                }}>
                  Wait Time Over Time
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={timeseriesData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                    <XAxis
                      dataKey="time"
                      label={{ value: 'Time (min)', position: 'insideBottom', offset: -5 }}
                      tick={{ fontSize: 12, fill: 'var(--color-text-tertiary)' }}
                    />
                    <YAxis
                      label={{ value: 'Wait Time (min)', angle: -90, position: 'insideLeft' }}
                      tick={{ fontSize: 12, fill: 'var(--color-text-tertiary)' }}
                    />
                    <ChartTooltip
                      contentStyle={{
                        background: 'var(--color-bg-elevated)',
                        border: '1px solid var(--color-border-light)',
                        borderRadius: 'var(--radius-md)',
                        fontSize: 13
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 13 }} />
                    <Line
                      type="monotone"
                      dataKey="wait_time"
                      stroke="#6366f1"
                      strokeWidth={2}
                      name="Wait Time"
                      isAnimationActive={false}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div style={{
                padding: 24,
                background: 'var(--color-bg-elevated)',
                border: '1px solid var(--color-border-light)',
                borderRadius: 'var(--radius-xl)',
                boxShadow: 'var(--shadow-sm)'
              }}>
                <h3 style={{
                  fontSize: 16,
                  fontWeight: 600,
                  color: 'var(--color-text-primary)',
                  marginBottom: 20,
                  letterSpacing: '-0.01em'
                }}>
                  Charger Utilization Over Time
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={timeseriesData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                    <XAxis
                      dataKey="time"
                      label={{ value: 'Time (min)', position: 'insideBottom', offset: -5 }}
                      tick={{ fontSize: 12, fill: 'var(--color-text-tertiary)' }}
                    />
                    <YAxis
                      label={{ value: 'Utilization', angle: -90, position: 'insideLeft' }}
                      tick={{ fontSize: 12, fill: 'var(--color-text-tertiary)' }}
                    />
                    <ChartTooltip
                      contentStyle={{
                        background: 'var(--color-bg-elevated)',
                        border: '1px solid var(--color-border-light)',
                        borderRadius: 'var(--radius-md)',
                        fontSize: 13
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 13 }} />
                    <Line
                      type="monotone"
                      dataKey="utilization"
                      stroke="#10b981"
                      strokeWidth={2}
                      name="Utilization"
                      isAnimationActive={false}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Station Performance Table */}
            <div style={{
              padding: 24,
              background: 'var(--color-bg-elevated)',
              border: '1px solid var(--color-border-light)',
              borderRadius: 'var(--radius-xl)',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <h3 style={{
                fontSize: 16,
                fontWeight: 600,
                color: 'var(--color-text-primary)',
                marginBottom: 20,
                letterSpacing: '-0.01em'
              }}>
                Station Performance
              </h3>
              <Table
                columns={STATION_COLUMNS}
                dataSource={STATION_DATA}
                pagination={false}
                size="small"
                style={{ background: 'transparent' }}
              />
            </div>
          </div>

          {/* Fade/slide reveal animation (one-time; no constant motion) */}
          <style
            dangerouslySetInnerHTML={{
              __html: `
                .data-layer-reveal {
                  animation: data-layer-in 220ms cubic-bezier(0.2, 0.8, 0.2, 1) backwards;
                }
                @keyframes data-layer-in {
                  from { opacity: 0; transform: translateY(8px); }
                  to { opacity: 1; transform: translateY(0); }
                }
                @media (prefers-reduced-motion: reduce) {
                  .data-layer-reveal { animation: none !important; }
                }
              `,
            }}
          />
        </div>
      )}

      {/* Artifacts Information */}
      <div style={{
        padding: 24,
        background: 'var(--color-bg-elevated)',
        border: '1px solid var(--color-border-light)',
        borderRadius: 'var(--radius-xl)',
        marginTop: 24,
        boxShadow: 'var(--shadow-sm)'
      }}>
        <h3 style={{
          fontSize: 16,
          fontWeight: 600,
          color: 'var(--color-text-primary)',
          marginBottom: 16,
          letterSpacing: '-0.01em'
        }}>
          Simulation Artifacts
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
          {[
            { label: 'Events', value: artifacts.events || '(not available)' },
            { label: 'Frames', value: artifacts.frames || '(not available)' },
            { label: 'Summary', value: artifacts.summary || '(not available)' }
          ].map((artifact, i) => (
            <div key={i} style={{
              padding: 14,
              background: 'var(--color-bg-subtle)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border-light)'
            }}>
              <div style={{
                fontSize: 11,
                fontWeight: 600,
                color: 'var(--color-text-tertiary)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                marginBottom: 6
              }}>
                {artifact.label}
              </div>
              <Text code style={{
                fontSize: 12,
                fontFamily: 'monospace',
                background: 'var(--color-bg-elevated)',
                padding: '4px 8px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border-light)'
              }}>
                {artifact.value}
              </Text>
            </div>
          ))}
        </div>
      </div>

      {/* Drill-down panel (flat, not glass; appears only on interaction) */}
      <Drawer
        title={<span style={{ fontWeight: 600, fontSize: 16 }}>Detailed Summary</span>}
        placement="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={560}
        styles={{
          body: { padding: 24 }
        }}
      >
        <p style={{
          color: 'var(--color-text-secondary)',
          marginBottom: 24,
          fontSize: 14,
          lineHeight: 1.6
        }}>
          Raw JSON output from the simulation engine. Use this for debugging or advanced analysis.
        </p>

        <Divider style={{ borderColor: 'var(--color-border-light)' }} />

        <h4 style={{
          fontWeight: 600,
          fontSize: 14,
          color: 'var(--color-text-primary)',
          marginBottom: 12,
          marginTop: 0
        }}>
          Run Summary
        </h4>
        <pre style={{
          fontSize: 12,
          background: 'var(--color-bg-subtle)',
          padding: 16,
          borderRadius: 'var(--radius-md)',
          overflow: 'auto',
          border: '1px solid var(--color-border-light)',
          lineHeight: 1.5,
          color: 'var(--color-text-secondary)'
        }}>
          {JSON.stringify(summary, null, 2)}
        </pre>
      </Drawer>
    </div>
  )
}

export default ResultsDashboard
