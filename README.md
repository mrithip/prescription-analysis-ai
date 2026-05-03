# MedScan AI - Clinical Prescription Intelligence

**MedScan AI** is a Flask-based web application that uses OCR and AI to analyze prescription images and provide clinical insights. It combines Tesseract OCR with a local LLM using llama.cpp for medication identification and clinical analysis.

## Features

- **Image Upload**: Drag-and-drop prescription image upload
- **OCR Processing**: Tesseract-based text extraction with contrast enhancement
- **AI Analysis**: Local LLM for clinical pharmacology insights
- **PDF Export**: Generate professional clinical reports
- **Modern UI**: Responsive Tailwind CSS interface
- **Comprehensive Testing**: 28 E2E test cases with Playwright (positive, negative, edge, heartbreak)
- **CI/CD Ready**: GitHub Actions workflow with automatic testing and artifact generation

## Prerequisites

### System Dependencies
- **Tesseract OCR**: Required for image text extraction
  ```bash
  sudo apt update
  sudo apt install tesseract-ocr
  ```
- **Docker** (optional, for containerized deployment)

### Python Version
- Python 3.8+

## Installation

1. **Clone/Navigate to project**:
   ```bash
   cd /home/bunnyblack/program/medicalai
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Local Development

1. **Run the Flask app**:
   ```bash
   python main.py
   ```

2. **Access the web UI**:
   ```
   http://localhost:5000
   ```

3. **Upload prescription image** and click "Analyze"

4. **Download PDF report** with clinical insights

### Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **For testing with mocked AI** (no GGUF model required):
   ```bash
   docker run -d --name medscanai -p 5000:5000 -e TEST_MODE=true .
   ```

3. **Access the web UI**:
   ```
   http://localhost:5000
   ```

## Testing

### Quick Start

```bash
# Install test dependencies
pip install -r requirements.txt
python3 -m playwright install chromium

# Generate fixture image
python3 scripts/generate_rx_fixture.py

# Build and start container with TEST_MODE=true
docker build -t medscanai-ci .
docker run -d --name medscanai-test -p 5000:5000 -e TEST_MODE=true medscanai-ci

# Run all tests
pytest tests/test_app.py -v

# Generate HTML report
pytest tests/test_app.py --html=reports/test-report.html

# Stop container
docker stop medscanai-test && docker rm medscanai-test
```

### Test Categories (28 Total Tests)

**Positive Cases (5 tests)**
- Home page loads with correct UI
- Upload and analysis workflow completes
- Analysis contains required sections
- PDF download succeeds
- Image displays after upload

**Negative Cases (6 tests)**
- Missing file upload handling (400)
- Empty file validation
- Corrupted image error (500)
- Text file instead of image
- Non-existent request cancellation (404)
- Wrong form field name

**Edge Cases (6 tests)**
- Large file uploads (10MB+)
- Special characters in filenames
- Multiple file fields
- Zero-byte files
- Unicode filenames

**Heartbreak Cases (9 tests)**
- Rapid consecutive uploads
- Request cancellation mid-analysis
- JSON response structure validation
- Concurrent simultaneous requests
- Loader visibility transitions
- PDF file size verification
- Drop zone state changes

**Integration Tests (2 tests)**
- Complete user journey
- UI reset after "New Analysis"

See [TESTING.md](TESTING.md) for detailed test documentation.

### Run Specific Test Categories

```bash
pytest tests/test_app.py::TestPositiveCases -v
pytest tests/test_app.py::TestNegativeCases -v
pytest tests/test_app.py::TestEdgeCases -v
pytest tests/test_app.py::TestHeartbreakerCases -v
pytest tests/test_app.py::TestIntegration -v
```

### CI/CD Pipeline

GitHub Actions automatically runs all tests on:
- Push to `main` branch
- Pull requests

Workflow: [.github/workflows/test.yml](.github/workflows/test.yml)
- Builds Docker image
- Starts container with `TEST_MODE=true`
- Installs Playwright browsers
- Runs 28 test cases
- Uploads HTML report as artifact

## Project Structure

```
medicalai/
├── main.py                 # Flask app & OCR/AI logic
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker container setup
├── docker-compose.yml      # Docker Compose configuration
├── .gitignore              # Git ignore rules
├── .dockerignore           # Docker build ignore
├── README.md               # This file
├── TESTING.md              # Testing documentation
├── scripts/
│   └── generate_rx_fixture.py  # Fixture image generator
├── templates/
│   └── index.html          # Web UI with PDF generation
├── tests/
│   ├── test_app.py         # Comprehensive E2E test suite (28 tests)
│   └── fixtures/
│       └── rx.jpg          # Dummy prescription image
├── models/
│   └── *.gguf              # Local AI model (excluded from git)
└── reports/
    └── test-report.html    # HTML test report (generated)
```

## Configuration

### Environment Variables

- `TEST_MODE=true` - Enable mock AI responses (for testing without GGUF model)
- `FLASK_DEBUG=true` - Enable Flask debug mode
- `FLASK_ENV=production` - Set production environment

### Model Loading

The AI model is automatically loaded from the `models/` directory:

```python
# When TEST_MODE=false (production)
# Loads any .gguf, .bin, .safetensors, .pt, or .ckpt file

# When TEST_MODE=true (testing)
# Returns hardcoded mock analysis (no model needed)
```

## API Endpoints

- `GET /` - Render web interface
- `POST /analyze` - Upload & analyze prescription
  - **Request**: multipart/form-data with `file` field (image)
  - **Response**: JSON with `request_id`, `image_data`, `analysis_html`
- `POST /cancel/<request_id>` - Cancel ongoing analysis
  - **Response**: JSON with status ("cancelled" or "not_found")

## Medical Disclaimer

⚠️ **This tool is for informational purposes only.** AI-generated reports do not replace professional medical advice. Always consult a qualified healthcare provider for diagnosis and treatment decisions.

## Dependencies

Key packages:
- **Flask** - Web framework
- **pytesseract** - OCR interface
- **Pillow** - Image processing
- **llama-cpp-python** - Local LLM inference
- **Playwright** - E2E testing
- **pytest** - Test runner

See [requirements.txt](requirements.txt) for full list.

## License

MIT License - Feel free to modify and distribute.
