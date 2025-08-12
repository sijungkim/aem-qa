# AEM QA Station

**AI-powered translation quality assurance workstation for AEM multilingual websites**

## 📋 System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **RAM**: 8GB (16GB recommended for better AI performance)
- **Storage**: 5GB free space (for dependencies and AI models)
- **OS**: Windows 10+, macOS 10.14+, or Linux

### Recommended for Optimal Performance
- **Python**: 3.10+
- **RAM**: 16GB or more
- **GPU**: NVIDIA GPU with CUDA support (optional, for faster AI processing)
- **Storage**: SSD with 10GB free space

## 🚀 Installation Guide

### Option 1: Standard Installation (CPU Only)

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd aem_qa_system/aem_qa_station
```

#### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv aem_qa_env

# Activate virtual environment
# Windows:
aem_qa_env\Scripts\activate

# macOS/Linux:
source aem_qa_env/bin/activate
```

#### 3. Install Dependencies
```bash
# Standard installation (CPU only)
pip install -r requirements.txt
```

#### 4. Verify Installation
```bash
# Test import of key components
python -c "import streamlit; import pymongo; import sentence_transformers; print('✅ Installation successful!')"
```

### Option 2: GPU-Accelerated Installation (NVIDIA CUDA)

#### Prerequisites
- NVIDIA GPU with CUDA 11.8+ support
- [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) installed

#### 1-2. Same as Option 1 (Clone & Virtual Environment)

#### 3. Install GPU-Optimized Dependencies
```bash
# Install CUDA-enabled PyTorch first
pip install torch>=2.0.0+cu118 --index-url https://download.pytorch.org/whl/cu118

# Then install other dependencies
pip install -r requirements.txt
```

#### 4. Verify GPU Support
```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
```

### Option 3: Lightweight Installation (Minimal Setup)

For users with limited resources or those who want to test basic functionality:

```bash
# Create minimal requirements file
cat > requirements-minimal.txt << EOF
streamlit>=1.28.0
pymongo>=4.5.0
pandas>=2.1.0
openpyxl>=3.1.0
chromadb>=0.4.15
torch>=2.0.0+cpu --index-url https://download.pytorch.org/whl/cpu
sentence-transformers>=2.2.2
EOF

# Install minimal version
pip install -r requirements-minimal.txt
```

## ⚙️ Configuration

### 1. Database Setup

Ensure your MongoDB and ChromaDB connections are configured:

```bash
# Check if MongoDB is accessible
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/'); print('✅ MongoDB connection successful!')"
```

### 2. AI Model Configuration

The system will automatically download AI models on first run:
- **Model**: `intfloat/multilingual-e5-large` (~2.3GB)
- **Location**: `~/.cache/huggingface/transformers/`

To pre-download models:
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-large'); print('✅ AI model downloaded!')"
```

## 🏃‍♂️ Running the Application

### Start the Web Interface
```bash
# Make sure virtual environment is activated
streamlit run app.py
```

### Access the Application
- **Local URL**: http://localhost:8501
- **Network URL**: http://your-ip:8501 (for team access)

### Custom Port (Optional)
```bash
streamlit run app.py --server.port 8502
```

## 🔧 Performance Optimization

### For CPU Users
```bash
# Set threading optimization
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4

# Run with optimized settings
streamlit run app.py
```

### For GPU Users
```bash
# Verify GPU utilization
nvidia-smi

# Monitor GPU usage while running
watch -n 1 nvidia-smi
```

### Memory Optimization
```bash
# For systems with limited RAM
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
streamlit run app.py --server.maxUploadSize 50
```

## 📁 Project Structure

```
aem_qa_station/
├── app.py                     # Main Streamlit application
├── requirements.txt           # Python dependencies
├── modules/
│   ├── __init__.py
│   ├── connections.py         # Database connections
│   ├── analyzer.py           # Page analysis logic
│   ├── searcher.py           # AI translation search
│   └── version_manager.py    # Version management
└── README.md                 # This file
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# If sentence-transformers fails to import
pip uninstall sentence-transformers
pip install sentence-transformers --no-cache-dir
```

#### 2. MongoDB Connection Issues
```bash
# Check MongoDB service
# Windows:
net start MongoDB

# macOS:
brew services start mongodb-community

# Linux:
sudo systemctl start mongod
```

#### 3. Out of Memory Errors
```bash
# Reduce model precision
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1

# Or use smaller model
# Edit modules/searcher.py and change model to:
# 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
```

#### 4. Streamlit Port Already in Use
```bash
# Kill existing Streamlit processes
pkill -f streamlit

# Or use different port
streamlit run app.py --server.port 8502
```

### Performance Monitoring

```bash
# Check system resources
# Windows:
tasklist | findstr python

# macOS/Linux:
top -p $(pgrep python)

# Monitor memory usage
python -c "import psutil; print(f'Available RAM: {psutil.virtual_memory().available / 1024**3:.1f} GB')"
```

## 🔄 Updating

### Update Dependencies
```bash
# Activate virtual environment
source aem_qa_env/bin/activate  # or aem_qa_env\Scripts\activate on Windows

# Update packages
pip install -r requirements.txt --upgrade
```

### Update AI Models
```bash
# Clear model cache
rm -rf ~/.cache/huggingface/transformers/

# Models will be re-downloaded on next run
```

## 📞 Support

### System Information
When reporting issues, please provide:

```bash
# Generate system info
python -c "
import sys, torch, streamlit, pandas, pymongo
print(f'Python: {sys.version}')
print(f'Streamlit: {streamlit.__version__}')
print(f'PyTorch: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
print(f'Pandas: {pandas.__version__}')
print(f'PyMongo: {pymongo.__version__}')
"
```

### Environment Variables
For advanced configuration:

```bash
# Set in your shell or .env file
export STREAMLIT_THEME_BASE="light"           # or "dark"
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200   # MB
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512"
export TOKENIZERS_PARALLELISM=false           # Disable tokenizer warnings
```

---

## 🎯 Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed via `pip install -r requirements.txt`
- [ ] MongoDB accessible
- [ ] AI models downloaded (automatic on first run)
- [ ] Application starts with `streamlit run app.py`
- [ ] Web interface accessible at http://localhost:8501

**Happy analyzing!** 🚀