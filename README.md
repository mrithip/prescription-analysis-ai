# MedScan AI - Clinical Prescription Intelligence

**MedScan AI** is a Flask-based web application that uses OCR and AI to analyze prescription images and provide clinical insights. It combines Tesseract OCR with a local LLM using llama.cpp for medication identification and clinical analysis.

## Features

- **Image Upload**: Drag-and-drop prescription image upload
- **OCR Processing**: Tesseract-based text extraction with contrast enhancement
- **AI Analysis**: Local LLM for clinical pharmacology insights
- **PDF Export**: Generate professional clinical reports
- **Modern UI**: Responsive Tailwind CSS interface

## Prerequisites

### System Dependencies
- **Tesseract OCR**: Required for image text extraction
  ```bash
  sudo apt update
  sudo apt install tesseract-ocr
  ```

### Python Version
- Python 3.8+

## Installation

1. **Clone/Navigate to project**:
   ```bash
   cd /home/bunnyblack/program/medicalai
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
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

2. **Access the web UI**:
   ```
   http://localhost:5000
   ```

## Project Structure

```
medicalai/
├── main.py                 # Flask app & OCR/AI logic
├── templates/
│   └── index.html         # Web UI with PDF generation
├── models/
│   └── Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf or any # Local AI model
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker container setup
├── docker-compose.yml      # Docker Compose configuration
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Configuration

The AI model is automatically loaded from the `models/` directory. Ensure the GGUF model file is present.

## API Endpoints

- `GET /` - Render web interface
- `POST /analyze` - Upload & analyze prescription
  - **Request**: multipart/form-data with `file` field
  - **Response**: JSON with `image_data` & `analysis_html`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No file uploaded" | Ensure file field name is `file` |
| Tesseract not found | Run `sudo apt install tesseract-ocr` |
| Model not found | Ensure GGUF model file is in `models/` directory |
| PDF is blank | Ensure analysis HTML renders before downloading |
| No text detected | Use high-quality prescription images |

## Dependencies

```
Flask
pytesseract
Pillow
openai
```

## Medical Disclaimer

⚠️ **This tool is for informational purposes only.** AI-generated reports do not replace professional medical advice. Always consult a qualified healthcare provider for diagnosis and treatment decisions.

## License

MIT License - Feel free to modify and distribute.

## Author

Created for medical prescription analysis using AI.
