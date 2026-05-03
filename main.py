from flask import Flask, render_template, request, jsonify
import pytesseract
from PIL import Image, ImageOps, ImageEnhance
import re
from llama_cpp import Llama
import glob
import os
import base64
from io import BytesIO
import uuid
import threading

TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

app = Flask(__name__)

def find_model_path():
    model_dir = os.path.join(os.path.dirname(__file__), "models")
    patterns = ["*.gguf", "*.bin", "*.safetensors", "*.pt", "*.ckpt"]
    candidates = []
    for pattern in patterns:
        candidates.extend(glob.glob(os.path.join(model_dir, pattern)))
    if not candidates:
        raise RuntimeError("No model file found in the models/ folder. Place a .gguf or compatible file there.")
    return candidates[0]

def load_model():
    if TEST_MODE:
        print("TEST_MODE=true detected - skipping model load")
        return None

    model_path = find_model_path()
    print(f"Loading local Llama model from: {model_path}")
    return Llama(model_path=model_path, n_ctx=16384, n_threads=4)

llm = load_model()

# Global dictionary to track active requests and their cancellation status
active_requests = {}
requests_lock = threading.Lock()

def clean_ocr_text(text):
    """Clean and normalize OCR extracted text."""
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return "\n".join([line.strip() for line in text.split('\n') if len(line.strip()) > 3])


def dedupe_response(text):
    """Remove exact repeated blocks from the generated response."""
    if not text:
        return text
    cleaned = text.strip()
    for repeat_count in range(2, 5):
        if len(cleaned) % repeat_count != 0:
            continue
        part_len = len(cleaned) // repeat_count
        part = cleaned[:part_len]
        if part * repeat_count == cleaned:
            return part.strip()
    return text


def sanitize_response(text):
    """Clean noise from the model response and normalize punctuation."""
    if not text:
        return text

    text = text.strip()

    # Remove exact repeated consecutive lines
    lines = [line.rstrip() for line in text.splitlines()]
    normalized_lines = []
    previous_line = None
    for line in lines:
        if line == previous_line:
            continue
        normalized_lines.append(line)
        previous_line = line
    text = "\n".join(normalized_lines).strip()

    # Collapse repeated punctuation like ,,,,, or .....
    text = re.sub(r'([.,:;!?])\1{2,}', r'\1', text)
    text = re.sub(r'[-]{3,}', '-', text)
    text = re.sub(r'[`]{2,}', '', text)

    # Remove markdown/code fences and stray question marks/slashes
    text = re.sub(r'(^|\n)\s*```[\s\S]*?```', '', text)
    text = re.sub(r'(^|\n)\s*~~~[\s\S]*?~~~', '', text)

    # Remove stray leading/trailing punctuation and line noise
    text = re.sub(r'^[\s\.,;:!\-─–—`]+', '', text)
    text = re.sub(r'[\s\.,;:!\-─–—`]+$', '', text)

    # Strip extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text


def get_mock_analysis():
    return (
        "<h3>Medications</h3>"
        "<p>Mocked Clinical Analysis: this is a fixed test response.</p>"
        "<h3>Clinical Indications</h3>"
        "<p>Mocked Clinical Analysis provides a sample overview.</p>"
        "<h3>Patient Case</h3>"
        "<p>Example patient case description generated during TEST_MODE.</p>"
        "<footer>Mocked Clinical Analysis - test mode only.</footer>"
    )


def is_request_cancelled(request_id):
    """Check if a request has been cancelled."""
    with requests_lock:
        return active_requests.get(request_id, {}).get('cancelled', False)

def cancel_request(request_id):
    """Mark a request as cancelled."""
    with requests_lock:
        if request_id in active_requests:
            active_requests[request_id]['cancelled'] = True
            # Signal the thread to stop if it exists
            if 'thread' in active_requests[request_id]:
                active_requests[request_id]['thread'].should_stop = True
            return True
    return False

def run_ai_analysis(request_id, prompt):
    """Run AI analysis in a separate thread with cancellation support."""
    thread_data = active_requests.get(request_id, {})
    thread_data['thread'] = threading.current_thread()
    thread_data['thread'].should_stop = False
    
    try:
        print(f"Starting AI generation for request {request_id} in thread {threading.current_thread().name}")

        if TEST_MODE:
            print(f"TEST_MODE active - returning mock AI output for request {request_id}")
            return get_mock_analysis()
        
        # Check for cancellation before starting
        if is_request_cancelled(request_id) or getattr(threading.current_thread(), 'should_stop', False):
            print(f"Request {request_id} cancelled before AI call")
            return None
            
        response = llm.create_completion(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.1,
            top_p=0.95,
            repeat_penalty=1.1,
            echo=False,
            stop=["</s>"]
        )

        full_response = response['choices'][0]['text']
        full_response = dedupe_response(full_response)
        full_response = sanitize_response(full_response)
        print(f"AI generation completed for request {request_id}")
        return full_response
        
    except Exception as e:
        print(f"AI generation error for request {request_id}: {e}")
        raise e

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cancel/<request_id>', methods=['POST'])
def cancel_analysis(request_id):
    """Cancel an ongoing analysis request."""
    if cancel_request(request_id):
        return jsonify({"status": "cancelled"}), 200
    return jsonify({"status": "not_found"}), 404

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    
    # Register the request
    with requests_lock:
        active_requests[request_id] = {'cancelled': False}
    
    try:
        file = request.files['file']
        img = Image.open(file.stream)
        
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        if TEST_MODE:
            cleaned_text = "TEST PRESCRIPTION"
        else:
            ocr_img = ImageOps.grayscale(img)
            ocr_img = ImageEnhance.Contrast(ocr_img).enhance(2.5)
            raw_text = pytesseract.image_to_string(ocr_img)
            cleaned_text = clean_ocr_text(raw_text)

            if not cleaned_text:
                return jsonify({"error": "No text detected"}), 400

        # Check if cancelled before starting AI processing
        if is_request_cancelled(request_id):
            return jsonify({"error": "Request cancelled"}), 499

        prompt = (
            "<s>[INST] You are a Clinical Pharmacologist. Analyze this prescription only once. "
            "Respond in HTML only, with no Markdown, no code fences, and no backticks. "
            "Use only <h3>, <p>, <ul>, and <li> tags. "
            "Return exactly one section for each requested heading. "
            "Do not repeat or duplicate any part of the output. "
            "Do not include the original prescription text or any extra preamble. "
            "Begin directly with the first heading. "
            "1. List Medications in <h3>. "
            "2. Explain Clinical Indications in <h3>. "
            "3. Describe the overall Patient Case in <h3>. "
            "4. End with a <footer> for the medical disclaimer.\n\n"
            f"TEXT:\n{cleaned_text} [/INST]"
        )
        
        # Check cancellation again before AI call
        if is_request_cancelled(request_id):
            return jsonify({"error": "Request cancelled"}), 499
            
        # Run AI analysis in a separate thread for better cancellation control
        ai_thread = threading.Thread(target=lambda: None)  # Placeholder
        ai_result = [None]  # Use list to store result from thread
        ai_error = [None]
        
        def run_ai():
            try:
                ai_result[0] = run_ai_analysis(request_id, prompt)
            except Exception as e:
                ai_error[0] = e
        
        ai_thread = threading.Thread(target=run_ai, name=f"AI-{request_id[:8]}")
        ai_thread.start()
        
        # Store thread reference for cancellation
        with requests_lock:
            if request_id in active_requests:
                active_requests[request_id]['thread'] = ai_thread
        
        # Wait for completion with periodic cancellation checks
        while ai_thread.is_alive():
            ai_thread.join(timeout=0.1)  # Check every 100ms
            if is_request_cancelled(request_id):
                print(f"Request {request_id} cancelled while waiting for AI completion")
                return jsonify({"error": "Request cancelled"}), 499
        
        # Check if AI completed successfully
        if ai_error[0]:
            raise ai_error[0]
            
        ai_response = ai_result[0]
        if ai_response is None:  # Cancelled
            return jsonify({"error": "Request cancelled"}), 499
        
        # Final cancellation check
        if is_request_cancelled(request_id):
            print(f"Request {request_id} cancelled after AI completion")
            return jsonify({"error": "Request cancelled"}), 499
        
        return jsonify({
            "request_id": request_id,
            "image_data": img_str,
            "analysis_html": ai_response
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up the request
        with requests_lock:
            active_requests.pop(request_id, None)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=5000)
    # app.run(debug=True, port=5000)