# Voice Transcriber - Simple Deployment

## 🚀 **Quick Start**

### **Local Development**
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app_main.py

# Access at http://localhost:5001
```

### **Docker Deployment**
```bash
# Simple deployment
./deploy.sh

# Or manually
docker-compose up -d
```

## 📁 **Deployment Files**

- **`Dockerfile`** - Simple container configuration
- **`docker-compose.yml`** - Basic Docker Compose setup
- **`deploy.sh`** - One-command deployment script
- **`requirements.txt`** - Python dependencies

## 🔧 **Configuration**

The application uses environment variables for configuration:

```bash
# Optional environment variables
FLASK_ENV=production
PORT=5001
HOST=0.0.0.0
```

## 📊 **Access**

- **Application**: http://localhost:5001
- **Health Check**: http://localhost:5001/health

## 🛑 **Stop Application**

```bash
# Stop Docker containers
docker-compose down

# Or stop local development
Ctrl+C
```

## 📝 **Notes**

- **Simple Setup**: No complex Nginx or reverse proxy needed
- **Development Ready**: Works out of the box
- **Production Ready**: Can be deployed to any Docker host
- **Clean Structure**: Minimal deployment files
