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
  LoadingOutlined
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
            <Button 
              size="small" 
              type="primary"
              onClick={() => viewResults(record.run_id)}
            >
              Results
            </Button>
          )}
        </Space>
      )
    }
  ]

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <Title level={2} style={{ margin: 0 }}>📊 Job Monitor</Title>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={refreshJobs}
            loading={loading}
          >
            Refresh
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={jobs}
          rowKey="run_id"
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: 'No jobs found. Submit a scenario to get started.' }}
        />
      </Card>

      <Modal
        title="Job Details"
        open={detailsVisible}
        onCancel={() => setDetailsVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailsVisible(false)}>
            Close
          </Button>,
          selectedJob?.status === 'completed' && (
            <Button 
              key="results" 
              type="primary"
              onClick={() => {
                setDetailsVisible(false)
                viewResults(selectedJob.run_id)
              }}
            >
              View Results
            </Button>
          )
        ]}
        width={700}
      >
        {selectedJob && (
          <Descriptions bordered column={1}>
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
