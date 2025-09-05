/**
 * WSL2 API Service
 * 
 * Handles all HTTP requests to the WSL2 backend API
 */

class WSL2ApiService {
  constructor() {
    this.baseUrl = '/api/wsl2'
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    }

    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body)
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`)
      }

      return data
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error)
      throw error
    }
  }

  // WSL2 Instances
  async getInstances() {
    return this.request('/instances')
  }

  async startInstance(instanceName) {
    return this.request('/instances', {
      method: 'POST',
      body: {
        instance_name: instanceName,
        action: 'start'
      }
    })
  }

  async stopInstance(instanceName) {
    return this.request('/instances', {
      method: 'POST',
      body: {
        instance_name: instanceName,
        action: 'stop'
      }
    })
  }

  // Projects
  async getProjects(filters = {}) {
    const params = new URLSearchParams()
    if (filters.instance) params.append('instance', filters.instance)
    if (filters.type) params.append('type', filters.type)
    if (filters.status) params.append('status', filters.status)
    
    const query = params.toString()
    return this.request(`/projects${query ? '?' + query : ''}`)
  }

  async getProject(projectId) {
    return this.request(`/projects/${projectId}`)
  }

  async createProject(projectData) {
    return this.request('/projects', {
      method: 'POST',
      body: projectData
    })
  }

  async updateProject(projectData) {
    return this.request('/projects', {
      method: 'POST',
      body: projectData
    })
  }

  async deleteProject(projectId) {
    return this.request(`/projects/${projectId}`, {
      method: 'DELETE'
    })
  }

  // Project Actions
  async startProject(projectId) {
    return this.request(`/projects/${projectId}/start`, {
      method: 'POST'
    })
  }

  async stopProject(projectId) {
    return this.request(`/projects/${projectId}/stop`, {
      method: 'POST'
    })
  }

  async restartProject(projectId) {
    return this.request(`/projects/${projectId}/restart`, {
      method: 'POST'
    })
  }

  // Bulk Actions
  async bulkStartProjects(filters = {}) {
    return this.request('/bulk/start', {
      method: 'POST',
      body: filters
    })
  }

  async bulkStopProjects(filters = {}) {
    return this.request('/bulk/stop', {
      method: 'POST',
      body: filters
    })
  }

  // Discovery
  async discoverProjects(options = {}) {
    return this.request('/discovery', {
      method: 'POST',
      body: {
        instance_name: options.instanceName,
        scan_path: options.scanPath || '/home',
        max_depth: options.maxDepth || 3
      }
    })
  }

  // Port Monitoring
  async getPortUsage(instanceName = null) {
    const params = instanceName ? `?instance=${instanceName}` : ''
    return this.request(`/ports${params}`)
  }

  // Health Monitoring
  async getHealthStatus(projectId = null) {
    const params = projectId ? `?project_id=${projectId}` : ''
    return this.request(`/health${params}`)
  }

  // Configuration
  async getConfigTemplate() {
    return this.request('/config/template')
  }

  async validateConfig(config) {
    return this.request('/config/template', {
      method: 'POST',
      body: config
    })
  }
}

export const wsl2Api = new WSL2ApiService()
