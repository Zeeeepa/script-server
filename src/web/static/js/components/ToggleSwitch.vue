<template>
  <div class="toggle-switch" :class="{ 'toggle-disabled': disabled }">
    <input
      :id="inputId"
      type="checkbox"
      class="toggle-input"
      :checked="value"
      :disabled="disabled"
      @change="handleChange"
    />
    <label :for="inputId" class="toggle-label">
      <span class="toggle-slider" :class="{ 'toggle-on': value, 'toggle-off': !value }">
        <span class="toggle-handle"></span>
      </span>
      <span v-if="showLabels" class="toggle-text">
        {{ value ? onLabel : offLabel }}
      </span>
    </label>
  </div>
</template>

<script>
export default {
  name: 'ToggleSwitch',
  props: {
    value: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    },
    onLabel: {
      type: String,
      default: 'ON'
    },
    offLabel: {
      type: String,
      default: 'OFF'
    },
    showLabels: {
      type: Boolean,
      default: true
    },
    size: {
      type: String,
      default: 'medium',
      validator: (value) => ['small', 'medium', 'large'].includes(value)
    }
  },
  emits: ['change'],
  computed: {
    inputId() {
      return `toggle-${this.$.uid}`
    }
  },
  methods: {
    handleChange(event) {
      if (!this.disabled) {
        this.$emit('change', event.target.checked)
      }
    }
  }
}
</script>

<style scoped>
.toggle-switch {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.toggle-input {
  display: none;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.toggle-disabled .toggle-label {
  cursor: not-allowed;
  opacity: 0.6;
}

.toggle-slider {
  position: relative;
  width: 44px;
  height: 24px;
  background: #404040;
  border-radius: 12px;
  transition: all 0.2s ease;
  border: 1px solid #555;
}

.toggle-slider.toggle-on {
  background: #28a745;
  border-color: #28a745;
}

.toggle-slider.toggle-off {
  background: #6c757d;
  border-color: #6c757d;
}

.toggle-handle {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  background: #ffffff;
  border-radius: 50%;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.toggle-on .toggle-handle {
  transform: translateX(20px);
}

.toggle-text {
  font-size: 12px;
  font-weight: 600;
  color: #ccc;
  min-width: 24px;
  text-align: center;
}

.toggle-on + .toggle-text {
  color: #28a745;
}

.toggle-off + .toggle-text {
  color: #6c757d;
}

/* Size variations */
.toggle-switch.size-small .toggle-slider {
  width: 36px;
  height: 20px;
  border-radius: 10px;
}

.toggle-switch.size-small .toggle-handle {
  width: 14px;
  height: 14px;
  top: 2px;
  left: 2px;
}

.toggle-switch.size-small .toggle-on .toggle-handle {
  transform: translateX(16px);
}

.toggle-switch.size-small .toggle-text {
  font-size: 11px;
}

.toggle-switch.size-large .toggle-slider {
  width: 52px;
  height: 28px;
  border-radius: 14px;
}

.toggle-switch.size-large .toggle-handle {
  width: 22px;
  height: 22px;
  top: 2px;
  left: 2px;
}

.toggle-switch.size-large .toggle-on .toggle-handle {
  transform: translateX(24px);
}

.toggle-switch.size-large .toggle-text {
  font-size: 13px;
}

/* Hover effects */
.toggle-label:hover:not(.toggle-disabled) .toggle-slider {
  box-shadow: 0 0 0 2px rgba(0, 122, 204, 0.2);
}

.toggle-label:hover:not(.toggle-disabled) .toggle-slider.toggle-on {
  box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.2);
}

/* Focus effects */
.toggle-input:focus + .toggle-label .toggle-slider {
  box-shadow: 0 0 0 2px rgba(0, 122, 204, 0.4);
}

.toggle-input:focus + .toggle-label .toggle-slider.toggle-on {
  box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.4);
}

/* Animation for handle */
.toggle-handle {
  transition: transform 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .toggle-slider,
  .toggle-handle {
    transition: none;
  }
}
</style>
