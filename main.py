from flask import Flask, render_template, request, jsonify
import pytesseract
from PIL import Image, ImageOps, ImageEnhance
import re
from openai import OpenAI
import base64
from io import BytesIO
import uuid
import threading
import time

app = Flask(__name__)
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

# Global dictionary to track active requests and their cancellation status
active_requests = {}
requests_lock = threading.Lock()

def clean_ocr_text(text):
    """Clean and normalize OCR extracted text."""
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return "\n".join([line.strip() for line in text.split('\n') if len(line.strip()) > 3])

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
        
        # Check for cancellation before starting
        if is_request_cancelled(request_id) or getattr(threading.current_thread(), 'should_stop', False):
            print(f"Request {request_id} cancelled before AI call")
            return None
            
        response = client.chat.completions.create(
            model="qwen2.5-coder-3b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=True,
            timeout=30.0  # Shorter timeout for more responsive cancellation
        )
        
        full_response = ""
        chunk_count = 0
        
        for chunk in response:
            chunk_count += 1
            
            # Check for cancellation frequently
            if chunk_count % 3 == 0:  # Check every 3 chunks
                if is_request_cancelled(request_id) or getattr(threading.current_thread(), 'should_stop', False):
                    print(f"Request {request_id} cancelled during streaming at chunk {chunk_count}")
                    return None
            
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                
        print(f"AI generation completed for request {request_id}, total chunks: {chunk_count}")
        return full_response
        
    except Exception as e:
        if "cancelled" in str(e).lower() or "timeout" in str(e).lower():
            print(f"Request {request_id} cancelled due to: {e}")
            return None
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
            "<s>[INST] You are a Clinical Pharmacologist. Analyze this prescription. "
            "Use HTML tags (<h3>, <p>, <ul>, <li>) for your response. "
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
    # app.run(debug=True,host='0.0.0.0', port=5000)
    app.run(debug=True, port=5000)