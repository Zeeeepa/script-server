<template>
  <div class="project-settings">
    <div class="settings-tabs">
      <button 
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-button"
        :class="{ 'tab-active': activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <i :class="tab.icon"></i>
        {{ tab.label }}
      </button>
    </div>

    <div class="settings-content">
      <!-- General Settings -->
      <div v-if="activeTab === 'general'" class="settings-section">
        <h3 class="section-title">General Settings</h3>
        
        <div class="form-group">
          <label class="form-label">Project Name</label>
          <input 
            v-model="formData.name"
            type="text"
            class="form-input"
            placeholder="Enter project name"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label">Project Path</label>
          <input 
            v-model="formData.path"
            type="text"
            class="form-input"
            placeholder="Enter project path"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label">Project Type</label>
          <select v-model="formData.project_type" class="form-select">
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
            placeholder="Enter project description"
            rows="3"
          ></textarea>
        </div>
      </div>

      <!-- WSL Settings -->
      <div v-if="activeTab === 'wsl'" class="settings-section">
        <h3 class="section-title">WSL Settings</h3>
        
        <div class="form-group">
          <label class="form-label">Start command</label>
          <input 
            v-model="formData.wsl_settings.start_command"
            type="text"
            class="form-input"
            placeholder="e.g. /bin/bash"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Start directory path</label>
          <input 
            v-model="formData.wsl_settings.start_directory"
            type="text"
            class="form-input"
            placeholder="/home/"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Start user</label>
          <input 
            v-model="formData.wsl_settings.start_user"
            type="text"
            class="form-input"
            placeholder="(empty the fields for default or if your WSL version does not support it)"
          />
          <small class="form-help">
            (empty the fields for default or if your WSL version does not support it)
          </small>
        </div>

        <ExpandableSection title="WSL Settings" :expanded="wslExpanded" @toggle="wslExpanded = !wslExpanded">
          <div class="expandable-content">
            <div class="form-group">
              <label class="form-label">Distribution</label>
              <select v-model="formData.wsl_settings.distribution" class="form-select">
                <option value="">Default</option>
                <option value="Ubuntu">Ubuntu</option>
                <option value="Ubuntu-20.04">Ubuntu 20.04</option>
                <option value="Ubuntu-22.04">Ubuntu 22.04</option>
                <option value="Debian">Debian</option>
                <option value="Alpine">Alpine</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Environment Variables</label>
              <textarea 
                v-model="formData.wsl_settings.environment_variables"
                class="form-textarea"
                placeholder="KEY1=value1&#10;KEY2=value2"
                rows="4"
              ></textarea>
            </div>
          </div>
        </ExpandableSection>
      </div>

      <!-- System Settings -->
      <div v-if="activeTab === 'system'" class="settings-section">
        <h3 class="section-title">System Settings</h3>
        
        <div class="form-group">
          <div class="toggle-group">
            <ToggleSwitch 
              v-model="formData.system_settings.systemd_enabled"
              :show-labels="false"
            />
            <label class="toggle-label">Systemd</label>
          </div>
        </div>

        <ExpandableSection title="Automount" :expanded="automountExpanded" @toggle="automountExpanded = !automountExpanded">
          <div class="expandable-content">
            <div class="form-group">
              <div class="toggle-group">
                <ToggleSwitch 
                  v-model="formData.system_settings.automount_enabled"
                  :show-labels="false"
                />
                <label class="toggle-label">Enabled</label>
              </div>
            </div>

            <div class="form-group">
              <div class="toggle-group">
                <ToggleSwitch 
                  v-model="formData.system_settings.mounts_tab_enabled"
                  :show-labels="false"
                />
                <label class="toggle-label">MountsTab</label>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Root</label>
              <input 
                v-model="formData.system_settings.mount_root"
                type="text"
                class="form-input"
                placeholder="Enter mount root path"
              />
            </div>

            <div class="form-group">
              <label class="form-label">Options</label>
              <input 
                v-model="formData.system_settings.mount_options"
                type="text"
                class="form-input"
                placeholder="Enter mount options"
              />
            </div>
          </div>
        </ExpandableSection>
      </div>

      <!-- Advanced Settings -->
      <div v-if="activeTab === 'advanced'" class="settings-section">
        <h3 class="section-title">Advanced Settings</h3>
        
        <div class="form-group">
          <label class="form-label">Port Range</label>
          <div class="port-range">
            <input 
              v-model.number="formData.advanced_settings.port_range_start"
              type="number"
              class="form-input"
              placeholder="Start"
              min="1024"
              max="65535"
            />
            <span class="port-separator">-</span>
            <input 
              v-model.number="formData.advanced_settings.port_range_end"
              type="number"
              class="form-input"
              placeholder="End"
              min="1024"
              max="65535"
            />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Health Check URL</label>
          <input 
            v-model="formData.advanced_settings.health_check_url"
            type="url"
            class="form-input"
            placeholder="http://localhost:3000/health"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Startup Timeout (seconds)</label>
          <input 
            v-model.number="formData.advanced_settings.startup_timeout"
            type="number"
            class="form-input"
            placeholder="30"
            min="1"
            max="300"
          />
        </div>

        <div class="form-group">
          <div class="toggle-group">
            <ToggleSwitch 
              v-model="formData.advanced_settings.auto_restart"
              :show-labels="false"
            />
            <label class="toggle-label">Auto Restart on Failure</label>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ToggleSwitch from './ToggleSwitch.vue'
import ExpandableSection from './ExpandableSection.vue'
import { ProjectService } from '../services/ProjectService.js'

export default {
  name: 'ProjectSettings',
  components: {
    ToggleSwitch,
    ExpandableSection
  },
  props: {
    project: {
      type: Object,
      required: true
    }
  },
  emits: ['settings-changed'],
  data() {
    return {
      activeTab: 'general',
      wslExpanded: false,
      automountExpanded: false,
      formData: {
        name: '',
        path: '',
        project_type: 'nodejs',
        description: '',
        wsl_settings: {
          start_command: '/bin/bash',
          start_directory: '/home/',
          start_user: '',
          distribution: '',
          environment_variables: ''
        },
        system_settings: {
          systemd_enabled: false,
          automount_enabled: false,
          mounts_tab_enabled: false,
          mount_root: '',
          mount_options: ''
        },
        advanced_settings: {
          port_range_start: 3000,
          port_range_end: 3999,
          health_check_url: '',
          startup_timeout: 30,
          auto_restart: false
        }
      },
      tabs: [
        { id: 'general', label: 'General', icon: 'icon-settings' },
        { id: 'wsl', label: 'WSL', icon: 'icon-terminal' },
        { id: 'system', label: 'System', icon: 'icon-system' },
        { id: 'advanced', label: 'Advanced', icon: 'icon-advanced' }
      ]
    }
  },
  mounted() {
    this.loadProjectData()
  },
  methods: {
    loadProjectData() {
      if (this.project) {
        this.formData = {
          ...this.formData,
          ...this.project,
          wsl_settings: {
            ...this.formData.wsl_settings,
            ...(this.project.wsl_settings || {})
          },
          system_settings: {
            ...this.formData.system_settings,
            ...(this.project.system_settings || {})
          },
          advanced_settings: {
            ...this.formData.advanced_settings,
            ...(this.project.advanced_settings || {})
          }
        }
      }
    },

    async validate() {
      const errors = []
      
      if (!this.formData.name.trim()) {
        errors.push('Project name is required')
      }
      
      if (!this.formData.path.trim()) {
        errors.push('Project path is required')
      }
      
      if (this.formData.advanced_settings.port_range_start >= this.formData.advanced_settings.port_range_end) {
        errors.push('Port range start must be less than end')
      }
      
      if (errors.length > 0) {
        alert('Validation errors:\n' + errors.join('\n'))
        return false
      }
      
      return true
    },

    async save() {
      try {
        const updatedProject = await ProjectService.updateProject(this.project.id, this.formData)
        this.$emit('settings-changed', updatedProject)
        return true
      } catch (error) {
        console.error('Failed to save project settings:', error)
        alert('Failed to save project settings')
        return false
      }
    }
  }
}
</script>

<style scoped>
.project-settings {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.settings-tabs {
  display: flex;
  border-bottom: 1px solid #404040;
  margin-bottom: 24px;
}

.tab-button {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 12px 16px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-button:hover {
  color: #ccc;
  background: rgba(255, 255, 255, 0.05);
}

.tab-button.tab-active {
  color: #007acc;
  border-bottom-color: #007acc;
}

.settings-content {
  flex: 1;
  overflow-y: auto;
}

.settings-section {
  padding: 0 4px;
}

.section-title {
  font-size: 18px;
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

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.form-help {
  display: block;
  font-size: 12px;
  color: #888;
  margin-top: 4px;
  font-style: italic;
}

.toggle-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toggle-label {
  font-size: 14px;
  color: #ccc;
  cursor: pointer;
}

.port-range {
  display: flex;
  align-items: center;
  gap: 8px;
}

.port-range .form-input {
  flex: 1;
}

.port-separator {
  color: #888;
  font-weight: bold;
}

.expandable-content {
  padding-top: 16px;
}

/* Icons */
.icon-settings::before { content: '⚙️'; }
.icon-terminal::before { content: '💻'; }
.icon-system::before { content: '🖥️'; }
.icon-advanced::before { content: '🔧'; }

@media (max-width: 768px) {
  .settings-tabs {
    flex-wrap: wrap;
  }
  
  .tab-button {
    flex: 1;
    min-width: 0;
    justify-content: center;
  }
  
  .port-range {
    flex-direction: column;
    align-items: stretch;
  }
  
  .port-separator {
    text-align: center;
  }
}
</style>
