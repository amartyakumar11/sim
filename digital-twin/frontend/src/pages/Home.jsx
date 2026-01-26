import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Row, Col, Statistic, Button, Typography } from 'antd'
import { 
  ExperimentOutlined, 
  RocketOutlined, 
  ThunderboltOutlined,
  BarChartOutlined 
} from '@ant-design/icons'

const { Title, Paragraph } = Typography

function Home() {
  const navigate = useNavigate()

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <Title level={1}>🔋 Digital Twin Simulation Sandbox</Title>
        <Paragraph style={{ fontSize: 18, color: '#666' }}>
          Test EV battery swap network scenarios before implementing them in the real world
        </Paragraph>
      </div>

      <Row gutter={[24, 24]} style={{ marginBottom: 48 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Simulation Mode"
              value="Real-time"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Engine Status"
              value="Ready"
              prefix={<RocketOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Jobs"
              value="0"
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Completed"
              value="0"
              prefix={<ExperimentOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        <Col xs={24} md={12}>
          <Card
            title="🚀 Quick Start"
            hoverable
            onClick={() => navigate('/submit')}
            style={{ height: '100%', cursor: 'pointer' }}
          >
            <Paragraph>
              <strong>Submit a new scenario</strong> to test infrastructure changes, 
              demand patterns, or operational strategies before deploying them.
            </Paragraph>
            <Button type="primary" icon={<ExperimentOutlined />}>
              Create Scenario
            </Button>
          </Card>
        </Col>
        
        <Col xs={24} md={12}>
          <Card
            title="📊 Monitor Jobs"
            hoverable
            onClick={() => navigate('/monitor')}
            style={{ height: '100%', cursor: 'pointer' }}
          >
            <Paragraph>
              <strong>Track running simulations</strong> in real-time and view 
              detailed results with KPIs, charts, and network visualizations.
            </Paragraph>
            <Button type="default" icon={<BarChartOutlined />}>
              View Jobs
            </Button>
          </Card>
        </Col>
      </Row>

      <Card style={{ marginTop: 48, background: '#f9f9f9' }}>
        <Title level={4}>How It Works</Title>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <div style={{ textAlign: 'center' }}>
              <ExperimentOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              <Title level={5}>1. Define Scenario</Title>
              <Paragraph>Configure city layout, stations, and interventions</Paragraph>
            </div>
          </Col>
          <Col xs={24} md={8}>
            <div style={{ textAlign: 'center' }}>
              <RocketOutlined style={{ fontSize: 48, color: '#52c41a' }} />
              <Title level={5}>2. Run Simulation</Title>
              <Paragraph>SimPy-based discrete event simulation processes your scenario</Paragraph>
            </div>
          </Col>
          <Col xs={24} md={8}>
            <div style={{ textAlign: 'center' }}>
              <BarChartOutlined style={{ fontSize: 48, color: '#faad14' }} />
              <Title level={5}>3. Analyze Results</Title>
              <Paragraph>View KPIs, charts, and network metrics</Paragraph>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default Home
