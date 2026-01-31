import React, { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Table,
  Tag,
  Button,
  Space,
  Progress,
  Typography,
  message,
  Modal,
  Descriptions
} from 'antd'
import {
  ReloadOutlined,
  EyeOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,

  LoadingOutlined,
  BarChartOutlined
} from '@ant-design/icons'
import { simulationAPI } from '../services/api'

const { Title, Text } = Typography

function JobMonitor() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [jobs, setJobs] = useState([])
  const [selectedJob, setSelectedJob] = useState(null)
  const [detailsVisible, setDetailsVisible] = useState(false)
  const [loading, setLoading] = useState(false)
  const runIdFromUrl = searchParams.get('runId')

  // Auto-refresh job status
  useEffect(() => {
    if (runIdFromUrl) {
      fetchJobStatus(runIdFromUrl)
      const interval = setInterval(() => {
        fetchJobStatus(runIdFromUrl)
      }, 3000) // Poll every 3 seconds

      return () => clearInterval(interval)
    }
  }, [runIdFromUrl])

  const fetchJobStatus = async (runId) => {
    try {
      const status = await simulationAPI.getJobStatus(runId)

      // Update or add job to list
      setJobs(prevJobs => {
        const existingIndex = prevJobs.findIndex(j => j.run_id === runId)
        if (existingIndex >= 0) {
          const updated = [...prevJobs]
          updated[existingIndex] = status
          return updated
        } else {
          return [status, ...prevJobs]
        }
      })

      // If job is completed, show success message
      if (status.status === 'completed') {
        message.success(`Job ${runId} completed successfully!`)
      } else if (status.status === 'failed') {
        message.error(`Job ${runId} failed: ${status.message}`)
      }
    } catch (error) {
      console.error('Failed to fetch job status:', error)
    }
  }

  const refreshJobs = () => {
    setLoading(true)
    jobs.forEach(job => fetchJobStatus(job.run_id))
    setTimeout(() => setLoading(false), 1000)
  }

  const viewDetails = (job) => {
    setSelectedJob(job)
    setDetailsVisible(true)
  }

  const viewResults = (runId) => {
    navigate(`/city-map?runId=${runId}`)
  }

  const viewDashboard = (runId) => {
    navigate(`/results/${runId}`)
  }

  const getStatusTag = (status) => {
    const statusConfig = {
      submitted: { color: 'default', icon: <ClockCircleOutlined /> },
      running: { color: 'processing', icon: <LoadingOutlined /> },
      completed: { color: 'success', icon: <CheckCircleOutlined /> },
      failed: { color: 'error', icon: <CloseCircleOutlined /> },
      cancelled: { color: 'warning', icon: <CloseCircleOutlined /> }
    }

    const config = statusConfig[status] || statusConfig.submitted
    return (
      <Tag color={config.color} icon={config.icon}>
        {status.toUpperCase()}
      </Tag>
    )
  }

  const columns = [
    {
      title: 'Run ID',
      dataIndex: 'run_id',
      key: 'run_id',
      width: 280,
      render: (text) => <Text code copyable>{text.substring(0, 8)}...</Text>
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) => getStatusTag(status)
    },
    {
      title: 'Progress',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress) => (
        <Progress
          percent={progress ? Math.round(progress * 100) : 0}
          size="small"
          status={progress === 1 ? 'success' : 'active'}
        />
      )
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date) => new Date(date).toLocaleString()
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 180,
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => viewDetails(record)}
          >
            Details
          </Button>
          {record.status === 'completed' && (
            <>
              <Button
                size="small"
                icon={<BarChartOutlined />}
                onClick={() => viewDashboard(record.run_id)}
              >
                Results
              </Button>
              <Button
                size="small"
                type="primary"
                onClick={() => viewResults(record.run_id)}
              >
                Map
              </Button>
            </>
          )}
        </Space>
      )
    }
  ]

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 32
      }}>
        <div>
          <h1 style={{
            fontSize: 32,
            fontWeight: 700,
            color: 'var(--color-text-primary)',
            marginBottom: 4,
            letterSpacing: '-0.02em'
          }}>
            Job Monitor
          </h1>
          <p style={{
            fontSize: 15,
            color: 'var(--color-text-secondary)',
            margin: 0
          }}>
            Track all simulation runs and their execution status
          </p>
        </div>
        <Button
          icon={<ReloadOutlined />}
          onClick={refreshJobs}
          loading={loading}
          style={{
            borderRadius: 'var(--radius-md)',
            height: 38
          }}
        >
          Refresh
        </Button>
      </div>

      {/* Table Card */}
      <div style={{
        background: 'var(--color-bg-elevated)',
        border: '1px solid var(--color-border-light)',
        borderRadius: 'var(--radius-xl)',
        overflow: 'hidden',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <Table
          columns={columns}
          dataSource={jobs}
          rowKey="run_id"
          pagination={{
            pageSize: 10,
            showSizeChanger: false,
            style: { padding: '16px 24px' }
          }}
          locale={{ emptyText: 'No jobs yet. Submit a scenario to get started.' }}
          style={{
            background: 'transparent'
          }}
        />
      </div>

      <Modal
        title={<span style={{ fontWeight: 600, fontSize: 16 }}>Job Details</span>}
        open={detailsVisible}
        onCancel={() => setDetailsVisible(false)}
        footer={[
          <Button
            key="close"
            onClick={() => setDetailsVisible(false)}
            style={{ borderRadius: 'var(--radius-md)' }}
          >
            Close
          </Button>,
          selectedJob?.status === 'completed' && (
            <>
              <Button
                key="dashboard"
                icon={<BarChartOutlined />}
                onClick={() => {
                  setDetailsVisible(false)
                  viewDashboard(selectedJob.run_id)
                }}
                style={{ borderRadius: 'var(--radius-md)' }}
              >
                View Results
              </Button>
              <Button
                key="results"
                type="primary"
                onClick={() => {
                  setDetailsVisible(false)
                  viewResults(selectedJob.run_id)
                }}
                style={{ borderRadius: 'var(--radius-md)' }}
              >
                View on Map
              </Button>
            </>
          )
        ]}
        width={700}
        style={{ borderRadius: 'var(--radius-xl)' }}
      >
        {selectedJob && (
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="Run ID">
              <Text code copyable>{selectedJob.run_id}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="Status">
              {getStatusTag(selectedJob.status)}
            </Descriptions.Item>
            <Descriptions.Item label="Progress">
              <Progress
                percent={selectedJob.progress ? Math.round(selectedJob.progress * 100) : 0}
                status={selectedJob.status === 'completed' ? 'success' :
                  selectedJob.status === 'failed' ? 'exception' : 'active'}
                strokeColor={selectedJob.status === 'completed' ? 'var(--color-accent-success)' : 'var(--color-accent-primary)'}
              />
            </Descriptions.Item>
            <Descriptions.Item label="Message">
              {selectedJob.message}
            </Descriptions.Item>
            <Descriptions.Item label="Created At">
              {new Date(selectedJob.created_at).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="Updated At">
              {new Date(selectedJob.updated_at).toLocaleString()}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

export default JobMonitor
