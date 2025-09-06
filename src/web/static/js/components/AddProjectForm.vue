<template>
  <div class="add-project-form">
    <form @submit.prevent="handleSubmit">
      <div class="form-section">
        <h4 class="section-title">Project Information</h4>
        
        <div class="form-group">
          <label class="form-label">Project Name *</label>
          <input 
            v-model="formData.name"
            type="text"
            class="form-input"
            placeholder="Enter project name"
            required
            :class="{ 'error': errors.name }"
          />
          <span v-if="errors.name" class="error-message">{{ errors.name }}</span>
        </div>

        <div class="form-group">
          <label class="form-label">Project Path *</label>
          <div class="input-with-button">
            <input 
              v-model="formData.path"
              type="text"
              class="form-input"
              placeholder="Enter or browse project path"
              required
              :class="{ 'error': errors.path }"
            />
            <button type="button" class="btn btn-secondary btn-sm" @click="browseDirectory">
              Browse
            </button>
          </div>
          <span v-if="errors.path" class="error-message">{{ errors.path }}</span>
        </div>

        <div class="form-group">
          <label class="form-label">Project Type</label>
          <select v-model="formData.project_type" class="form-select">
            <option value="auto">Auto-detect</option>
            <option value="nodejs">Node.js</option>
            <option value="python">Python</option>
            <option value="docker">Docker</option>
            <option value="go">Go</option>
            <option value="java">Java</option>
            <option value="dotnet">.NET</option>
            <option value="generic">Generic</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Description</label>
          <textarea 
            v-model="formData.description"
            class="form-textarea"
            placeholder="Enter project description (optional)"
            rows="3"
          ></textarea>
        </div>
      </div>

      <div class="form-section">
        <h4 class="section-title">Quick Setup</h4>
        
        <div class="form-group">
          <div class="checkbox-group">
            <input 
              id="auto-discover"
              v-model="autoDiscover"
              type="checkbox"
              class="form-checkbox"
            />
            <label for="auto-discover" class="checkbox-label">
              Auto-discover project settings
            </label>
          </div>
          <small class="form-help">
            Automatically detect project type, start commands, and configuration
          </small>
        </div>

        <div class="form-group">
          <div class="checkbox-group">
            <input 
              id="create-from-template"
              v-model="useTemplate"
              type="checkbox"
              class="form-checkbox"
            />
            <label for="create-from-template" class="checkbox-label">
              Create from template
            </label>
          </div>
        </div>

        <div v-if="useTemplate" class="form-group">
          <label class="form-label">Template</label>
          <select v-model="selectedTemplate" class="form-select">
            <option value="">Select a template</option>
            <option 
              v-for="template in templates"
              :key="template.id"
              :value="template.id"
            >
              {{ template.name }} - {{ template.description }}
            </option>
          </select>
        </div>
      </div>

      <div v-if="!autoDiscover && !useTemplate" class="form-section">
        <h4 class="section-title">Basic Configuration</h4>
        
        <div class="form-group">
          <label class="form-label">Start Command</label>
          <input 
            v-model="formData.start_command"
            type="text"
            class="form-input"
            placeholder="e.g., npm start, python app.py"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Port</label>
          <input 
            v-model.number="formData.port"
            type="number"
            class="form-input"
            placeholder="3000"
            min="1024"
            max="65535"
          />
        </div>
      </div>

      <div class="form-actions">
        <button type="button" class="btn btn-secondary" @click="$emit('cancel')">
          Cancel
        </button>
        <button type="submit" class="btn btn-primary" :disabled="!isValid || creating">
          {{ creating ? 'Creating...' : 'Create Project' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { ProjectService } from '../services/ProjectService.js'

export default {
  name: 'AddProjectForm',
  emits: ['project-created', 'cancel'],
  data() {
    return {
      formData: {
        name: '',
        path: '',
        project_type: 'auto',
        description: '',
        start_command: '',
        port: null
      },
      autoDiscover: true,
      useTemplate: false,
      selectedTemplate: '',
      templates: [],
      errors: {},
      creating: false
    }
  },
  computed: {
    isValid() {
      return this.formData.name.trim() && this.formData.path.trim()
    }
  },
  async mounted() {
    await this.loadTemplates()
  },
  methods: {
    async loadTemplates() {
      try {
        this.templates = await ProjectService.getProjectTemplates()
      } catch (error) {
        console.error('Failed to load templates:', error)
      }
    },

    async browseDirectory() {
      // In a real implementation, this would open a directory picker
      // For now, we'll simulate it
      const path = prompt('Enter project directory path:')
      if (path) {
        this.formData.path = path
        if (this.autoDiscover) {
          await this.discoverProject()
        }
      }
    },

    async discoverProject() {
      if (!this.formData.path) return

      try {
        const projects = await ProjectService.discoverProjects(this.formData.path)
        if (projects.length > 0) {
          const discovered = projects[0]
          this.formData = {
            ...this.formData,
            ...discovered,
            path: this.formData.path // Keep the user-specified path
          }
        }
      } catch (error) {
        console.error('Failed to discover project:', error)
      }
    },

    validate() {
      this.errors = {}

      if (!this.formData.name.trim()) {
        this.errors.name = 'Project name is required'
      }

      if (!this.formData.path.trim()) {
        this.errors.path = 'Project path is required'
      }

      if (this.formData.port && (this.formData.port < 1024 || this.formData.port > 65535)) {
        this.errors.port = 'Port must be between 1024 and 65535'
      }

      return Object.keys(this.errors).length === 0
    },

    async handleSubmit() {
      if (!this.validate()) {
        return
      }

      this.creating = true

      try {
        let project

        if (this.useTemplate && this.selectedTemplate) {
          project = await ProjectService.createFromTemplate(this.selectedTemplate, this.formData)
        } else {
          // Clean up form data
          const projectData = { ...this.formData }
          if (projectData.project_type === 'auto') {
            delete projectData.project_type
          }
          if (!projectData.port) {
            delete projectData.port
          }
          if (!projectData.start_command) {
            delete projectData.start_command
          }

          project = await ProjectService.createProject(projectData)
        }

        this.$emit('project-created', project)
      } catch (error) {
        console.error('Failed to create project:', error)
        alert('Failed to create project: ' + error.message)
      } finally {
        this.creating = false
      }
    },

    async submit() {
      return this.handleSubmit()
    }
  },
  watch: {
    'formData.path'() {
      if (this.autoDiscover && this.formData.path) {
        this.discoverProject()
      }
    },

    useTemplate(newValue) {
      if (newValue) {
        this.autoDiscover = false
      }
    },

    autoDiscover(newValue) {
      if (newValue) {
        this.useTemplate = false
        if (this.formData.path) {
          this.discoverProject()
        }
      }
    }
  }
}
</script>

<style scoped>
.add-project-form {
  max-width: 600px;
}

.form-section {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #404040;
}

.form-section:last-of-type {
  border-bottom: none;
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 20px 0;
  color: #ffffff;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #ccc;
  margin-bottom: 6px;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  background: #404040;
  border: 1px solid #555;
  border-radius: 4px;
  color: #ffffff;
  font-size: 14px;
  padding: 10px 12px;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #007acc;
  box-shadow: 0 0 0 2px rgba(0, 122, 204, 0.2);
}

.form-input.error {
  border-color: #dc3545;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.input-with-button {
  display: flex;
  gap: 8px;
}

.input-with-button .form-input {
  flex: 1;
}

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-checkbox {
  width: 16px;
  height: 16px;
  accent-color: #007acc;
}

.checkbox-label {
  font-size: 14px;
  color: #ccc;
  cursor: pointer;
}

.form-help {
  display: block;
  font-size: 12px;
  color: #888;
  margin-top: 4px;
  font-style: italic;
}

.error-message {
  display: block;
  font-size: 12px;
  color: #dc3545;
  margin-top: 4px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #404040;
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

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
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

@media (max-width: 768px) {
  .form-actions {
    flex-direction: column;
  }
  
  .form-actions .btn {
    width: 100%;
  }
  
  .input-with-button {
    flex-direction: column;
  }
}
</style>
