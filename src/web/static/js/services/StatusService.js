/**
 * Status Service - Handles real-time status updates via WebSocket
 */
class StatusService {
  constructor() {
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 1000
    this.listeners = new Map()
    this.isConnected = false
    this.shouldReconnect = true
  }

  /**
   * Connect to the WebSocket server
   */
  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/status`

    try {
      this.ws = new WebSocket(wsUrl)
      this.setupEventHandlers()
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      this.scheduleReconnect()
    }
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect() {
    this.shouldReconnect = false
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.isConnected = false
  }

  /**
   * Setup WebSocket event handlers
   */
  setupEventHandlers() {
    if (!this.ws) return

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.isConnected = true
      this.reconnectAttempts = 0
      this.emit('connected')
    }

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason)
      this.isConnected = false
      this.emit('disconnected', { code: event.code, reason: event.reason })
      
      if (this.shouldReconnect && event.code !== 1000) {
        this.scheduleReconnect()
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      this.emit('error', error)
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.handleMessage(data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }
  }

  /**
   * Handle incoming WebSocket messages
   * @param {Object} data - Parsed message data
   */
  handleMessage(data) {
    const { type, payload } = data

    switch (type) {
      case 'status_update':
        this.emit('status-update', payload)
        break
      case 'project_started':
        this.emit('project-started', payload)
        break
      case 'project_stopped':
        this.emit('project-stopped', payload)
        break
      case 'project_error':
        this.emit('project-error', payload)
        break
      case 'health_update':
        this.emit('health-update', payload)
        break
      case 'port_update':
        this.emit('port-update', payload)
        break
      case 'log_update':
        this.emit('log-update', payload)
        break
      case 'system_update':
        this.emit('system-update', payload)
        break
      default:
        console.warn('Unknown message type:', type)
        this.emit('message', data)
    }
  }

  /**
   * Schedule a reconnection attempt
   */
  scheduleReconnect() {
    if (!this.shouldReconnect || this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    console.log(`Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`)
    
    setTimeout(() => {
      if (this.shouldReconnect) {
        this.connect()
      }
    }, delay)
  }

  /**
   * Send a message to the server
   * @param {Object} message - Message to send
   */
  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, cannot send message:', message)
    }
  }

  /**
   * Subscribe to project status updates
   * @param {string} projectId - Project ID to subscribe to
   */
  subscribeToProject(projectId) {
    this.send({
      type: 'subscribe',
      payload: {
        project_id: projectId
      }
    })
  }

  /**
   * Unsubscribe from project status updates
   * @param {string} projectId - Project ID to unsubscribe from
   */
  unsubscribeFromProject(projectId) {
    this.send({
      type: 'unsubscribe',
      payload: {
        project_id: projectId
      }
    })
  }

  /**
   * Subscribe to all project updates
   */
  subscribeToAll() {
    this.send({
      type: 'subscribe_all'
    })
  }

  /**
   * Request current status for a project
   * @param {string} projectId - Project ID
   */
  requestStatus(projectId) {
    this.send({
      type: 'get_status',
      payload: {
        project_id: projectId
      }
    })
  }

  /**
   * Request current status for all projects
   */
  requestAllStatus() {
    this.send({
      type: 'get_all_status'
    })
  }

  /**
   * Add event listener
   * @param {string} event - Event name
   * @param {Function} callback - Callback function
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event).add(callback)
  }

  /**
   * Remove event listener
   * @param {string} event - Event name
   * @param {Function} callback - Callback function
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback)
    }
  }

  /**
   * Emit event to all listeners
   * @param {string} event - Event name
   * @param {*} data - Event data
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error)
        }
      })
    }
  }

  /**
   * Convenience method for status updates
   * @param {Function} callback - Callback function
   */
  onStatusUpdate(callback) {
    this.on('status-update', callback)
  }

  /**
   * Convenience method for project started events
   * @param {Function} callback - Callback function
   */
  onProjectStarted(callback) {
    this.on('project-started', callback)
  }

  /**
   * Convenience method for project stopped events
   * @param {Function} callback - Callback function
   */
  onProjectStopped(callback) {
    this.on('project-stopped', callback)
  }

  /**
   * Convenience method for project error events
   * @param {Function} callback - Callback function
   */
  onProjectError(callback) {
    this.on('project-error', callback)
  }

  /**
   * Convenience method for health updates
   * @param {Function} callback - Callback function
   */
  onHealthUpdate(callback) {
    this.on('health-update', callback)
  }

  /**
   * Convenience method for port updates
   * @param {Function} callback - Callback function
   */
  onPortUpdate(callback) {
    this.on('port-update', callback)
  }

  /**
   * Convenience method for log updates
   * @param {Function} callback - Callback function
   */
  onLogUpdate(callback) {
    this.on('log-update', callback)
  }

  /**
   * Convenience method for connection events
   * @param {Function} callback - Callback function
   */
  onConnected(callback) {
    this.on('connected', callback)
  }

  /**
   * Convenience method for disconnection events
   * @param {Function} callback - Callback function
   */
  onDisconnected(callback) {
    this.on('disconnected', callback)
  }

  /**
   * Get connection status
   * @returns {boolean} True if connected
   */
  getConnectionStatus() {
    return this.isConnected
  }

  /**
   * Get WebSocket ready state
   * @returns {number} WebSocket ready state
   */
  getReadyState() {
    return this.ws ? this.ws.readyState : WebSocket.CLOSED
  }

  /**
   * Enable automatic reconnection
   */
  enableReconnect() {
    this.shouldReconnect = true
  }

  /**
   * Disable automatic reconnection
   */
  disableReconnect() {
    this.shouldReconnect = false
  }

  /**
   * Reset reconnection attempts counter
   */
  resetReconnectAttempts() {
    this.reconnectAttempts = 0
  }
}

// Export singleton instance
export { StatusService }
export default new StatusService()
