<template>
  <div class="expandable-section">
    <button 
      class="section-header"
      @click="toggle"
      :aria-expanded="expanded"
      :aria-controls="contentId"
    >
      <span class="section-title">{{ title }}</span>
      <i class="expand-icon" :class="{ 'expanded': expanded }"></i>
    </button>
    
    <div 
      :id="contentId"
      class="section-content"
      :class="{ 'content-expanded': expanded }"
      :style="{ maxHeight: expanded ? contentHeight + 'px' : '0px' }"
    >
      <div ref="contentWrapper" class="content-wrapper">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ExpandableSection',
  props: {
    title: {
      type: String,
      required: true
    },
    expanded: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['toggle'],
  data() {
    return {
      contentHeight: 0
    }
  },
  computed: {
    contentId() {
      return `expandable-content-${this.$.uid}`
    }
  },
  mounted() {
    this.updateContentHeight()
    // Watch for content changes
    if (this.$refs.contentWrapper) {
      const resizeObserver = new ResizeObserver(() => {
        this.updateContentHeight()
      })
      resizeObserver.observe(this.$refs.contentWrapper)
      this.$once('beforeUnmount', () => {
        resizeObserver.disconnect()
      })
    }
  },
  updated() {
    this.$nextTick(() => {
      this.updateContentHeight()
    })
  },
  methods: {
    toggle() {
      if (!this.disabled) {
        this.$emit('toggle')
      }
    },
    
    updateContentHeight() {
      if (this.$refs.contentWrapper) {
        this.contentHeight = this.$refs.contentWrapper.scrollHeight
      }
    }
  }
}
</script>

<style scoped>
.expandable-section {
  border: 1px solid #404040;
  border-radius: 6px;
  background: #2a2a2a;
  overflow: hidden;
  transition: all 0.2s ease;
}

.expandable-section:hover {
  border-color: #555;
}

.section-header {
  width: 100%;
  background: none;
  border: none;
  color: #ffffff;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  text-align: left;
}

.section-header:hover {
  background: rgba(255, 255, 255, 0.05);
}

.section-header:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.section-title {
  flex: 1;
}

.expand-icon {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease;
  color: #888;
}

.expand-icon::before {
  content: '▶';
  font-size: 12px;
}

.expand-icon.expanded {
  transform: rotate(90deg);
  color: #007acc;
}

.section-content {
  overflow: hidden;
  transition: max-height 0.3s ease;
  background: #262626;
}

.content-wrapper {
  padding: 0 20px 16px 20px;
}

.content-expanded {
  border-top: 1px solid #404040;
}

/* Animation variants */
.expandable-section.animate-slide .section-content {
  transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.expandable-section.animate-fade .section-content {
  transition: max-height 0.3s ease, opacity 0.2s ease;
}

.expandable-section.animate-fade .section-content:not(.content-expanded) {
  opacity: 0;
}

.expandable-section.animate-fade .content-expanded {
  opacity: 1;
}

/* Size variants */
.expandable-section.size-small .section-header {
  padding: 12px 16px;
  font-size: 13px;
}

.expandable-section.size-small .content-wrapper {
  padding: 0 16px 12px 16px;
}

.expandable-section.size-large .section-header {
  padding: 20px 24px;
  font-size: 16px;
}

.expandable-section.size-large .content-wrapper {
  padding: 0 24px 20px 24px;
}

/* Theme variants */
.expandable-section.theme-primary {
  border-color: #007acc;
}

.expandable-section.theme-primary .section-header {
  background: rgba(0, 122, 204, 0.1);
}

.expandable-section.theme-primary .expand-icon.expanded {
  color: #007acc;
}

.expandable-section.theme-success {
  border-color: #28a745;
}

.expandable-section.theme-success .section-header {
  background: rgba(40, 167, 69, 0.1);
}

.expandable-section.theme-success .expand-icon.expanded {
  color: #28a745;
}

.expandable-section.theme-warning {
  border-color: #ffc107;
}

.expandable-section.theme-warning .section-header {
  background: rgba(255, 193, 7, 0.1);
}

.expandable-section.theme-warning .expand-icon.expanded {
  color: #ffc107;
}

/* Focus styles for accessibility */
.section-header:focus {
  outline: 2px solid #007acc;
  outline-offset: -2px;
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .section-content,
  .expand-icon {
    transition: none;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .expandable-section {
    border-width: 2px;
  }
  
  .section-header {
    border-bottom: 1px solid currentColor;
  }
}

/* Mobile responsive */
@media (max-width: 768px) {
  .section-header {
    padding: 14px 16px;
  }
  
  .content-wrapper {
    padding: 0 16px 14px 16px;
  }
}
</style>
