<template>
  <div class="project-card" :class="[`status-${project.status}`, { 'has-health-issues': hasHealthIssues }]">
    <!-- Project Header -->
    <div class="project-header">
      <div class="project-info">
        <h3 class="project-name">{{ project.name }}</h3>
        <div class="project-meta">
          <span class="project-type">
            <i :class="getTypeIcon(project.project_type)"></i>
            {{ getTypeLabel(project.project_type) }}
          </span>
          <span class="project-instance">
            <i class="fas fa-server"></i>
            {{ project.wsl_instance }}
          </span>
        </div>
      </div>
      
      <div class="project-status">
        <div class="status-indicator" :class="`status-${project.status}`">
          <i :class="getStatusIcon(project.status)"></i>
        </div>
        <span class="status-text">{{ getStatusLabel(project.status) }}</span>
      </div>
    </div>

    <!-- Project Details -->
    <div class="project-details">
      <div class="detail-row">
        <span class="detail-label">Path:</span>
        <span class="detail-value">{{ project.path }}</span>
      </div>
      
      <div class="detail-row" v-if="project.ports && project.ports.length > 0">
        <span class="detail-label">Ports:</span>
        <div class="ports-list">
          <span 
            v-for="port in project.ports" 
            :key="port" 
            class="port-badge"
            :class="{ 'port-conflict': isPortConflicted(port) }"
          >
            {{ port }}
          </span>
        </div>
      </div>
      
      <div class="detail-row" v-if="project.health_check">
        <span class="detail-label">Health:</span>
        <div class="health-status" :class="{ 'healthy': isHealthy, 'unhealthy': !isHealthy }">
          <i :class="isHealthy ? 'fas fa-heart' : 'fas fa-heart-broken'"></i>
          {{ isHealthy ? 'Healthy' : 'Unhealthy' }}
        </div>
      </div>
      
      <div class="detail-row" v-if="project.dependencies && project.dependencies.length > 0">
        <span class="detail-label">Dependencies:</span>
        <span class="detail-value">{{ project.dependencies.join(', ') }}</span>
      </div>
    </div>

    <!-- Project Actions -->
    <div class="project-actions">
      <div class="primary-actions">
        <button 
          v-if="project.status === 'stopped' || project.status === 'error'"
          class="btn btn-success btn-sm"
          @click="$emit('start', project)"
          :disabled="isActionDisabled"
        >
          <i class="fas fa-play"></i>
          Start
        </button>
        
        <button 
          v-if="project.status === 'running'"
          class="btn btn-warning btn-sm"
          @click="$emit('stop', project)"
          :disabled="isActionDisabled"
        >
          <i class="fas fa-stop"></i>
          Stop
        </button>
        
        <button 
          v-if="project.status === 'running'"
          class="btn btn-info btn-sm"
          @click="$emit('restart', project)"
          :disabled="isActionDisabled"
        >
          <i class="fas fa-redo"></i>
          Restart
        </button>
        
        <div v-if="project.status === 'starting' || project.status === 'stopping'" class="loading-indicator">
          <i class="fas fa-spinner fa-spin"></i>
          {{ project.status === 'starting' ? 'Starting...' : 'Stopping...' }}
        </div>
      </div>
      
      <div class="secondary-actions">
        <button class="btn btn-outline btn-sm" @click="$emit('edit', project)">
          <i class="fas fa-edit"></i>
        </button>
        
        <div class="dropdown">
          <button class="btn btn-outline btn-sm dropdown-toggle" @click="toggleDropdown">
            <i class="fas fa-ellipsis-v"></i>
          </button>
          <div class="dropdown-menu" v-show="showDropdown">
            <a class="dropdown-item" @click="viewLogs">
              <i class="fas fa-file-alt"></i>
              View Logs
            </a>
            <a class="dropdown-item" @click="openTerminal">
              <i class="fas fa-terminal"></i>
              Open Terminal
            </a>
            <a class="dropdown-item" @click="viewConfig">
              <i class="fas fa-cog"></i>
              Configuration
            </a>
            <div class="dropdown-divider"></div>
            <a class="dropdown-item text-danger" @click="confirmDelete">
              <i class="fas fa-trash"></i>
              Delete Project
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- Health Issues Alert -->
    <div v-if="hasHealthIssues" class="health-alert">
      <i class="fas fa-exclamation-triangle"></i>
      Health check failing - {{ healthIssueMessage }}
    </div>

    <!-- Port Conflicts Alert -->
    <div v-if="hasPortConflicts" class="port-conflict-alert">
      <i class="fas fa-exclamation-circle"></i>
      Port conflicts detected: {{ conflictedPorts.join(', ') }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'WSL2ProjectCard',
  props: {
    project: {
      type: Object,
      required: true
    },
    portConflicts: {
      type: Array,
      default: () => []
    },
    healthStatus: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      showDropdown: false,
      isActionDisabled: false
    }
  },
  computed: {
    isHealthy() {
      return this.healthStatus[this.project.id]?.healthy !== false
    },
    
    hasHealthIssues() {
      return this.healthStatus[this.project.id]?.healthy === false
    },
    
    healthIssueMessage() {
      return this.healthStatus[this.project.id]?.message || 'Unknown health issue'
    },
    
    conflictedPorts() {
      if (!this.project.ports) return []
      return this.project.ports.filter(port => this.isPortConflicted(port))
    },
    
    hasPortConflicts() {
      return this.conflictedPorts.length > 0
    }
  },
  methods: {
    getTypeIcon(type) {
      const icons = {
        nodejs: 'fab fa-node-js',
        python: 'fab fa-python',
        docker: 'fab fa-docker',
        go: 'fab fa-golang',
        java: 'fab fa-java',
        dotnet: 'fab fa-microsoft',
        generic: 'fas fa-code'
      }
      return icons[type] || icons.generic
    },
    
    getTypeLabel(type) {
      const labels = {
        nodejs: 'Node.js',
        python: 'Python',
        docker: 'Docker',
        go: 'Go',
        java: 'Java',
        dotnet: '.NET',
        generic: 'Generic'
      }
      return labels[type] || 'Unknown'
    },
    
    getStatusIcon(status) {
      const icons = {
        running: 'fas fa-play-circle',
        stopped: 'fas fa-stop-circle',
        starting: 'fas fa-spinner fa-spin',
        stopping: 'fas fa-spinner fa-spin',
        error: 'fas fa-exclamation-circle'
      }
      return icons[status] || 'fas fa-question-circle'
    },
    
    getStatusLabel(status) {
      const labels = {
        running: 'Running',
        stopped: 'Stopped',
        starting: 'Starting',
        stopping: 'Stopping',
        error: 'Error'
      }
      return labels[status] || 'Unknown'
    },
    
    isPortConflicted(port) {
      return this.portConflicts.some(conflict => conflict.port === port)
    },
    
    toggleDropdown() {
      this.showDropdown = !this.showDropdown
    },
    
    viewLogs() {
      this.showDropdown = false
      // Emit event or navigate to logs view
      this.$emit('view-logs', this.project)
    },
    
    openTerminal() {
      this.showDropdown = false
      // Open terminal in WSL2 instance
      this.$emit('open-terminal', this.project)
    },
    
    viewConfig() {
      this.showDropdown = false
      this.$emit('view-config', this.project)
    },
    
    confirmDelete() {
      this.showDropdown = false
      if (confirm(`Are you sure you want to delete ${this.project.name}?`)) {
        this.$emit('delete', this.project)
      }
    }
  },
  mounted() {
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
      if (!this.$el.contains(e.target)) {
        this.showDropdown = false
      }
    })
  }
}
</script>

<style scoped>
.project-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
  border-left: 4px solid #e9ecef;
  position: relative;
}

.project-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

.project-card.status-running {
  border-left-color: #27ae60;
}

.project-card.status-stopped {
  border-left-color: #95a5a6;
}

.project-card.status-starting,
.project-card.status-stopping {
  border-left-color: #f39c12;
}

.project-card.status-error {
  border-left-color: #e74c3c;
}

.project-card.has-health-issues {
  border-left-color: #e74c3c;
  background: linear-gradient(135deg, #fff 0%, #fff5f5 100%);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.project-name {
  font-size: 1.2rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 8px 0;
}

.project-meta {
  display: flex;
  gap: 15px;
  font-size: 0.85rem;
  color: #6c757d;
}

.project-meta span {
  display: flex;
  align-items: center;
  gap: 5px;
}

.project-status {
  text-align: right;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  margin-bottom: 5px;
}

.status-indicator.status-running {
  background: #d4edda;
  color: #27ae60;
}

.status-indicator.status-stopped {
  background: #f8f9fa;
  color: #6c757d;
}

.status-indicator.status-starting,
.status-indicator.status-stopping {
  background: #fff3cd;
  color: #f39c12;
}

.status-indicator.status-error {
  background: #f8d7da;
  color: #e74c3c;
}

.status-text {
  font-size: 0.8rem;
  font-weight: 600;
  color: #6c757d;
}

.project-details {
  margin-bottom: 20px;
}

.detail-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.detail-label {
  font-weight: 600;
  color: #495057;
  min-width: 80px;
  margin-right: 10px;
}

.detail-value {
  color: #6c757d;
  flex: 1;
  word-break: break-all;
}

.ports-list {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.port-badge {
  background: #e9ecef;
  color: #495057;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.port-badge.port-conflict {
  background: #f8d7da;
  color: #721c24;
}

.health-status {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.85rem;
  font-weight: 500;
}

.health-status.healthy {
  color: #27ae60;
}

.health-status.unhealthy {
  color: #e74c3c;
}

.project-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.primary-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.secondary-actions {
  display: flex;
  gap: 5px;
  position: relative;
}

.btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.btn:hover {
  transform: translateY(-1px);
}

.btn-sm {
  padding: 4px 8px;
  font-size: 0.75rem;
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

.btn-outline {
  background: transparent;
  border: 1px solid #dee2e6;
  color: #6c757d;
}

.btn-outline:hover {
  background: #f8f9fa;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #f39c12;
  font-size: 0.85rem;
  font-weight: 500;
}

.dropdown {
  position: relative;
}

.dropdown-toggle {
  background: transparent;
  border: 1px solid #dee2e6;
  color: #6c757d;
  padding: 4px 8px;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 1000;
  min-width: 150px;
  margin-top: 2px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  color: #495057;
  text-decoration: none;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.dropdown-item:hover {
  background: #f8f9fa;
}

.dropdown-item.text-danger {
  color: #e74c3c;
}

.dropdown-divider {
  height: 1px;
  background: #dee2e6;
  margin: 5px 0;
}

.health-alert,
.port-conflict-alert {
  margin-top: 15px;
  padding: 10px;
  border-radius: 6px;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.health-alert {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.port-conflict-alert {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

@media (max-width: 768px) {
  .project-header {
    flex-direction: column;
    gap: 10px;
  }
  
  .project-meta {
    flex-direction: column;
    gap: 5px;
  }
  
  .project-actions {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
  }
  
  .primary-actions {
    justify-content: center;
  }
}
</style>
