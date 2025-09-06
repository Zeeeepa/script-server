<template>
  <div class="project-card" :class="{ 'project-running': isRunning, 'project-error': hasError }">
    <div class="project-header">
      <div class="project-info">
        <div class="project-icon">
          <i :class="projectIcon"></i>
        </div>
        <div class="project-details">
          <h3 class="project-name">{{ project.name }}</h3>
          <p class="project-path">{{ project.path }}</p>
        </div>
      </div>
      
      <div class="project-status">
        <StatusBadge :status="project.status" />
        <ToggleSwitch 
          :value="isRunning"
          :disabled="isTransitioning"
          @change="handleToggle"
        />
      </div>
    </div>

    <div class="project-body">
      <div class="project-type">
        <span class="type-label">Type:</span>
        <span class="type-value">{{ project.project_type }}</span>
      </div>
      
      <div v-if="project.ports && project.ports.length > 0" class="project-ports">
        <span class="ports-label">Ports:</span>
        <div class="ports-list">
          <span 
            v-for="port in project.ports" 
            :key="port"
            class="port-badge"
            :class="{ 'port-active': isRunning }"
          >
            localhost:{{ port }}
          </span>
        </div>
      </div>

      <div v-if="project.health" class="project-health">
        <span class="health-label">Health:</span>
        <div class="health-indicator" :class="healthClass">
          <i :class="healthIcon"></i>
          <span>{{ healthText }}</span>
        </div>
      </div>
    </div>

    <div class="project-actions">
      <button 
        class="btn btn-secondary btn-sm"
        @click="$emit('settings', project)"
        title="Project Settings"
      >
        <i class="icon-settings"></i>
        Settings
      </button>
      
      <button 
        v-if="!isRunning"
        class="btn btn-success btn-sm"
        :disabled="isTransitioning"
        @click="handleStart"
        title="Start Project"
      >
        <i class="icon-play"></i>
        {{ isTransitioning ? 'Starting...' : 'Run' }}
      </button>
      
      <button 
        v-else
        class="btn btn-warning btn-sm"
        :disabled="isTransitioning"
        @click="handleStop"
        title="Stop Project"
      >
        <i class="icon-stop"></i>
        {{ isTransitioning ? 'Stopping...' : 'Stop' }}
      </button>
      
      <button 
        class="btn btn-danger btn-sm"
        @click="handleDelete"
        title="Delete Project"
      >
        <i class="icon-delete"></i>
      </button>
    </div>
  </div>
</template>

<script>
import StatusBadge from './StatusBadge.vue'
import ToggleSwitch from './ToggleSwitch.vue'

export default {
  name: 'ProjectCard',
  components: {
    StatusBadge,
    ToggleSwitch
  },
  props: {
    project: {
      type: Object,
      required: true
    }
  },
  emits: ['start', 'stop', 'settings', 'delete', 'status-change'],
  computed: {
    isRunning() {
      return this.project.status === 'running'
    },
    
    isTransitioning() {
      return ['starting', 'stopping'].includes(this.project.status)
    },
    
    hasError() {
      return this.project.status === 'error'
    },
    
    projectIcon() {
      const iconMap = {
        'nodejs': 'icon-nodejs',
        'python': 'icon-python',
        'docker': 'icon-docker',
        'go': 'icon-go',
        'java': 'icon-java',
        'dotnet': 'icon-dotnet',
        'generic': 'icon-code'
      }
      return iconMap[this.project.project_type] || 'icon-code'
    },
    
    healthClass() {
      if (!this.project.health) return 'health-unknown'
      return this.project.health.healthy ? 'health-good' : 'health-bad'
    },
    
    healthIcon() {
      if (!this.project.health) return 'icon-question'
      return this.project.health.healthy ? 'icon-check' : 'icon-warning'
    },
    
    healthText() {
      if (!this.project.health) return 'Unknown'
      return this.project.health.healthy ? 'Healthy' : 'Unhealthy'
    }
  },
  methods: {
    handleToggle(enabled) {
      if (enabled && !this.isRunning) {
        this.handleStart()
      } else if (!enabled && this.isRunning) {
        this.handleStop()
      }
    },
    
    handleStart() {
      this.$emit('start', this.project)
    },
    
    handleStop() {
      this.$emit('stop', this.project)
    },
    
    handleDelete() {
      this.$emit('delete', this.project)
    }
  }
}
</script>

<style scoped>
.project-card {
  background: #2d2d2d;
  border: 1px solid #404040;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.2s ease;
  position: relative;
}

.project-card:hover {
  border-color: #555;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.project-card.project-running {
  border-color: #28a745;
  box-shadow: 0 0 0 1px rgba(40, 167, 69, 0.2);
}

.project-card.project-error {
  border-color: #dc3545;
  box-shadow: 0 0 0 1px rgba(220, 53, 69, 0.2);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.project-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
}

.project-icon {
  width: 40px;
  height: 40px;
  background: #404040;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #007acc;
}

.project-details {
  flex: 1;
}

.project-name {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: #ffffff;
}

.project-path {
  font-size: 13px;
  color: #888;
  margin: 0;
  font-family: 'Courier New', monospace;
}

.project-status {
  display: flex;
  align-items: center;
  gap: 12px;
}

.project-body {
  margin-bottom: 20px;
  space-y: 12px;
}

.project-type,
.project-ports,
.project-health {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.type-label,
.ports-label,
.health-label {
  font-size: 13px;
  color: #888;
  min-width: 60px;
}

.type-value {
  font-size: 13px;
  color: #ccc;
  text-transform: capitalize;
}

.ports-list {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.port-badge {
  background: #404040;
  color: #ccc;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Courier New', monospace;
  transition: all 0.2s;
}

.port-badge.port-active {
  background: #28a745;
  color: white;
}

.health-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.health-good {
  color: #28a745;
}

.health-bad {
  color: #dc3545;
}

.health-unknown {
  color: #888;
}

.project-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.btn {
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  padding: 6px 12px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 11px;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #5a6268;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #218838;
}

.btn-warning {
  background: #ffc107;
  color: #212529;
}

.btn-warning:hover:not(:disabled) {
  background: #e0a800;
}

.btn-danger {
  background: #dc3545;
  color: white;
  padding: 4px 6px;
}

.btn-danger:hover:not(:disabled) {
  background: #c82333;
}

/* Icons */
.icon-nodejs::before { content: '⬢'; color: #68a063; }
.icon-python::before { content: '🐍'; }
.icon-docker::before { content: '🐳'; }
.icon-go::before { content: '🐹'; }
.icon-java::before { content: '☕'; }
.icon-dotnet::before { content: '🔷'; }
.icon-code::before { content: '💻'; }
.icon-settings::before { content: '⚙️'; }
.icon-play::before { content: '▶️'; }
.icon-stop::before { content: '⏹️'; }
.icon-delete::before { content: '🗑️'; }
.icon-check::before { content: '✅'; }
.icon-warning::before { content: '⚠️'; }
.icon-question::before { content: '❓'; }
</style>
