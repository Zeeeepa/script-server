/**
 * WSL2 WebSocket Service
 * 
 * Handles real-time communication with the WSL2 backend
 */

class WSL2WebSocketService {
  constructor() {
    this.ws = null
    this.listeners = {}
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 1000
    this.isConnected = false
  }

  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/wsl2`

    try {
      this.ws = new WebSocket(wsUrl)
      this.setupEventHandlers()
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      this.scheduleReconnect()
    }
  }

  setupEventHandlers() {
    this.ws.onopen = () => {
      console.log('WSL2 WebSocket connected')
      this.isConnected = true
      this.reconnectAttempts = 0
      this.emit('connected')
    }

    this.ws.onclose = (event) => {
      console.log('WSL2 WebSocket disconnected:', event.code, event.reason)
      this.isConnected = false
      this.emit('disconnected', { code: event.code, reason: event.reason })
      
      if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnect()
      }
    }

    this.ws.onerror = (error) => {
      console.error('WSL2 WebSocket error:', error)
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

  handleMessage(data) {
    const { type } = data

    switch (type) {
      case 'connection_established':
        this.emit('connected')
        break
      
      case 'subscription_confirmed':
        this.emit('subscription_confirmed', data)
        break
      
      case 'project_status_update':
        this.emit('project_status_update', data)
        break
      
      case 'project_status_changed':
        this.emit('project_status_changed', data)
        break
      
      case 'port_monitoring_update':
        this.emit('port_monitoring_update', data)
        break
      
      case 'port_conflict_detected':
        this.emit('port_conflict_detected', data)
        break
      
      case 'health_monitoring_update':
        this.emit('health_monitoring_update', data)
        break
      
      case 'health_alert':
        this.emit('health_alert', data)
        break
      
      case 'instance_status_update':
        this.emit('instance_status_update', data)
        break
      
      case 'error':
        console.error('WebSocket error:', data.error)
        this.emit('error', data)
        break
      
      default:
        console.log('Unknown WebSocket message type:', type, data)
    }
  }

  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
    
    setTimeout(() => {
      this.connect()
    }, delay)
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, cannot send message:', message)
    }
  }

  // Subscription methods
  subscribe(subscriptionType, options = {}) {
    this.send({
      type: 'subscribe',
      subscription_type: subscriptionType,
      ...options
    })
  }

  unsubscribe(subscriptionType) {
    this.send({
      type: 'unsubscribe',
      subscription_type: subscriptionType
    })
  }

  // Status requests
  getStatus(statusType) {
    this.send({
      type: 'get_status',
      status_type: statusType
    })
  }

  // Project actions via WebSocket
  executeProjectAction(projectId, action) {
    this.send({
      type: 'project_action',
      project_id: projectId,
      action: action
    })
  }

  // Event listener management
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = []
    }
    this.listeners[event].push(callback)
  }

  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback)
    }
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error(`Error in WebSocket event listener for ${event}:`, error)
        }
      })
    }
  }

  // Connection management
  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
    }
  }

  isConnectedToServer() {
    return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN
  }

  // Utility methods for common subscriptions
  subscribeToAllProjects() {
    this.subscribe('project_status')
  }

  subscribeToProject(projectId) {
    this.subscribe('project_status', { project_id: projectId })
  }

  subscribeToPortMonitoring(instanceName = null) {
    this.subscribe('port_monitoring', instanceName ? { instance_name: instanceName } : {})
  }

  subscribeToHealthMonitoring() {
    this.subscribe('health_monitoring')
  }

  subscribeToInstanceStatus() {
    this.subscribe('instance_status')
  }
}

export const wsl2WebSocket = new WSL2WebSocketService()
