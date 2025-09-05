<template>
  <div class="wsl2-dashboard">
    <!-- Header -->
    <div class="dashboard-header">
      <h1 class="dashboard-title">
        <i class="fas fa-server"></i>
        WSL2 Project Manager
      </h1>
      <div class="dashboard-stats">
        <div class="stat-card">
          <div class="stat-value">{{ totalProjects }}</div>
          <div class="stat-label">Total Projects</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ runningProjects }}</div>
          <div class="stat-label">Running</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ totalInstances }}</div>
          <div class="stat-label">WSL2 Instances</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ portConflicts }}</div>
          <div class="stat-label">Port Conflicts</div>
        </div>
      </div>
    </div>

    <!-- Action Bar -->
    <div class="action-bar">
      <div class="action-group">
        <button class="btn btn-primary" @click="discoverProjects">
          <i class="fas fa-search"></i>
          Discover Projects
        </button>
        <button class="btn btn-success" @click="startAllProjects">
          <i class="fas fa-play"></i>
          Start All
        </button>
        <button class="btn btn-warning" @click="stopAllProjects">
          <i class="fas fa-stop"></i>
          Stop All
        </button>
        <button class="btn btn-info" @click="refreshData">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': isRefreshing }"></i>
          Refresh
        </button>
      </div>
      
      <div class="filter-group">
        <select v-model="selectedInstance" @change="filterProjects" class="form-select">
          <option value="">All Instances</option>
          <option v-for="instance in instances" :key="instance.name" :value="instance.name">
            {{ instance.name }} ({{ instance.status }})
          </option>
        </select>
        
        <select v-model="selectedType" @change="filterProjects" class="form-select">
          <option value="">All Types</option>
          <option value="nodejs">Node.js</option>
          <option value="python">Python</option>
          <option value="docker">Docker</option>
          <option value="go">Go</option>
          <option value="java">Java</option>
          <option value="dotnet">.NET</option>
          <option value="generic">Generic</option>
        </select>
        
        <select v-model="selectedStatus" @change="filterProjects" class="form-select">
          <option value="">All Status</option>
          <option value="running">Running</option>
          <option value="stopped">Stopped</option>
          <option value="starting">Starting</option>
          <option value="stopping">Stopping</option>
          <option value="error">Error</option>
        </select>
      </div>
    </div>

    <!-- Main Content -->
    <div class="dashboard-content">
      <!-- Projects Grid -->
      <div class="projects-section">
        <h2 class="section-title">
          <i class="fas fa-folder-open"></i>
          Projects ({{ filteredProjects.length }})
        </h2>
        
        <div class="projects-grid" v-if="filteredProjects.length > 0">
          <WSL2ProjectCard
            v-for="project in filteredProjects"
            :key="project.id"
            :project="project"
            @start="startProject"
            @stop="stopProject"
            @restart="restartProject"
            @delete="deleteProject"
            @edit="editProject"
          />
        </div>
        
        <div v-else class="empty-state">
          <i class="fas fa-folder-open fa-3x"></i>
          <h3>No Projects Found</h3>
          <p>Click "Discover Projects" to automatically find projects in your WSL2 instances.</p>
          <button class="btn btn-primary" @click="discoverProjects">
            <i class="fas fa-search"></i>
            Discover Projects
          </button>
        </div>
      </div>

      <!-- Side Panel -->
      <div class="side-panel">
        <!-- WSL2 Instances -->
        <div class="panel-section">
          <h3 class="panel-title">
            <i class="fas fa-server"></i>
            WSL2 Instances
          </h3>
          <div class="instance-list">
            <div
              v-for="instance in instances"
              :key="instance.name"
              class="instance-item"
              :class="{ 'running': instance.status === 'Running', 'stopped': instance.status === 'Stopped' }"
            >
              <div class="instance-info">
                <div class="instance-name">{{ instance.name }}</div>
                <div class="instance-status">{{ instance.status }}</div>
              </div>
              <div class="instance-actions">
                <button
                  v-if="instance.status === 'Stopped'"
                  class="btn btn-sm btn-success"
                  @click="startInstance(instance.name)"
                >
                  <i class="fas fa-play"></i>
                </button>
                <button
                  v-if="instance.status === 'Running'"
                  class="btn btn-sm btn-warning"
                  @click="stopInstance(instance.name)"
                >
                  <i class="fas fa-stop"></i>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Port Monitor -->
        <div class="panel-section">
          <h3 class="panel-title">
            <i class="fas fa-network-wired"></i>
            Port Monitor
          </h3>
          <div class="port-stats">
            <div class="port-stat">
              <span class="port-count">{{ totalPortsInUse }}</span>
              <span class="port-label">Ports in Use</span>
            </div>
            <div class="port-stat" v-if="portConflicts > 0">
              <span class="port-count conflict">{{ portConflicts }}</span>
              <span class="port-label">Conflicts</span>
            </div>
          </div>
          
          <div v-if="portConflictsList.length > 0" class="conflict-list">
            <div v-for="conflict in portConflictsList" :key="conflict.port" class="conflict-item">
              <i class="fas fa-exclamation-triangle"></i>
              Port {{ conflict.port }} conflict
            </div>
          </div>
        </div>

        <!-- Health Monitor -->
        <div class="panel-section">
          <h3 class="panel-title">
            <i class="fas fa-heartbeat"></i>
            Health Monitor
          </h3>
          <div class="health-stats">
            <div class="health-stat healthy">
              <span class="health-count">{{ healthyProjects }}</span>
              <span class="health-label">Healthy</span>
            </div>
            <div class="health-stat unhealthy" v-if="unhealthyProjects > 0">
              <span class="health-count">{{ unhealthyProjects }}</span>
              <span class="health-label">Unhealthy</span>
            </div>
          </div>
          
          <div v-if="unhealthyProjectsList.length > 0" class="unhealthy-list">
            <div v-for="project in unhealthyProjectsList" :key="project.project_id" class="unhealthy-item">
              <i class="fas fa-exclamation-circle"></i>
              {{ project.project.name }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <WSL2ProjectModal
      v-if="showProjectModal"
      :project="selectedProject"
      :mode="modalMode"
      @save="saveProject"
      @close="closeProjectModal"
    />

    <WSL2DiscoveryModal
      v-if="showDiscoveryModal"
      @discover="handleDiscovery"
      @close="closeDiscoveryModal"
    />

    <!-- Connection Status -->
    <div class="connection-status" :class="{ 'connected': wsConnected, 'disconnected': !wsConnected }">
      <i class="fas" :class="wsConnected ? 'fa-wifi' : 'fa-wifi-slash'"></i>
      {{ wsConnected ? 'Connected' : 'Disconnected' }}
    </div>
  </div>
</template>

<script>
import WSL2ProjectCard from './WSL2ProjectCard.vue'
import WSL2ProjectModal from './WSL2ProjectModal.vue'
import WSL2DiscoveryModal from './WSL2DiscoveryModal.vue'
import { wsl2Api } from '../../services/wsl2Api'
import { wsl2WebSocket } from '../../services/wsl2WebSocket'

export default {
  name: 'WSL2Dashboard',
  components: {
    WSL2ProjectCard,
    WSL2ProjectModal,
    WSL2DiscoveryModal
  },
  data() {
    return {
      // Data
      projects: [],
      instances: [],
      portUsage: {},
      portConflictsList: [],
      healthData: {},
      unhealthyProjectsList: [],
      
      // Filters
      selectedInstance: '',
      selectedType: '',
      selectedStatus: '',
      
      // UI State
      isRefreshing: false,
      showProjectModal: false,
      showDiscoveryModal: false,
      selectedProject: null,
      modalMode: 'create', // 'create' or 'edit'
      
      // WebSocket
      wsConnected: false
    }
  },
  computed: {
    filteredProjects() {
      return this.projects.filter(project => {
        if (this.selectedInstance && project.wsl_instance !== this.selectedInstance) {
          return false
        }
        if (this.selectedType && project.project_type !== this.selectedType) {
          return false
        }
        if (this.selectedStatus && project.status !== this.selectedStatus) {
          return false
        }
        return true
      })
    },
    totalProjects() {
      return this.projects.length
    },
    runningProjects() {
      return this.projects.filter(p => p.status === 'running').length
    },
    totalInstances() {
      return this.instances.length
    },
    portConflicts() {
      return this.portConflictsList.length
    },
    totalPortsInUse() {
      return Object.values(this.portUsage).reduce((total, instancePorts) => {
        return total + Object.keys(instancePorts).length
      }, 0)
    },
    healthyProjects() {
      return this.projects.filter(p => p.status === 'running').length
    },
    unhealthyProjects() {
      return this.unhealthyProjectsList.length
    }
  },
  async mounted() {
    await this.initializeDashboard()
    this.setupWebSocket()
  },
  beforeUnmount() {
    if (this.ws) {
      this.ws.close()
    }
  },
  methods: {
    async initializeDashboard() {
      this.isRefreshing = true
      try {
        await Promise.all([
          this.loadProjects(),
          this.loadInstances(),
          this.loadPortUsage(),
          this.loadHealthData()
        ])
      } catch (error) {
        console.error('Error initializing dashboard:', error)
        this.$toast.error('Failed to load dashboard data')
      } finally {
        this.isRefreshing = false
      }
    },
    
    async loadProjects() {
      try {
        const response = await wsl2Api.getProjects()
        this.projects = response.projects || []
      } catch (error) {
        console.error('Error loading projects:', error)
        throw error
      }
    },
    
    async loadInstances() {
      try {
        const response = await wsl2Api.getInstances()
        this.instances = response.instances || []
      } catch (error) {
        console.error('Error loading instances:', error)
        throw error
      }
    },
    
    async loadPortUsage() {
      try {
        const response = await wsl2Api.getPortUsage()
        this.portUsage = response.all_port_usage || {}
        this.portConflictsList = response.conflicts || []
      } catch (error) {
        console.error('Error loading port usage:', error)
        throw error
      }
    },
    
    async loadHealthData() {
      try {
        const response = await wsl2Api.getHealthStatus()
        this.healthData = response.all_health || {}
        this.unhealthyProjectsList = Object.values(this.healthData.health_results || {})
          .filter(result => !result.healthy)
          .map(result => ({ project_id: result.project_id, project: { name: result.project_name } }))
      } catch (error) {
        console.error('Error loading health data:', error)
        throw error
      }
    },
    
    setupWebSocket() {
      wsl2WebSocket.connect()
      
      wsl2WebSocket.on('connected', () => {
        this.wsConnected = true
        // Subscribe to all updates
        wsl2WebSocket.subscribe('project_status')
        wsl2WebSocket.subscribe('port_monitoring')
        wsl2WebSocket.subscribe('health_monitoring')
        wsl2WebSocket.subscribe('instance_status')
      })
      
      wsl2WebSocket.on('disconnected', () => {
        this.wsConnected = false
      })
      
      wsl2WebSocket.on('project_status_update', (data) => {
        this.updateProjectStatus(data.project)
      })
      
      wsl2WebSocket.on('project_status_changed', (data) => {
        this.updateProjectStatus({
          project_id: data.project_id,
          status: data.new_status
        })
        this.$toast.info(`${data.project_name} is now ${data.new_status}`)
      })
      
      wsl2WebSocket.on('port_monitoring_update', (data) => {
        if (data.scope === 'all') {
          this.portUsage = data.port_usage
          this.portConflictsList = data.conflicts
        }
      })
      
      wsl2WebSocket.on('port_conflict_detected', (data) => {
        this.portConflictsList.push(data.conflict)
        this.$toast.warning(`Port conflict detected on port ${data.conflict.port}`)
      })
      
      wsl2WebSocket.on('health_monitoring_update', (data) => {
        this.unhealthyProjectsList = data.unhealthy_projects
      })
      
      wsl2WebSocket.on('health_alert', (data) => {
        this.$toast.error(`Health alert: ${data.project_name} is unhealthy`)
      })
      
      wsl2WebSocket.on('instance_status_update', (data) => {
        this.instances = data.instances
      })
    },
    
    updateProjectStatus(projectUpdate) {
      const index = this.projects.findIndex(p => p.id === projectUpdate.project_id)
      if (index !== -1) {
        this.projects[index] = { ...this.projects[index], ...projectUpdate }
      }
    },
    
    filterProjects() {
      // Computed property handles filtering
    },
    
    async refreshData() {
      await this.initializeDashboard()
      this.$toast.success('Dashboard refreshed')
    },
    
    // Project Actions
    async startProject(project) {
      try {
        await wsl2Api.startProject(project.id)
        this.$toast.success(`Starting ${project.name}...`)
      } catch (error) {
        console.error('Error starting project:', error)
        this.$toast.error(`Failed to start ${project.name}`)
      }
    },
    
    async stopProject(project) {
      try {
        await wsl2Api.stopProject(project.id)
        this.$toast.success(`Stopping ${project.name}...`)
      } catch (error) {
        console.error('Error stopping project:', error)
        this.$toast.error(`Failed to stop ${project.name}`)
      }
    },
    
    async restartProject(project) {
      try {
        await wsl2Api.restartProject(project.id)
        this.$toast.success(`Restarting ${project.name}...`)
      } catch (error) {
        console.error('Error restarting project:', error)
        this.$toast.error(`Failed to restart ${project.name}`)
      }
    },
    
    async deleteProject(project) {
      if (confirm(`Are you sure you want to delete ${project.name}?`)) {
        try {
          await wsl2Api.deleteProject(project.id)
          this.projects = this.projects.filter(p => p.id !== project.id)
          this.$toast.success(`Deleted ${project.name}`)
        } catch (error) {
          console.error('Error deleting project:', error)
          this.$toast.error(`Failed to delete ${project.name}`)
        }
      }
    },
    
    editProject(project) {
      this.selectedProject = { ...project }
      this.modalMode = 'edit'
      this.showProjectModal = true
    },
    
    // Bulk Actions
    async startAllProjects() {
      if (confirm('Start all stopped projects?')) {
        try {
          await wsl2Api.bulkStartProjects()
          this.$toast.success('Starting all projects...')
        } catch (error) {
          console.error('Error starting all projects:', error)
          this.$toast.error('Failed to start all projects')
        }
      }
    },
    
    async stopAllProjects() {
      if (confirm('Stop all running projects?')) {
        try {
          await wsl2Api.bulkStopProjects()
          this.$toast.success('Stopping all projects...')
        } catch (error) {
          console.error('Error stopping all projects:', error)
          this.$toast.error('Failed to stop all projects')
        }
      }
    },
    
    // Instance Actions
    async startInstance(instanceName) {
      try {
        await wsl2Api.startInstance(instanceName)
        this.$toast.success(`Starting ${instanceName}...`)
      } catch (error) {
        console.error('Error starting instance:', error)
        this.$toast.error(`Failed to start ${instanceName}`)
      }
    },
    
    async stopInstance(instanceName) {
      if (confirm(`Stop WSL2 instance ${instanceName}?`)) {
        try {
          await wsl2Api.stopInstance(instanceName)
          this.$toast.success(`Stopping ${instanceName}...`)
        } catch (error) {
          console.error('Error stopping instance:', error)
          this.$toast.error(`Failed to stop ${instanceName}`)
        }
      }
    },
    
    // Discovery
    discoverProjects() {
      this.showDiscoveryModal = true
    },
    
    async handleDiscovery(discoveryOptions) {
      try {
        const response = await wsl2Api.discoverProjects(discoveryOptions)
        const discoveredProjects = response.discovered_projects || []
        
        // Add discovered projects to the list
        for (const project of discoveredProjects) {
          const existing = this.projects.find(p => p.name === project.name && p.wsl_instance === project.wsl_instance)
          if (!existing) {
            this.projects.push(project)
          }
        }
        
        this.$toast.success(`Discovered ${discoveredProjects.length} projects`)
        this.closeDiscoveryModal()
      } catch (error) {
        console.error('Error discovering projects:', error)
        this.$toast.error('Failed to discover projects')
      }
    },
    
    // Modal Management
    closeProjectModal() {
      this.showProjectModal = false
      this.selectedProject = null
    },
    
    closeDiscoveryModal() {
      this.showDiscoveryModal = false
    },
    
    async saveProject(projectData) {
      try {
        if (this.modalMode === 'edit') {
          await wsl2Api.updateProject(projectData)
          const index = this.projects.findIndex(p => p.id === projectData.id)
          if (index !== -1) {
            this.projects[index] = projectData
          }
          this.$toast.success(`Updated ${projectData.name}`)
        } else {
          const response = await wsl2Api.createProject(projectData)
          this.projects.push(response.project)
          this.$toast.success(`Created ${projectData.name}`)
        }
        this.closeProjectModal()
      } catch (error) {
        console.error('Error saving project:', error)
        this.$toast.error('Failed to save project')
      }
    }
  }
}
</script>

<style scoped>
.wsl2-dashboard {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e9ecef;
}

.dashboard-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #2c3e50;
  margin: 0;
}

.dashboard-title i {
  margin-right: 15px;
  color: #3498db;
}

.dashboard-stats {
  display: flex;
  gap: 20px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  min-width: 120px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
}

.action-group {
  display: flex;
  gap: 10px;
}

.filter-group {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-success {
  background: #27ae60;
  color: white;
}

.btn-warning {
  background: #f39c12;
  color: white;
}

.btn-info {
  background: #17a2b8;
  color: white;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 0.8rem;
}

.form-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
}

.dashboard-content {
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 30px;
}

.projects-section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6c757d;
}

.empty-state i {
  color: #dee2e6;
  margin-bottom: 20px;
}

.empty-state h3 {
  margin-bottom: 10px;
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.panel-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.instance-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.instance-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.instance-item.running {
  background: #d4edda;
  border-color: #c3e6cb;
}

.instance-item.stopped {
  background: #f8d7da;
  border-color: #f5c6cb;
}

.instance-name {
  font-weight: 600;
}

.instance-status {
  font-size: 0.8rem;
  color: #6c757d;
}

.port-stats, .health-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.port-stat, .health-stat {
  text-align: center;
}

.port-count, .health-count {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #27ae60;
}

.port-count.conflict, .health-count {
  color: #e74c3c;
}

.health-stat.healthy .health-count {
  color: #27ae60;
}

.port-label, .health-label {
  font-size: 0.8rem;
  color: #6c757d;
}

.conflict-list, .unhealthy-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.conflict-item, .unhealthy-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #fff3cd;
  border-radius: 6px;
  font-size: 0.9rem;
}

.conflict-item i, .unhealthy-item i {
  color: #856404;
}

.connection-status {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 10px 15px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 1000;
}

.connection-status.connected {
  background: #d4edda;
  color: #155724;
}

.connection-status.disconnected {
  background: #f8d7da;
  color: #721c24;
}

@media (max-width: 1200px) {
  .dashboard-content {
    grid-template-columns: 1fr;
  }
  
  .dashboard-header {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .action-bar {
    flex-direction: column;
    gap: 15px;
  }
}

@media (max-width: 768px) {
  .dashboard-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .projects-grid {
    grid-template-columns: 1fr;
  }
  
  .action-group, .filter-group {
    flex-wrap: wrap;
  }
}
</style>
