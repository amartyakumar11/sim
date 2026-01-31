import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { Layout } from 'antd'
import ScenarioSubmission from './pages/ScenarioSubmission'
import JobMonitor from './pages/JobMonitor'
import ResultsDashboard from './pages/ResultsDashboard'
import SimulationScene from './pages/SimulationScene'
import CityVisualization from './pages/CityVisualization'
import Home from './pages/Home'
import './App.css'

const { Header, Content, Footer } = Layout

const NAV_ITEMS = [
  { key: 'home', path: '/', label: 'Overview' },
  { key: 'simulation', path: '/simulation', label: 'Live View' },
  { key: 'city-map', path: '/city-map', label: 'City Map' },
  { key: 'submit', path: '/submit', label: 'New Scenario' },
  { key: 'monitor', path: '/monitor', label: 'Jobs' },
  { key: 'results', path: '/results', label: 'Results' },
]

function Navigation() {
  const location = useLocation()
  const currentPath = location.pathname

  return (
    <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      {NAV_ITEMS.map(item => {
        const isActive = currentPath === item.path ||
          (item.path !== '/' && currentPath.startsWith(item.path))
        return (
          <Link
            key={item.key}
            to={item.path}
            style={{
              padding: '8px 16px',
              borderRadius: 'var(--radius-md)',
              fontSize: '14px',
              fontWeight: 500,
              color: isActive ? 'var(--color-accent-primary)' : 'var(--color-text-secondary)',
              background: isActive ? 'rgba(59, 130, 246, 0.08)' : 'transparent',
              textDecoration: 'none',
              transition: 'all 160ms cubic-bezier(0.25, 0.1, 0.25, 1)',
              display: 'inline-block'
            }}
            onMouseEnter={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = 'var(--color-bg-subtle)'
                e.currentTarget.style.color = 'var(--color-text-primary)'
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = 'transparent'
                e.currentTarget.style.color = 'var(--color-text-secondary)'
              }
            }}
          >
            {item.label}
          </Link>
        )
      })}
    </nav>
  )
}

function App() {
  return (
    <Router>
      <Layout className="app-layout">
        <Header style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 32px',
          background: 'var(--color-bg-elevated)',
          borderBottom: '1px solid var(--color-border-light)',
          height: '64px',
          lineHeight: '64px'
        }}>
          <div className="logo">
            <div className="logo-icon">DT</div>
            <span>Digital Twin</span>
          </div>
          <Navigation />
        </Header>

        <Content className="content-wrapper">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/simulation" element={<SimulationScene />} />
            <Route path="/city-map" element={<CityVisualization />} />
            <Route path="/submit" element={<ScenarioSubmission />} />
            <Route path="/monitor" element={<JobMonitor />} />
            <Route path="/results/:runId" element={<ResultsDashboard />} />
            <Route path="/results" element={<ResultsDashboard />} />
          </Routes>
        </Content>

        <Footer style={{
          textAlign: 'center',
          background: 'var(--color-bg-elevated)',
          borderTop: '1px solid var(--color-border-light)',
          color: 'var(--color-text-tertiary)',
          fontSize: '13px',
          padding: '24px 32px'
        }}>
          Digital Twin Simulation Platform © {new Date().getFullYear()} · Built with React + FastAPI
        </Footer>
      </Layout>
    </Router>
  )
}

export default App
