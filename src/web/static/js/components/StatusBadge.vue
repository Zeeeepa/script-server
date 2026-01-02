<template>
  <div class="status-badge" :class="statusClass">
    <div class="status-indicator" :class="indicatorClass">
      <i :class="statusIcon"></i>
    </div>
    <span class="status-text">{{ statusText }}</span>
  </div>
</template>

<script>
export default {
  name: 'StatusBadge',
  props: {
    status: {
      type: String,
      required: true
    },
    showText: {
      type: Boolean,
      default: true
    },
    size: {
      type: String,
      default: 'medium',
      validator: (value) => ['small', 'medium', 'large'].includes(value)
    }
  },
  computed: {
    statusClass() {
      return [
        `status-${this.status}`,
        `status-${this.size}`
      ]
    },
    
    indicatorClass() {
      const classes = [`indicator-${this.status}`]
      
      if (['starting', 'stopping', 'restarting'].includes(this.status)) {
        classes.push('indicator-pulsing')
      }
      
      return classes
    },
    
    statusIcon() {
      const iconMap = {
        'running': 'icon-running',
        'stopped': 'icon-stopped',
        'starting': 'icon-starting',
        'stopping': 'icon-stopping',
        'restarting': 'icon-restarting',
        'error': 'icon-error',
        'unknown': 'icon-unknown'
      }
      return iconMap[this.status] || 'icon-unknown'
    },
    
    statusText() {
      const textMap = {
        'running': 'Running',
        'stopped': 'Stopped',
        'starting': 'Starting',
        'stopping': 'Stopping',
        'restarting': 'Restarting',
        'error': 'Error',
        'unknown': 'Unknown'
      }
      return textMap[this.status] || 'Unknown'
    }
  }
}
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.status-badge.status-small {
  padding: 2px 6px;
  font-size: 11px;
  gap: 4px;
}

.status-badge.status-large {
  padding: 6px 12px;
  font-size: 13px;
  gap: 8px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.status-small .status-indicator {
  width: 6px;
  height: 6px;
}

.status-large .status-indicator {
  width: 10px;
  height: 10px;
}

.status-text {
  line-height: 1;
}

/* Status-specific styles */
.status-running {
  background: rgba(40, 167, 69, 0.1);
  color: #28a745;
  border-color: rgba(40, 167, 69, 0.2);
}

.indicator-running {
  background: #28a745;
  box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.2);
}

.status-stopped {
  background: rgba(108, 117, 125, 0.1);
  color: #6c757d;
  border-color: rgba(108, 117, 125, 0.2);
}

.indicator-stopped {
  background: #6c757d;
}

.status-starting,
.status-stopping,
.status-restarting {
  background: rgba(255, 193, 7, 0.1);
  color: #ffc107;
  border-color: rgba(255, 193, 7, 0.2);
}

.indicator-starting,
.indicator-stopping,
.indicator-restarting {
  background: #ffc107;
}

.status-error {
  background: rgba(220, 53, 69, 0.1);
  color: #dc3545;
  border-color: rgba(220, 53, 69, 0.2);
}

.indicator-error {
  background: #dc3545;
  box-shadow: 0 0 0 2px rgba(220, 53, 69, 0.2);
}

.status-unknown {
  background: rgba(136, 136, 136, 0.1);
  color: #888;
  border-color: rgba(136, 136, 136, 0.2);
}

.indicator-unknown {
  background: #888;
}

/* Pulsing animation for transitional states */
.indicator-pulsing {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

/* Icons */
.status-indicator i {
  font-size: 6px;
  color: white;
}

.status-small .status-indicator i {
  font-size: 5px;
}

.status-large .status-indicator i {
  font-size: 7px;
}

.icon-running::before { content: '●'; }
.icon-stopped::before { content: '■'; }
.icon-starting::before { content: '▶'; }
.icon-stopping::before { content: '⏸'; }
.icon-restarting::before { content: '↻'; }
.icon-error::before { content: '✕'; }
.icon-unknown::before { content: '?'; }

/* Hover effects */
.status-badge:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .indicator-pulsing {
    animation: none;
  }
  
  .status-badge:hover {
    transform: none;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .status-badge {
    border-width: 2px;
  }
  
  .status-indicator {
    border: 1px solid currentColor;
  }
}
</style>
