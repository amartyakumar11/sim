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
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'
import { simulationAPI } from '../services/api'

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

  // Generate static mock timeseries only when user reveals data layer.
  // (No live updates; no continuous visual animation.)
  useEffect(() => {
    if (!showDataLayer) return
    if (timeseriesData.length > 0) return

    const generated = Array.from({ length: 20 }, (_, i) => ({
      time: i * 3,
      wait_time: 5 + Math.random() * 10,
      utilization: 0.4 + Math.random() * 0.3,
    }))
    setTimeseriesData(generated)
  }, [showDataLayer, timeseriesData.length])

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
  const artifacts = result?.artifacts || {}
  const runIdShort = useMemo(() => {
    const s = String(runIdFromParams || '')
    return s.length > 10 ? `${s.substring(0, 8)}…` : s
  }, [runIdFromParams])

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>Simulation Results</Title>
            <Text type="secondary">
              Run ID: <Text code>{runIdShort}</Text>
            </Text>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Button
              type={showDataLayer ? 'default' : 'primary'}
              onClick={() => setShowDataLayer(v => !v)}
            >
              {showDataLayer ? 'Hide data layer' : 'Reveal data layer'}
            </Button>
            <Button onClick={() => setDrawerOpen(true)}>Drill-down</Button>
            <Tag color="success" icon={<CheckCircleOutlined />}>COMPLETED</Tag>
          </div>
        </div>
      </Card>

      {/* KPI Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Avg Wait Time"
              value={formatFixed(summary.avg_wait_time, 2)}
              suffix="min"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: (asNumber(summary.avg_wait_time) ?? 0) > 10 ? '#cf1322' : '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Lost Swaps"
              value={asNumber(summary.lost_swaps) ?? 0}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Charger Utilization"
              value={((asNumber(summary.charger_utilization) ?? 0) * 100).toFixed(1)}
              suffix="%"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="City Throughput"
              value={asNumber(summary.city_throughput) ?? 0}
              suffix="swaps"
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Idle Inventory"
              value={formatFixed(summary.idle_inventory, 1)}
              suffix="%"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Cost Impact"
              value={formatFixed(summary.total_cost_impact, 2)}
              prefix={<DollarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="ROI"
              value={((asNumber(summary.roi) ?? 0) * 100).toFixed(1)}
              suffix="%"
              valueStyle={{ color: (asNumber(summary.roi) ?? 0) > 0.2 ? '#3f8600' : '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Events Logged"
              value={asNumber(result.events_count) ?? 0}
            />
          </Card>
        </Col>
      </Row>

      {/* Data revelation layer (hidden by default) */}
      {!showDataLayer ? (
        <Card style={{ marginTop: 8 }}>
          <Paragraph style={{ margin: 0, color: '#555' }}>
            Data visualizations are hidden by default. Click <Text strong>Reveal data layer</Text> to show charts and tables.
          </Paragraph>
        </Card>
      ) : (
        <div className="data-layer-reveal">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="Wait Time Over Time" style={{ background: '#fff' }}>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={timeseriesData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" label={{ value: 'Time (min)', position: 'insideBottom', offset: -5 }} />
                    <YAxis label={{ value: 'Wait Time (min)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="wait_time"
                      stroke="#6366f1"
                      name="Wait Time"
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Charger Utilization Over Time" style={{ background: '#fff' }}>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={timeseriesData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" label={{ value: 'Time (min)', position: 'insideBottom', offset: -5 }} />
                    <YAxis label={{ value: 'Utilization', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="utilization"
                      stroke="#10b981"
                      name="Utilization"
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </Col>

            <Col xs={24}>
              <Card title="Station Performance (table)" style={{ background: '#fff' }}>
                <Table
                  columns={STATION_COLUMNS}
                  dataSource={STATION_DATA}
                  pagination={false}
                  size="small"
                />
              </Card>
            </Col>
          </Row>

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
      <Card style={{ marginTop: 24 }}>
        <Title level={4}>Simulation Artifacts</Title>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Text strong>Events:</Text> <Text code>{artifacts.events || '(not available)'}</Text>
          </Col>
          <Col xs={24} md={8}>
            <Text strong>Frames:</Text> <Text code>{artifacts.frames || '(not available)'}</Text>
          </Col>
          <Col xs={24} md={8}>
            <Text strong>Summary:</Text> <Text code>{artifacts.summary || '(not available)'}</Text>
          </Col>
        </Row>
      </Card>

      {/* Drill-down panel (flat, not glass; appears only on interaction) */}
      <Drawer
        title="Drill-down"
        placement="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={520}
      >
        <Paragraph style={{ color: '#555' }}>
          This panel is a progressive disclosure surface. It stays hidden until opened and should be used for deeper
          inspection without overwhelming the main view.
        </Paragraph>

        <Divider />
        <Title level={5} style={{ marginTop: 0 }}>Run summary (raw)</Title>
        <pre style={{ fontSize: 12, background: '#f8fafc', padding: 12, borderRadius: 8, overflow: 'auto' }}>
{JSON.stringify(summary, null, 2)}
        </pre>
      </Drawer>
    </div>
  )
}

export default ResultsDashboard
