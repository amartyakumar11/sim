import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  ExperimentOutlined,
  DashboardOutlined,
  HistoryOutlined,
  EnvironmentOutlined,
} from '@ant-design/icons'
import ScenarioSubmission from './pages/ScenarioSubmission'
import JobMonitor from './pages/JobMonitor'
import ResultsDashboard from './pages/ResultsDashboard'
import SimulationScene from './pages/SimulationScene'
import Home from './pages/Home'
import './App.css'

const { Header, Content, Footer } = Layout

function App() {
  return (
    <Router>
      <Layout className="app-layout">
        <Header style={{ display: 'flex', alignItems: 'center' }}>
          <div className="logo" style={{ color: 'white', fontSize: '20px', fontWeight: 'bold', marginRight: '50px' }}>
            🔋 Digital Twin Sandbox
          </div>
          <Menu
            theme="dark"
            mode="horizontal"
            defaultSelectedKeys={['home']}
            style={{ flex: 1, minWidth: 0 }}
          >
            <Menu.Item key="home" icon={<DashboardOutlined />}>
              <Link to="/">Home</Link>
            </Menu.Item>
            <Menu.Item key="simulation" icon={<EnvironmentOutlined />}>
              <Link to="/simulation">Simulation</Link>
            </Menu.Item>
            <Menu.Item key="submit" icon={<ExperimentOutlined />}>
              <Link to="/submit">Submit Scenario</Link>
            </Menu.Item>
            <Menu.Item key="monitor" icon={<HistoryOutlined />}>
              <Link to="/monitor">Job Monitor</Link>
            </Menu.Item>
            <Menu.Item key="results" icon={<EnvironmentOutlined />}>
              <Link to="/results">Results</Link>
            </Menu.Item>
          </Menu>
        </Header>
        
        <Content className="content-wrapper">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/simulation" element={<SimulationScene />} />
            <Route path="/submit" element={<ScenarioSubmission />} />
            <Route path="/monitor" element={<JobMonitor />} />
            <Route path="/results/:runId" element={<ResultsDashboard />} />
            <Route path="/results" element={<ResultsDashboard />} />
          </Routes>
        </Content>
        
        <Footer style={{ textAlign: 'center' }}>
          Digital Twin Simulation Sandbox ©{new Date().getFullYear()} | 
          Built with React + FastAPI
        </Footer>
      </Layout>
    </Router>
  )
}

export default App
