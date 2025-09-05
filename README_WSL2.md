# WSL2 Project Management System

A comprehensive WSL2 project management system built on top of Script-Server, providing intelligent project discovery, execution, and monitoring capabilities.

## 🚀 Features

### 🔍 **Smart Project Discovery**
- **Auto-detection**: Automatically discovers Node.js, Python, Docker, Go, Java, .NET projects
- **Intelligent Configuration**: Generates optimal start/stop scripts, port configurations, and health checks
- **Multi-instance Support**: Scans across multiple WSL2 instances simultaneously
- **File Analysis**: Parses package.json, requirements.txt, docker-compose.yml for project metadata

### ⚡ **Real-time Project Management**
- **One-click Operations**: Start, stop, restart projects with dependency management
- **Live Status Updates**: Real-time project status via WebSocket connections
- **Bulk Operations**: Start/stop multiple projects across instances
- **Dependency Handling**: Automatic startup sequencing for project dependencies

### 🌐 **Intelligent Port Management**
- **Port Monitoring**: Real-time tracking of port usage across WSL2 instances
- **Conflict Detection**: Automatic detection and alerting of port conflicts
- **Usage Statistics**: Comprehensive port usage analytics and reporting
- **Health Monitoring**: HTTP, TCP, and command-based health checks

### 🎨 **Modern Web Interface**
- **Responsive Dashboard**: Modern Vue.js interface with real-time updates
- **Project Cards**: Visual project management with status indicators
- **Filtering & Search**: Advanced filtering by instance, type, and status
- **Mobile-friendly**: Responsive design for desktop and mobile devices

### 🔧 **Developer Experience**
- **Configuration Templates**: Pre-built templates for different project types
- **Validation**: Comprehensive configuration validation and error reporting
- **Integration**: Seamless integration with existing Script-Server functionality
- **Extensible**: Plugin-based architecture for custom project types

## 📋 Requirements

- **Windows 10/11** with WSL2 enabled
- **Python 3.8+** for Script-Server backend
- **Node.js 14+** for frontend development (optional)
- **WSL2 Instances** with your development projects

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-org/script-server.git
cd script-server

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies (optional)
cd web-src
npm install
cd ..
```

### 2. Configuration

Create a WSL2 project configuration:

```json
{
  "name": "My Node.js App",
  "description": "Node.js application with auto-discovery",
  "script": "./start.sh",
  "working_directory": "/home/user/myapp",
  
  "wsl_instance": "Ubuntu",
  "project_type": "nodejs",
  "ports": [3000, 3001],
  "environment": {
    "NODE_ENV": "development",
    "PORT": "3000"
  },
  "health_check": {
    "type": "http",
    "url": "http://localhost:3000/health",
    "interval": 30,
    "timeout": 10,
    "retries": 3
  },
  "dependencies": [],
  "auto_restart": false
}
```

### 3. Auto-Discovery

Use the discovery feature to automatically find and configure projects:

```bash
# Discover projects in all running WSL2 instances
python -m src.projects.project_discovery --discover-all

# Discover projects in specific instance
python -m src.projects.project_discovery --instance Ubuntu --path /home/user
```

### 4. Start the Server

```bash
# Start Script-Server with WSL2 integration
python server.py --config-dir configs/
```

Navigate to `http://localhost:5000` to access the WSL2 Project Manager dashboard.

## 🏗️ Architecture

### Foundation Approach
The WSL2 Project Management System extends Script-Server's proven architecture by treating WSL2 projects as enhanced scripts with additional metadata (instance, ports, health checks, dependencies).

### Key Benefits
- ✅ **80% Infrastructure Reuse**: Leverages existing execution engine, WebSocket system, Vue.js frontend
- ✅ **Backward Compatibility**: All existing Script-Server functionality remains intact
- ✅ **Proven Stability**: Built on battle-tested codebase with years of development

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    WSL2 Project Manager                     │
├─────────────────────────────────────────────────────────────┤
│  Vue.js Dashboard  │  WebSocket  │  REST API  │  Discovery  │
├─────────────────────────────────────────────────────────────┤
│     Port Monitor   │   Health    │  Project   │   Config    │
│                    │   Checker   │  Executor  │ Validator   │
├─────────────────────────────────────────────────────────────┤
│                 WSL2 Service Layer                          │
├─────────────────────────────────────────────────────────────┤
│              Script-Server Core Engine                      │
├─────────────────────────────────────────────────────────────┤
│                    WSL2 Instances                           │
│    Ubuntu    │    Debian    │   Custom    │    Alpine      │
└─────────────────────────────────────────────────────────────┘
```

## 📚 API Reference

### REST API Endpoints

#### Projects
- `GET /api/wsl2/projects` - List all projects with filtering
- `POST /api/wsl2/projects` - Create or update a project
- `GET /api/wsl2/projects/{id}` - Get project details
- `DELETE /api/wsl2/projects/{id}` - Delete a project
- `POST /api/wsl2/projects/{id}/start` - Start a project
- `POST /api/wsl2/projects/{id}/stop` - Stop a project
- `POST /api/wsl2/projects/{id}/restart` - Restart a project

#### Instances
- `GET /api/wsl2/instances` - List WSL2 instances
- `POST /api/wsl2/instances` - Start/stop WSL2 instance

#### Discovery
- `POST /api/wsl2/discovery` - Discover projects in WSL2 instances

#### Monitoring
- `GET /api/wsl2/ports` - Get port usage information
- `GET /api/wsl2/health` - Get health monitoring data

#### Bulk Operations
- `POST /api/wsl2/bulk/start` - Start multiple projects
- `POST /api/wsl2/bulk/stop` - Stop multiple projects

### WebSocket Events

#### Subscriptions
- `project_status` - Subscribe to project status updates
- `port_monitoring` - Subscribe to port monitoring updates
- `health_monitoring` - Subscribe to health alerts
- `instance_status` - Subscribe to WSL2 instance status

#### Events
- `project_status_changed` - Project status change notification
- `port_conflict_detected` - Port conflict alert
- `health_alert` - Health check failure notification
- `instance_status_update` - WSL2 instance status change

## 🔧 Configuration

### Project Types

The system supports automatic detection and configuration for:

#### Node.js Projects
```json
{
  "project_type": "nodejs",
  "detection_files": ["package.json"],
  "start_script": "npm start",
  "stop_script": "pkill -f node",
  "default_ports": [3000],
  "health_check": {
    "type": "http",
    "url": "http://localhost:3000"
  }
}
```

#### Python Projects
```json
{
  "project_type": "python",
  "detection_files": ["requirements.txt", "setup.py", "pyproject.toml"],
  "start_script": "python app.py",
  "stop_script": "pkill -f python",
  "default_ports": [8000, 5000],
  "health_check": {
    "type": "http",
    "url": "http://localhost:8000"
  }
}
```

#### Docker Projects
```json
{
  "project_type": "docker",
  "detection_files": ["docker-compose.yml", "Dockerfile"],
  "start_script": "docker-compose up -d",
  "stop_script": "docker-compose down",
  "default_ports": [80, 443],
  "health_check": {
    "type": "command",
    "command": "docker-compose ps"
  }
}
```

### Health Check Types

#### HTTP Health Check
```json
{
  "type": "http",
  "url": "http://localhost:3000/health",
  "method": "GET",
  "timeout": 10,
  "interval": 30,
  "retries": 3,
  "expected_status": 200
}
```

#### TCP Health Check
```json
{
  "type": "tcp",
  "host": "localhost",
  "port": 3000,
  "timeout": 5,
  "interval": 30,
  "retries": 3
}
```

#### Command Health Check
```json
{
  "type": "command",
  "command": "curl -f http://localhost:3000/health",
  "timeout": 10,
  "interval": 30,
  "retries": 3,
  "expected_exit_code": 0
}
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test suite
python -m pytest tests/test_wsl2_integration.py

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Cross-component functionality
- **API Tests**: REST API endpoint testing
- **WebSocket Tests**: Real-time communication testing
- **Discovery Tests**: Project discovery and configuration

## 🚀 Deployment

### Production Setup

1. **Environment Configuration**
```bash
export SCRIPT_SERVER_CONFIG_DIR=/path/to/configs
export WSL2_DISCOVERY_ENABLED=true
export WSL2_MONITORING_INTERVAL=30
```

2. **Service Configuration**
```ini
[Unit]
Description=WSL2 Project Manager
After=network.target

[Service]
Type=simple
User=scriptserver
WorkingDirectory=/opt/script-server
ExecStart=/opt/script-server/venv/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. **Nginx Configuration**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /ws/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🤝 Contributing

### Development Setup

1. **Fork and Clone**
```bash
git clone https://github.com/your-username/script-server.git
cd script-server
```

2. **Create Development Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
```

3. **Frontend Development**
```bash
cd web-src
npm install
npm run dev  # Start development server
```

4. **Run Tests**
```bash
python -m pytest tests/
npm test  # Frontend tests
```

### Code Style

- **Python**: Follow PEP 8, use `black` for formatting
- **JavaScript**: Use ESLint and Prettier
- **Vue.js**: Follow Vue.js style guide
- **Documentation**: Use docstrings and JSDoc

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with tests
3. Ensure all tests pass
4. Update documentation
5. Submit pull request with detailed description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Script-Server**: Built on the excellent Script-Server foundation
- **Vue.js Community**: For the amazing frontend framework
- **WSL2 Team**: For making Windows development awesome
- **Contributors**: Thanks to all contributors who make this project better

## 📞 Support

- **Documentation**: [Wiki](https://github.com/your-org/script-server/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-org/script-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/script-server/discussions)
- **Discord**: [Community Discord](https://discord.gg/your-invite)

---

**Made with ❤️ for the WSL2 development community**
