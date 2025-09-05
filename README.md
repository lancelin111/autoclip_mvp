# AutoClip - AI-Powered Video Clipping Tool

🎬 An intelligent video clipping and collection recommendation system based on AI, supporting automatic Bilibili video download, subtitle extraction, intelligent slicing, and collection generation.

## 📋 Table of Contents

- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
- [📁 Project Structure](#-project-structure)
- [🔧 Configuration](#-configuration)
- [📖 User Guide](#-user-guide)
- [🛠️ Development Guide](#️-development-guide)
- [🐛 FAQ](#-faq)
- [📝 Changelog](#-changelog)
- [📄 License](#-license)
- [🤝 Contributing](#-contributing)
- [📞 Contact](#-contact)

## ✨ Features

- 🔥 **Intelligent Video Clipping**: AI-powered video content analysis for high-quality automatic clipping
- 📺 **Bilibili Video Download**: Support for automatic Bilibili video download and subtitle extraction
- 🎯 **Smart Collection Recommendations**: AI automatically analyzes slice content and recommends related collections
- 🎨 **Manual Collection Editing**: Support drag-and-drop sorting, adding/removing slices
- 📦 **One-Click Package Download**: Support one-click package download for all slices and collections
- 🌐 **Modern Web Interface**: React + TypeScript + Ant Design
- ⚡ **Real-time Processing Status**: Real-time display of processing progress and logs

## 🚀 Quick Start

### Requirements

#### Development Environment
- Python 3.8+
- Node.js 16+
- DashScope API Key or SiliconFlow API Key (for AI analysis)

#### Docker Deployment (Recommended)
- Docker 20.10+
- Docker Compose 2.0+
- DashScope API Key or SiliconFlow API Key (for AI analysis)

### Installation

#### 🐳 Docker Deployment (Recommended)

**One-click deployment, no complex environment setup required!**

```bash
# 1. Clone the project
git clone git@github.com:lancelin/autoclip_mvp.git
cd autoclip_mvp

# 2. Configure environment variables
cp env.example .env
# Edit .env file and configure your API keys

# 3. One-click deployment
./docker-deploy.sh
```

**Access URL**: http://localhost:8000

📖 **Detailed Deployment Guide**: [Docker Deployment Guide](DOCKER_DEPLOY.md)

#### 🔧 Development Environment

1. **Clone the project**
```bash
git clone git@github.com:lancelin/autoclip_mvp.git
cd autoclip_mvp
```

2. **Install backend dependencies**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

3. **Install frontend dependencies**
```bash
cd frontend
npm install
cd ..
```

4. **Configure API keys**
```bash
# Copy example configuration file
cp data/settings.example.json data/settings.json

# Edit configuration file and add your API key
# Choose between DashScope and SiliconFlow APIs:

# For DashScope:
{
  "api_provider": "dashscope",
  "dashscope_api_key": "your-dashscope-api-key",
  "model_name": "qwen-plus",
  "chunk_size": 5000,
  "min_score_threshold": 0.7,
  "max_clips_per_collection": 5,
  "default_browser": "chrome"
}

# For SiliconFlow:
{
  "api_provider": "siliconflow",
  "siliconflow_api_key": "your-siliconflow-api-key",
  "siliconflow_model": "Qwen/Qwen2.5-72B-Instruct",
  "chunk_size": 5000,
  "min_score_threshold": 0.7,
  "max_clips_per_collection": 5,
  "default_browser": "chrome"
}
```

### Start Services

#### Method 1: Using startup script (Recommended)
```bash
chmod +x start_dev.sh
./start_dev.sh
```

#### Method 2: Manual startup
```bash
# Start backend service
source venv/bin/activate
python backend_server.py

# Open new terminal, start frontend service
cd frontend
npm run dev
```

#### Method 3: Command line tool
```bash
# Process local video files
python main.py --video input.mp4 --srt input.srt --project-name "My Project"

# Process existing project
python main.py --project-id <project_id>

# List all projects
python main.py --list-projects
```

### Access URLs

#### Docker Deployment
- 🌐 **Frontend Interface**: http://localhost:8000
- 📚 **API Documentation**: http://localhost:8000/docs

#### Development Environment
- 🌐 **Frontend Interface**: http://localhost:3000
- 🔌 **Backend API**: http://localhost:8000
- 📚 **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
autoclip_mvp/
├── backend_server.py          # FastAPI backend service
├── main.py                   # Command line entry
├── start_dev.sh              # Development environment startup script
├── requirements.txt           # Python dependencies
├── .gitignore               # Git ignore file
├── README.md                # Project documentation
│
├── Dockerfile               # Docker image build file
├── docker-compose.yml       # Docker Compose configuration
├── docker-compose.prod.yml  # Production Docker configuration
├── docker-deploy.sh         # Docker one-click deployment script
├── docker-deploy-prod.sh    # Production deployment script
├── test-docker.sh           # Docker environment test script
├── env.example              # Environment variables example file
├── .dockerignore           # Docker build ignore file
│
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── store/          # State management
│   │   └── hooks/          # Custom Hooks
│   ├── package.json        # Frontend dependencies
│   └── vite.config.ts      # Vite configuration
│
├── src/                    # Core business logic
│   ├── main.py            # Main processing logic
│   ├── config.py          # Configuration management
│   ├── api.py             # API interfaces
│   ├── pipeline/          # Processing pipeline
│   │   ├── step1_outline.py    # Outline extraction
│   │   ├── step2_timeline.py   # Timeline generation
│   │   ├── step3_scoring.py    # Score calculation
│   │   ├── step4_title.py      # Title generation
│   │   ├── step5_clustering.py # Clustering analysis
│   │   └── step6_video.py      # Video generation
│   ├── utils/             # Utility functions
│   │   ├── llm_client.py      # DashScope AI client
│   │   ├── siliconflow_client.py # SiliconFlow AI client
│   │   ├── llm_factory.py     # LLM client factory
│   │   ├── video_processor.py # Video processing
│   │   ├── text_processor.py  # Text processing
│   │   ├── project_manager.py # Project management
│   │   ├── error_handler.py   # Error handling
│   │   └── bilibili_downloader.py # Bilibili downloader
│   └── upload/            # File upload
│       └── upload_manager.py
│
├── data/                  # Data files
│   ├── projects.json     # Project data
│   └── settings.json     # Configuration file
│
├── uploads/              # Upload file storage
│   ├── tmp/             # Temporary download files
│   └── {project_id}/    # Project files
│       ├── input/       # Original files
│       └── output/      # Processing results
│           ├── clips/   # Sliced videos
│           └── collections/ # Collection videos
│
├── prompt/               # AI prompt templates
│   ├── business/        # Business & Finance
│   ├── knowledge/       # Knowledge & Science
│   ├── entertainment/   # Entertainment content
│   └── ...
│
└── tests/               # Test files
    ├── test_config.py
    └── test_error_handler.py
```

## 🔧 Configuration

### API Key Configuration
Configure your API keys in `data/settings.json`. You can choose between DashScope and SiliconFlow APIs:

#### DashScope Configuration
```json
{
  "api_provider": "dashscope",
  "dashscope_api_key": "your-dashscope-api-key",
  "model_name": "qwen-plus",
  "chunk_size": 5000,
  "min_score_threshold": 0.7,
  "max_clips_per_collection": 5,
  "default_browser": "chrome"
}
```

#### SiliconFlow Configuration
```json
{
  "api_provider": "siliconflow",
  "siliconflow_api_key": "your-siliconflow-api-key",
  "siliconflow_model": "Qwen/Qwen2.5-72B-Instruct",
  "chunk_size": 5000,
  "min_score_threshold": 0.7,
  "max_clips_per_collection": 5,
  "default_browser": "chrome"
}
```

#### Getting API Keys
- **DashScope**: Visit [Alibaba Cloud Console](https://dashscope.console.aliyun.com/) → AI Services → Tongyi Qianwen → API Key Management
- **SiliconFlow**: Visit [SiliconCloud](https://siliconflow.cn) → Login → API Keys → Create New API Key

### Browser Configuration
Support for Chrome, Firefox, Safari and other browsers for Bilibili video download:
```json
{
  "default_browser": "chrome"
}
```

## 📖 User Guide

### 1. Upload Local Video
1. Visit http://localhost:3000
2. Click "Upload Video" button
3. Select video file and subtitle file (required)
4. Fill in project name and category
5. Click "Start Processing"

### 2. Download Bilibili Video
1. Click "Bilibili Video Download" on homepage
2. Enter Bilibili video link (must be a video with subtitles)
3. Select browser (for login status)
4. Click "Start Download"

### 3. Edit Collections
1. Enter project detail page
2. Click collection card to enter edit mode
3. Drag and drop slices to adjust order
4. Add or remove slices
5. Save changes

### 4. Download Project
1. Click download button on project card
2. Automatically package all slices and collections
3. Download complete zip file

## 🐳 Docker Deployment

### Quick Deployment
```bash
# 1. Clone the project
git clone git@github.com:lancelin/autoclip_mvp.git
cd autoclip_mvp

# 2. Configure environment variables
cp env.example .env
# Edit .env file and configure your API keys

# 3. One-click deployment
./docker-deploy.sh
```

### Production Deployment
```bash
# Use production environment configuration
./docker-deploy-prod.sh
```

### Common Docker Commands
```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Update services
docker-compose pull && docker-compose up -d

# Test Docker environment
./test-docker.sh
```

### Environment Variables Configuration
Configure in `.env` file:
```bash
# Choose one API provider
DASHSCOPE_API_KEY=your-dashscope-api-key
# or
SILICONFLOW_API_KEY=your-siliconflow-api-key

# API provider selection
API_PROVIDER=dashscope  # or siliconflow
```

📖 **Detailed Docker Deployment Guide**: [Docker Deployment Guide](DOCKER_DEPLOY.md)

## 🛠️ Development Guide

### Backend Development
```bash
# Start development server (with hot reload)
python backend_server.py

# Run tests
pytest tests/
```

### Frontend Development
```bash
cd frontend
npm run dev    # Development mode
npm run build  # Production build
npm run lint   # Code linting
```

### Adding New Video Categories
1. Create new category folder in `prompt/` directory
2. Add corresponding prompt template files
3. Add category options in frontend `src/services/api.ts`

## 📝 Changelog

### [v1.1.1] - 2025-08-17

#### 🐳 Docker Deployment
- **🚀 One-Click Docker Deployment**: Support for Docker containerized deployment, simplifying environment setup
- **🏗️ Multi-Stage Build**: Optimized Docker image size and improved build efficiency
- **🔧 Production Environment Support**: Provided production Docker configuration and deployment scripts
- **📦 Data Persistence**: Support for volume mounting to ensure data security
- **🛡️ Health Checks**: Integrated container health checks for improved service reliability
- **📚 Deployment Documentation**: Comprehensive Docker deployment guides and quick start documentation

#### 🛠️ Technical Improvements
- **🔧 Backend Optimization**: Enhanced static file serving for Docker environment
- **🎨 Frontend Build**: Optimized production build configuration
- **📋 Environment Management**: Improved environment variable configuration system
- **🔍 Testing**: Added Docker environment testing scripts

---

### [v1.1.0] - 2025-08-03

#### ✨ New Features
- **🔌 SiliconFlow API Support**: Added support for SiliconFlow API as an alternative to DashScope
- **🎛️ Multi-API Provider Selection**: Users can now choose between DashScope and SiliconFlow APIs
- **🔄 Dynamic UI**: Frontend settings page now dynamically shows configuration options based on selected API provider
- **🧪 API Connection Testing**: Added built-in API connection testing functionality for both providers

#### 🔧 Improvements
- **🏭 LLM Factory Pattern**: Implemented unified LLM client factory for better API management
- **⚙️ Enhanced Configuration**: Extended configuration system to support multiple API providers
- **🎨 Improved UI/UX**: Better form validation and user experience in settings page
- **📝 Better Documentation**: Added comprehensive integration guides and troubleshooting

#### 🐛 Bug Fixes
- **🔧 Fixed API Testing**: Resolved issues with API connection testing functionality
- **🎯 Fixed Configuration Loading**: Improved configuration loading and validation
- **🔄 Fixed Provider Switching**: Fixed issues with API provider switching in frontend

#### 🛠️ Technical Changes
- **📦 New Dependencies**: Added `openai` library for SiliconFlow API support
- **🏗️ Architecture**: Implemented factory pattern for LLM client management
- **🔧 Configuration**: Extended settings model to support multiple API providers
- **📱 Frontend**: Enhanced settings page with conditional rendering and better validation

#### 📋 Supported Models

**DashScope (Tongyi Qianwen)**:
- Qwen Plus
- Qwen Turbo
- Qwen Max

**SiliconFlow (Silicon Cloud)**:
- Qwen2.5-72B-Instruct
- Qwen3-8B
- DeepSeek-R1

---

### [v1.0.0] - 2025-07-XX

#### ✨ Initial Release
- **🎬 AI-Powered Video Clipping**: Intelligent video content analysis and automatic clipping
- **📺 Bilibili Video Download**: Support for automatic Bilibili video download and subtitle extraction
- **🎯 Smart Collection Recommendations**: AI automatically analyzes slice content and recommends related collections
- **🎨 Manual Collection Editing**: Support drag-and-drop sorting, adding/removing slices
- **📦 One-Click Package Download**: Support one-click package download for all slices and collections
- **🌐 Modern Web Interface**: React + TypeScript + Ant Design
- **⚡ Real-time Processing Status**: Real-time display of processing progress and logs

---

## 🐛 FAQ

### Q: How do I choose between DashScope and SiliconFlow APIs?
A: Both APIs provide similar AI capabilities. DashScope is from Alibaba Cloud, while SiliconFlow offers access to multiple AI models. Choose based on your needs and API availability.

### Q: Bilibili video download failed?
A: Make sure you're logged into your Bilibili account and select the correct browser. Chrome browser is recommended.

### Q: AI analysis is slow?
A: You can adjust the `chunk_size` parameter. Smaller values will improve speed but may affect quality.

### Q: Slice quality is not good?
A: Adjust the `min_score_threshold` parameter. Higher values will improve slice quality but reduce quantity.

### Q: Too few collections?
A: Adjust the `max_clips_per_collection` parameter to increase the maximum number of slices per collection.

### Q: Docker deployment failed?
A: First run `./test-docker.sh` to check your Docker environment. Make sure Docker and Docker Compose are properly installed, and API keys are configured in the `.env` file.

### Q: Cannot access Docker container?
A: Check if the port is occupied: `netstat -tulpn | grep 8000`. If the port is occupied, you can modify the port mapping in `docker-compose.yml`.

### Q: Data lost after Docker deployment?
A: Make sure the data directories are properly mounted. Check the volumes configuration in `docker-compose.yml`. Data will be saved in the host machine's `./uploads/` and `./output/` directories.

### Q: How to deploy in production environment?
A: Use the `./docker-deploy-prod.sh` script for production deployment. This script will use port 80 and configure automatic restart and log management.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Welcome to submit Issues and Pull Requests!

1. Fork this project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Contact

For questions or suggestions, please contact us through:

### 💬 QQ  
<img src="./qq_qr.jpg" alt="QQ QR Code" width="150">

### 📱 Feishu  
<img src="./feishu_qr.jpg" alt="Feishu QR Code" width="150">

### 📧 Other Contact Methods
- Submit a [GitHub Issue](https://github.com/zhouxiaoka/autoclip_mvp/issues)
- Send email to: christine_zhouye@163.com
- Add the above QQ or Feishu contact

## 🤝 Contributing

Welcome to contribute code! Please see [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

⭐ If this project helps you, please give it a star! 
