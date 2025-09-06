<template>
  <div class="project-list">
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <span>Loading projects...</span>
    </div>
    
    <div v-else-if="projects.length === 0" class="empty-state">
      <div class="empty-icon">📁</div>
      <h3>No Projects Found</h3>
      <p>Get started by adding your first project</p>
    </div>
    
    <div v-else class="projects-grid">
      <ProjectCard
        v-for="project in projects"
        :key="project.id"
        :project="project"
        @start="$emit('project-start', project)"
        @stop="$emit('project-stop', project)"
        @settings="$emit('project-settings', project)"
        @delete="$emit('project-delete', project)"
        @status-change="$emit('status-change', project, $event)"
      />
    </div>
  </div>
</template>

<script>
import ProjectCard from './ProjectCard.vue'

export default {
  name: 'ProjectList',
  components: {
    ProjectCard
  },
  props: {
    projects: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: [
    'project-start',
    'project-stop', 
    'project-settings',
    'project-delete',
    'status-change'
  ]
}
</script>

<style scoped>
.project-list {
  width: 100%;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #888;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #333;
  border-top: 3px solid #007acc;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #888;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 24px;
  margin: 0 0 12px 0;
  color: #ccc;
}

.empty-state p {
  font-size: 16px;
  margin: 0;
  opacity: 0.8;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  padding: 10px 0;
}

@media (max-width: 768px) {
  .projects-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}
</style>
