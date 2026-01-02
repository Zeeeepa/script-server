<template>
  <div class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-dialog" :class="{ 'modal-large': large }">
      <div class="modal-header">
        <h2 class="modal-title">{{ title }}</h2>
        <button class="modal-close" @click="$emit('close')" title="Close">
          <i class="icon-close"></i>
        </button>
      </div>
      
      <div class="modal-body">
        <slot></slot>
      </div>
      
      <div class="modal-footer" v-if="showFooter">
        <button 
          class="btn btn-secondary"
          @click="$emit('close')"
          :disabled="saving"
        >
          Cancel
        </button>
        <button 
          class="btn btn-primary"
          @click="$emit('save')"
          :disabled="saving || !canSave"
        >
          <span v-if="saving">Saving...</span>
          <span v-else>{{ saveText }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ModalDialog',
  props: {
    title: {
      type: String,
      required: true
    },
    large: {
      type: Boolean,
      default: false
    },
    showFooter: {
      type: Boolean,
      default: true
    },
    saving: {
      type: Boolean,
      default: false
    },
    canSave: {
      type: Boolean,
      default: true
    },
    saveText: {
      type: String,
      default: 'Save'
    },
    closeOnOverlay: {
      type: Boolean,
      default: true
    }
  },
  emits: ['close', 'save'],
  mounted() {
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', this.handleKeydown)
  },
  beforeUnmount() {
    document.body.style.overflow = ''
    document.removeEventListener('keydown', this.handleKeydown)
  },
  methods: {
    handleOverlayClick(event) {
      if (event.target === event.currentTarget && this.closeOnOverlay) {
        this.$emit('close')
      }
    },
    
    handleKeydown(event) {
      if (event.key === 'Escape') {
        this.$emit('close')
      }
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-dialog {
  background: #2d2d2d;
  border: 1px solid #404040;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  animation: modalSlideIn 0.2s ease-out;
}

.modal-dialog.modal-large {
  max-width: 800px;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #404040;
}

.modal-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #ffffff;
}

.modal-close {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
}

.modal-close:hover {
  background: #404040;
  color: #ffffff;
}

.modal-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #404040;
  background: #262626;
}

.btn {
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  padding: 10px 20px;
  transition: all 0.2s;
  font-weight: 500;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #5a6268;
}

.btn-primary {
  background: #007acc;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #005a9e;
}

.icon-close::before {
  content: '✕';
  font-size: 16px;
}

@media (max-width: 768px) {
  .modal-overlay {
    padding: 10px;
  }
  
  .modal-dialog {
    max-width: 100%;
    max-height: 95vh;
  }
  
  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 16px;
  }
  
  .modal-footer {
    flex-direction: column;
  }
  
  .modal-footer .btn {
    width: 100%;
  }
}
</style>
