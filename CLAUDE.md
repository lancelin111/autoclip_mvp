# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AutoClip (自动切片工具) is an AI-powered video clipping and collection recommendation system. It supports automatic Bilibili video download, subtitle extraction, intelligent slicing based on AI analysis, and automatic collection generation.

## Development Commands

### Running the Application

```bash
# Development mode (starts both backend and frontend)
./start_dev.sh

# Backend only
python backend_server.py

# Frontend development server (in frontend directory)
cd frontend
npm run dev
```

### Code Quality & Testing

```bash
# Python tests
pytest tests/

# Frontend linting
cd frontend
npm run lint

# Frontend build check  
cd frontend
npm run build
```

### Docker Deployment

```bash
# One-click deployment
./docker-deploy.sh

# Production deployment
./docker-deploy-prod.sh

# Test Docker environment
./test-docker.sh
```

## Architecture Overview

### Tech Stack
- **Backend**: FastAPI + Python 3.8+ 
- **Frontend**: React + TypeScript + Ant Design + Vite
- **AI Integration**: DashScope (Alibaba) and SiliconFlow APIs for LLM processing
- **Video Processing**: FFmpeg, yt-dlp for downloads
- **Deployment**: Docker with multi-stage builds

### Core Components

1. **Backend Server** (`backend_server.py`): FastAPI REST API server handling all backend operations
2. **Processing Pipeline** (`src/main.py` + `src/pipeline/`): 6-step AI processing workflow
   - Step 1: Outline extraction from subtitles
   - Step 2: Timeline generation 
   - Step 3: Scoring and filtering clips
   - Step 4: Title generation for clips
   - Step 5: Clustering clips into collections
   - Step 6: Video generation (slicing and merging)
3. **Frontend App** (`frontend/`): React SPA for user interaction
4. **Utils** (`src/utils/`): Shared utilities
   - `llm_factory.py`: Unified LLM client factory (DashScope/SiliconFlow)
   - `video_processor.py`: Video slicing and merging operations
   - `bilibili_downloader.py`: Bilibili video download functionality

### Key API Endpoints

- `POST /api/upload` - Upload video and subtitle files
- `POST /api/projects/{id}/process` - Start processing a project
- `GET /api/projects` - List all projects
- `POST /api/bilibili/download` - Download Bilibili video
- `POST /api/settings` - Update API settings
- `GET /api/projects/{id}/download-all` - Download all project outputs as zip

### Configuration

Settings stored in `data/settings.json`:
- API provider selection (dashscope/siliconflow)
- API keys for selected provider
- Model selection
- Processing parameters (chunk_size, score_threshold, etc.)

## Important Considerations

1. **API Keys Required**: The system requires either DashScope or SiliconFlow API keys to function
2. **FFmpeg Dependency**: FFmpeg must be installed for video processing
3. **File Storage**: All uploads and outputs stored in `uploads/` directory structure
4. **Concurrent Processing**: Limited to 1 concurrent processing task to manage resources
5. **Browser Detection**: Bilibili downloads use browser cookies for authentication

## Project Structure

```
autoclip_mvp/
├── backend_server.py      # FastAPI server
├── frontend/              # React frontend
│   ├── src/              # Frontend source
│   └── dist/             # Built frontend (served by backend)
├── src/                  # Backend processing logic
│   ├── pipeline/         # 6-step processing pipeline
│   └── utils/           # Shared utilities
├── uploads/             # User uploads and outputs
│   └── {project_id}/    # Per-project files
├── data/                # Configuration storage
└── prompt/              # AI prompt templates by category
```