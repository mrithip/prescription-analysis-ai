# MedScan AI - Clinical Prescription Intelligence

**MedScan AI** is a Flask-based web application that uses OCR and AI to analyze prescription images and provide clinical insights. It combines Tesseract OCR with LM Studio's local LLM for medication identification and clinical analysis.

## Features

- 📸 **Image Upload**: Drag-and-drop prescription image upload
- 🔍 **OCR Processing**: Tesseract-based text extraction with contrast enhancement
- 🤖 **AI Analysis**: Local LLM (LM Studio) for clinical pharmacology insights
- 📄 **PDF Export**: Generate professional clinical reports
- 🎨 **Modern UI**: Responsive Tailwind CSS interface

## Prerequisites

### System Dependencies
- **Tesseract OCR**: Required for image text extraction
  ```bash
  sudo apt update
  sudo apt install tesseract-ocr
  ```

- **LM Studio**: Running locally on `http://localhost:1234` with `qwen2.5-coder-3b-instruct` model
  - [Download LM Studio](https://lmstudio.ai)
  - Start the local server before running the app

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

1. **Start LM Studio** with the model running on port 1234

2. **Run the Flask app**:
   ```bash
   python main.py
   ```

3. **Access the web UI**:
   ```
   http://localhost:5000
   ```

4. **Upload prescription image** and click "Analyze"

5. **Download PDF report** with clinical insights

## Project Structure

```
medicalai/
├── main.py                 # Flask app & OCR/AI logic
├── templates/
│   └── index.html         # Web UI with PDF generation
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Configuration

Edit model name in `main.py`:
```python
model="qwen2.5-coder-3b-instruct"  # Change to your LM Studio model
```

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
| LM Studio connection error | Verify server running on `http://localhost:1234` |
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
