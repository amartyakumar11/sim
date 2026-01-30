import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from 'antd'
import { 
  ArrowRightOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons'

function Home() {
  const navigate = useNavigate()

  const features = [
    {
      title: 'Scenario Planning',
      description: 'Model infrastructure changes before deployment',
      action: 'Create Scenario',
      path: '/submit',
      color: '#3b82f6'
    },
    {
      title: 'Live Monitoring',
      description: 'Track simulations with real-time status updates',
      action: 'View Jobs',
      path: '/monitor',
      color: '#10b981'
    },
    {
      title: 'City Visualization',
      description: 'Watch stations, queues, and charging activity',
      action: 'Open Live View',
      path: '/simulation',
      color: '#8b5cf6'
    }
  ]

  const stats = [
    { label: 'Engine Status', value: 'Ready', icon: <CheckCircleOutlined />, color: '#10b981' },
    { label: 'Mode', value: 'Real + Fake', icon: <ThunderboltOutlined />, color: '#3b82f6' },
    { label: 'Avg Response', value: '<100ms', icon: <ClockCircleOutlined />, color: '#f59e0b' }
  ]

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      {/* Hero Section */}
      <div style={{ 
        textAlign: 'center', 
        marginBottom: 64,
        paddingTop: 32
      }}>
        <div style={{
          display: 'inline-block',
          padding: '6px 14px',
          background: 'rgba(59, 130, 246, 0.08)',
          borderRadius: 'var(--radius-lg)',
          fontSize: '13px',
          fontWeight: 500,
          color: 'var(--color-accent-primary)',
          marginBottom: 20,
          letterSpacing: '0.01em'
        }}>
          EV Infrastructure Simulation Platform
        </div>
        
        <h1 style={{
          fontSize: 48,
          fontWeight: 700,
          color: 'var(--color-text-primary)',
          marginBottom: 16,
          letterSpacing: '-0.02em',
          lineHeight: 1.1
        }}>
          Test Scenarios Before <br />
          Building Infrastructure
        </h1>
        
        <p style={{
          fontSize: 18,
          color: 'var(--color-text-secondary)',
          maxWidth: 640,
          margin: '0 auto 32px',
          lineHeight: 1.6
        }}>
          Run discrete-event simulations of EV battery swapping networks. 
          Model demand, capacity, and operational costs with zero real-world risk.
        </p>

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
          <Button 
            type="primary" 
            size="large"
            onClick={() => navigate('/submit')}
            style={{ 
              height: 44,
              padding: '0 24px',
              fontSize: 15,
              fontWeight: 600
            }}
          >
            Submit Scenario
            <ArrowRightOutlined style={{ marginLeft: 4 }} />
          </Button>
          <Button 
            size="large"
            onClick={() => navigate('/simulation')}
            style={{ 
              height: 44,
              padding: '0 24px',
              fontSize: 15
            }}
          >
            Watch Live Demo
          </Button>
        </div>
      </div>

      {/* Status Bar */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 16,
        marginBottom: 48,
        padding: 20,
        background: 'var(--color-bg-elevated)',
        border: '1px solid var(--color-border-light)',
        borderRadius: 'var(--radius-xl)',
        boxShadow: 'var(--shadow-sm)'
      }}>
        {stats.map((stat, i) => (
          <div key={i} style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 12,
            padding: 8
          }}>
            <div style={{
              width: 40,
              height: 40,
              borderRadius: 'var(--radius-md)',
              background: `${stat.color}15`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 18,
              color: stat.color
            }}>
              {stat.icon}
            </div>
            <div>
              <div style={{ 
                fontSize: 12, 
                color: 'var(--color-text-tertiary)', 
                fontWeight: 500,
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}>
                {stat.label}
              </div>
              <div style={{ 
                fontSize: 16, 
                fontWeight: 600, 
                color: 'var(--color-text-primary)' 
              }}>
                {stat.value}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Feature Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: 20,
        marginBottom: 48
      }}>
        {features.map((feature, i) => (
          <div
            key={i}
            onClick={() => navigate(feature.path)}
            style={{
              padding: 28,
              background: 'var(--color-bg-elevated)',
              border: '1px solid var(--color-border-light)',
              borderRadius: 'var(--radius-xl)',
              cursor: 'pointer',
              transition: 'all 220ms cubic-bezier(0.2, 0.8, 0.2, 1)',
              boxShadow: 'var(--shadow-sm)',
              position: 'relative',
              overflow: 'hidden'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)'
              e.currentTarget.style.boxShadow = 'var(--shadow-lg)'
              e.currentTarget.style.borderColor = 'var(--color-border-medium)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = 'var(--shadow-sm)'
              e.currentTarget.style.borderColor = 'var(--color-border-light)'
            }}
          >
            <div style={{
              width: 8,
              height: 48,
              background: feature.color,
              borderRadius: 'var(--radius-sm)',
              position: 'absolute',
              left: 0,
              top: 28
            }} />
            
            <div style={{ marginLeft: 20 }}>
              <h3 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--color-text-primary)',
                marginBottom: 8,
                letterSpacing: '-0.01em'
              }}>
                {feature.title}
              </h3>
              
              <p style={{
                fontSize: 14,
                color: 'var(--color-text-secondary)',
                marginBottom: 20,
                lineHeight: 1.6
              }}>
                {feature.description}
              </p>

              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                color: feature.color,
                fontSize: 14,
                fontWeight: 600
              }}>
                {feature.action}
                <ArrowRightOutlined style={{ fontSize: 12 }} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Process Steps */}
      <div style={{
        padding: 32,
        background: 'var(--color-bg-elevated)',
        border: '1px solid var(--color-border-light)',
        borderRadius: 'var(--radius-xl)',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <h2 style={{
          fontSize: 22,
          fontWeight: 700,
          color: 'var(--color-text-primary)',
          marginBottom: 24,
          letterSpacing: '-0.01em'
        }}>
          How It Works
        </h2>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 24
        }}>
          {[
            { step: '01', title: 'Configure', desc: 'Define city layout and station capacity' },
            { step: '02', title: 'Simulate', desc: 'Run discrete-event simulation engine' },
            { step: '03', title: 'Analyze', desc: 'Review KPIs, wait times, and ROI metrics' },
            { step: '04', title: 'Optimize', desc: 'Iterate scenarios to find optimal configuration' }
          ].map((item, i) => (
            <div key={i} style={{ position: 'relative' }}>
              <div style={{
                fontSize: 48,
                fontWeight: 800,
                color: 'var(--color-bg-subtle)',
                marginBottom: 8,
                letterSpacing: '-0.04em'
              }}>
                {item.step}
              </div>
              <div style={{
                fontSize: 16,
                fontWeight: 600,
                color: 'var(--color-text-primary)',
                marginBottom: 6,
                letterSpacing: '-0.01em'
              }}>
                {item.title}
              </div>
              <div style={{
                fontSize: 14,
                color: 'var(--color-text-secondary)',
                lineHeight: 1.5
              }}>
                {item.desc}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Home
