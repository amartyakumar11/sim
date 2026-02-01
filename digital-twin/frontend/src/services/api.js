import axios from 'axios'

// In production (when served via nginx), use relative URLs
// In development, use localhost:8000
const getApiBaseUrl = () => {
  // If VITE_API_URL is explicitly set, use it
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  
  // In production (non-localhost), use relative path (nginx will proxy)
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    return '/api'
  }
  
  // Development default
  return 'http://localhost:8000/api'
}

const API_BASE_URL = getApiBaseUrl()

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

  // Level 2: Analytics
  getDemandHeatmap: async (scenarioConfig) => {
    const response = await apiClient.post('/analytics/demand-heatmap', scenarioConfig)
    return response.data
  },

  getCoverage: async (scenarioConfig) => {
    const response = await apiClient.post('/analytics/coverage', scenarioConfig)
    return response.data
  },

  getRecommendations: async (scenarioConfig) => {
    const response = await apiClient.post('/analytics/recommendations', scenarioConfig)
    return response.data
  },

  getForecast: async (scenarioConfig) => {
    // Expects scenarioConfig.description to contain "forecast_request:ST_ID"
    const response = await apiClient.post('/analytics/forecast', scenarioConfig)
    return response.data
  },
}

export default apiClient
