from flask import Flask, render_template, request, jsonify
import pytesseract
from PIL import Image, ImageOps, ImageEnhance
import re
from openai import OpenAI
import base64
from io import BytesIO

app = Flask(__name__)
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

def clean_ocr_text(text):
    """Clean and normalize OCR extracted text."""
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return "\n".join([line.strip() for line in text.split('\n') if len(line.strip()) > 3])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    img = Image.open(file.stream)
    
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    ocr_img = ImageOps.grayscale(img)
    ocr_img = ImageEnhance.Contrast(ocr_img).enhance(2.5)
    raw_text = pytesseract.image_to_string(ocr_img)
    cleaned_text = clean_ocr_text(raw_text)

    if not cleaned_text:
        return jsonify({"error": "No text detected"}), 400

    try:
        prompt = (
            "<s>[INST] You are a Clinical Pharmacologist. Analyze this prescription. "
            "Use HTML tags (<h3>, <p>, <ul>, <li>) for your response. "
            "1. List Medications in <h3>. "
            "2. Explain Clinical Indications in <h3>. "
            "3. Describe the overall Patient Case in <h3>. "
            "4. End with a <footer> for the medical disclaimer.\n\n"
            f"TEXT:\n{cleaned_text} [/INST]"
        )
        
        response = client.chat.completions.create(
            model="qwen2.5-coder-3b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        return jsonify({
            "image_data": img_str,
            "analysis_html": response.choices[0].message.content
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)