/**
 * Project Service - Handles all project-related API operations
 */
class ProjectService {
  constructor() {
    this.baseUrl = '/api/projects'
  }

  /**
   * Get all projects
   * @returns {Promise<Array>} Array of project objects
   */
  async getAllProjects() {
    try {
      const response = await fetch(this.baseUrl)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      return data.projects || []
    } catch (error) {
      console.error('Failed to fetch projects:', error)
      throw error
    }
  }

  /**
   * Get a specific project by ID
   * @param {string} projectId - The project ID
   * @returns {Promise<Object>} Project object
   */
  async getProject(projectId) {
    try {
      const response = await fetch(`${this.baseUrl}/${projectId}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error(`Failed to fetch project ${projectId}:`, error)
      throw error
    }
  }

  /**
   * Create a new project
   * @param {Object} projectData - Project configuration data
   * @returns {Promise<Object>} Created project object
   */
  async createProject(projectData) {
    try {
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(projectData)
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Failed to create project:', error)
      throw error
    }
  }

  /**
   * Update an existing project
   * @param {string} projectId - The project ID
   * @param {Object} projectData - Updated project data
   * @returns {Promise<Object>} Updated project object
   */
  async updateProject(projectId, projectData) {
    try {
      const response = await fetch(`${this.baseUrl}/${projectId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(projectData)
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error(`Failed to update project ${projectId}:`, error)
      throw error
    }
  }

  /**
   * Delete a project
   * @param {string} projectId - The project ID
   * @returns {Promise<void>}
   */
  async deleteProject(projectId) {
    try {
      const response = await fetch(`${this.baseUrl}/${projectId}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`)
      }
    } catch (error) {
      console.error(`Failed to delete project ${projectId}:`, error)
      throw error
    }
  }

  /**
   * Start a project
   * @param {string} projectId - The project ID
   * @returns {Promise<Object>} Operation result
   */
  async startProject(projectId) {
    try {
      const response = await fetch(`${this.baseUrl}/${projectId}/start`, {
        method: 'POST'
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error(`Failed to start project ${projectId}:`, error)
      throw error
    }
  }

  /**
   * Stop a project
   * @param {string} projectId - The project ID
   * @returns {Promise<Object>} Operation result
   */
  async stopProject(projectId) {
    try {
      const response = await fetch(`${this.baseUrl}/${projectId}/stop`, {
        method: 'POST'
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error(`Failed to stop project ${projectId}:`, error)
      throw error
    }
  }

  /**
   * Restart a project
   * @param {string} projectId - The project ID
   * @returns {Promise<Object>} Operation result
   */
  async restartProject(projectId) {
    try {
      const response = await fetch(`${this.baseUrl}/${projectId}/restart`, {
        method: 'POST'
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error(`Failed to restart project ${projectId}:`, error)
      throw error
    }
  }

  /**
   * Get project status
   * @param {string} projectId - The project ID
   * @returns {Promise<Object>} Project status information
   */
  async getProjectStatus(projectId) {
    try {
      const response = await fetch(`${this.baseUrl}/${projectId}/status`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error(`Failed to get project status ${projectId}:`, error)
      throw error
    }
  }

  /**
   * Get project logs
   * @param {string} projectId - The project ID
   * @param {Object} options - Log options (lines, follow, etc.)
   * @returns {Promise<Object>} Project logs
   */
  async getProjectLogs(projectId, options = {}) {
    try {
      const params = new URLSearchParams()
      if (options.lines) params.append('lines', options.lines)
      if (options.follow) params.append('follow', options.follow)
      if (options.since) params.append('since', options.since)
      
      const url = `${this.baseUrl}/${projectId}/logs${params.toString() ? '?' + params.toString() : ''}`
      const response = await fetch(url)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error(`Failed to get project logs ${projectId}:`, error)
      throw error
    }
  }

  /**
   * Get project health status
   * @param {string} projectId - The project ID
   * @returns {Promise<Object>} Health status information
   */
  async getProjectHealth(projectId) {
    try {
      const response = await fetch(`${this.baseUrl}/${projectId}/health`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error(`Failed to get project health ${projectId}:`, error)
      throw error
    }
  }

  /**
   * Validate project configuration
   * @param {Object} projectData - Project configuration to validate
   * @returns {Promise<Object>} Validation result
   */
  async validateProject(projectData) {
    try {
      const response = await fetch(`${this.baseUrl}/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(projectData)
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Failed to validate project:', error)
      throw error
    }
  }

  /**
   * Discover projects in a directory
   * @param {string} directory - Directory path to scan
   * @returns {Promise<Array>} Array of discovered project configurations
   */
  async discoverProjects(directory) {
    try {
      const response = await fetch(`${this.baseUrl}/discover`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ directory })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      return data.projects || []
    } catch (error) {
      console.error('Failed to discover projects:', error)
      throw error
    }
  }

  /**
   * Get available project templates
   * @returns {Promise<Array>} Array of project templates
   */
  async getProjectTemplates() {
    try {
      const response = await fetch(`${this.baseUrl}/templates`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      return data.templates || []
    } catch (error) {
      console.error('Failed to fetch project templates:', error)
      throw error
    }
  }

  /**
   * Create project from template
   * @param {string} templateId - Template ID
   * @param {Object} projectData - Project configuration
   * @returns {Promise<Object>} Created project object
   */
  async createFromTemplate(templateId, projectData) {
    try {
      const response = await fetch(`${this.baseUrl}/templates/${templateId}/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(projectData)
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error(`Failed to create project from template ${templateId}:`, error)
      throw error
    }
  }

  /**
   * Export project configuration
   * @param {string} projectId - The project ID
   * @returns {Promise<Object>} Exported configuration
   */
  async exportProject(projectId) {
    try {
      const response = await fetch(`${this.baseUrl}/${projectId}/export`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error(`Failed to export project ${projectId}:`, error)
      throw error
    }
  }

  /**
   * Import project configuration
   * @param {Object} configData - Project configuration to import
   * @returns {Promise<Object>} Imported project object
   */
  async importProject(configData) {
    try {
      const response = await fetch(`${this.baseUrl}/import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(configData)
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Failed to import project:', error)
      throw error
    }
  }
}

// Export singleton instance
export { ProjectService }
export default new ProjectService()
