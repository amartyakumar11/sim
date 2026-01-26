import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data)
    } else if (error.request) {
      console.error('Network Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export const simulationAPI = {
  // Submit a new scenario
  submitScenario: async (scenarioData) => {
    const response = await apiClient.post('/scenarios/submit', scenarioData)
    return response.data
  },

  // Get job status
  getJobStatus: async (runId) => {
    const response = await apiClient.get(`/jobs/${runId}/status`)
    return response.data
  },

  // Get job result
  getJobResult: async (runId) => {
    const response = await apiClient.get(`/jobs/${runId}/result`)
    return response.data
  },

  // Health check
  healthCheck: async () => {
    const response = await apiClient.get('/health')
    return response.data
  },
}

export default apiClient
