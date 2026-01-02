<template>
  <div class="project-manager">
    <div class="project-manager-header">
      <h1 class="manager-title">Project Manager</h1>
      <button class="btn btn-primary add-project-btn" @click="showAddProject">
        <i class="icon-plus"></i>
        Add Project
      </button>
    </div>
    
    <div class="project-list-container">
      <ProjectList 
        :projects="projects"
        :loading="loading"
        @project-start="handleProjectStart"
        @project-stop="handleProjectStop"
        @project-settings="handleProjectSettings"
        @project-delete="handleProjectDelete"
        @status-change="handleStatusChange"
      />
    </div>

    <!-- Add Project Modal -->
    <ModalDialog 
      v-if="showAddProjectModal"
      title="Add New Project"
      @close="closeAddProject"
      @save="handleAddProject"
    >
      <AddProjectForm 
        ref="addProjectForm"
        @project-created="handleProjectCreated"
      />
    </ModalDialog>

    <!-- Project Settings Modal -->
    <ModalDialog 
      v-if="showSettingsModal"
      title="Project Settings"
      @close="closeSettings"
      @save="handleSaveSettings"
    >
      <ProjectSettings 
        ref="projectSettings"
        :project="selectedProject"
        @settings-changed="handleSettingsChanged"
      />
    </ModalDialog>
  </div>
</template>

<script>
import ProjectList from './ProjectList.vue'
import ModalDialog from './ModalDialog.vue'
import AddProjectForm from './AddProjectForm.vue'
import ProjectSettings from './ProjectSettings.vue'
import { ProjectService } from '../services/ProjectService.js'
import { StatusService } from '../services/StatusService.js'

export default {
  name: 'ProjectManager',
  components: {
    ProjectList,
    ModalDialog,
    AddProjectForm,
    ProjectSettings
  },
  data() {
    return {
      projects: [],
      loading: false,
      showAddProjectModal: false,
      showSettingsModal: false,
      selectedProject: null,
      statusService: null
    }
  },
  async mounted() {
    await this.loadProjects()
    this.initializeStatusService()
  },
  beforeUnmount() {
    if (this.statusService) {
      this.statusService.disconnect()
    }
  },
  methods: {
    async loadProjects() {
      this.loading = true
      try {
        this.projects = await ProjectService.getAllProjects()
      } catch (error) {
        console.error('Failed to load projects:', error)
        this.$emit('error', 'Failed to load projects')
      } finally {
        this.loading = false
      }
    },

    initializeStatusService() {
      this.statusService = new StatusService()
      this.statusService.connect()
      this.statusService.onStatusUpdate((update) => {
        this.handleStatusUpdate(update)
      })
    },

    handleStatusUpdate(update) {
      const project = this.projects.find(p => p.id === update.project_id)
      if (project) {
        project.status = update.status
        project.ports = update.ports || project.ports
        project.health = update.health || project.health
      }
    },

    showAddProject() {
      this.showAddProjectModal = true
    },

    closeAddProject() {
      this.showAddProjectModal = false
    },

    async handleAddProject() {
      if (this.$refs.addProjectForm) {
        const isValid = await this.$refs.addProjectForm.validate()
        if (isValid) {
          await this.$refs.addProjectForm.submit()
        }
      }
    },

    async handleProjectCreated(project) {
      this.projects.push(project)
      this.closeAddProject()
      this.$emit('success', `Project "${project.name}" created successfully`)
    },

    async handleProjectStart(project) {
      try {
        await ProjectService.startProject(project.id)
        project.status = 'starting'
        this.$emit('success', `Starting project "${project.name}"`)
      } catch (error) {
        console.error('Failed to start project:', error)
        this.$emit('error', `Failed to start project "${project.name}"`)
      }
    },

    async handleProjectStop(project) {
      try {
        await ProjectService.stopProject(project.id)
        project.status = 'stopping'
        this.$emit('success', `Stopping project "${project.name}"`)
      } catch (error) {
        console.error('Failed to stop project:', error)
        this.$emit('error', `Failed to stop project "${project.name}"`)
      }
    },

    handleProjectSettings(project) {
      this.selectedProject = project
      this.showSettingsModal = true
    },

    closeSettings() {
      this.showSettingsModal = false
      this.selectedProject = null
    },

    async handleSaveSettings() {
      if (this.$refs.projectSettings) {
        const isValid = await this.$refs.projectSettings.validate()
        if (isValid) {
          await this.$refs.projectSettings.save()
        }
      }
    },

    async handleSettingsChanged(updatedProject) {
      const index = this.projects.findIndex(p => p.id === updatedProject.id)
      if (index !== -1) {
        this.projects[index] = { ...this.projects[index], ...updatedProject }
      }
      this.closeSettings()
      this.$emit('success', `Settings updated for "${updatedProject.name}"`)
    },

    async handleProjectDelete(project) {
      if (confirm(`Are you sure you want to delete project "${project.name}"?`)) {
        try {
          await ProjectService.deleteProject(project.id)
          this.projects = this.projects.filter(p => p.id !== project.id)
          this.$emit('success', `Project "${project.name}" deleted successfully`)
        } catch (error) {
          console.error('Failed to delete project:', error)
          this.$emit('error', `Failed to delete project "${project.name}"`)
        }
      }
    },

    handleStatusChange(project, newStatus) {
      project.status = newStatus
    }
  }
}
</script>

<style scoped>
.project-manager {
  padding: 20px;
  background: #1a1a1a;
  color: #ffffff;
  min-height: 100vh;
}

.project-manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #333;
}

.manager-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0;
  color: #ffffff;
}

.add-project-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #007acc;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.add-project-btn:hover {
  background: #005a9e;
}

.icon-plus::before {
  content: '+';
  font-weight: bold;
  font-size: 16px;
}

.project-list-container {
  flex: 1;
}

.btn {
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  padding: 8px 16px;
  transition: all 0.2s;
}

.btn-primary {
  background: #007acc;
  color: white;
}

.btn-primary:hover {
  background: #005a9e;
}
</style>
