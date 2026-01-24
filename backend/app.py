# Flask app for resume compatibility checker

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
import os

# Importing class from resume_matcher.py
from resume_matcher import ResumeJobMatcher

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
ALLOWED_EXTENSIONS = {'pdf'}


matcher = ResumeJobMatcher()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return jsonify({
        "message": "Resume Job Matcher API",
        "status": "running"
    })

"""
Take in formData and return JSON with alignment scores
"""
@app.route('/api/match', methods=['POST'])
def match_resume():
    # Check if file is in request
    if 'resume' not in request.files:
        return jsonify({
            "success": False,
            "error": "No resume file provided"
        }), 400
    
    file = request.files['resume']
    
    # Check if file is selected
    if file.filename == '':
        return jsonify({
            "success": False,
            "error": "No file selected"
        }), 400
    
    # Check if file is PDF
    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": "Only PDF files are supported"
        }), 400
    
    # Get job description
    job_description = request.form.get('job_description', '')
    if not job_description:
        return jsonify({
            "success": False,
            "error": "Job description is required"
        }), 400
    
    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            file.save(tmp_file.name)
            tmp_file_path = tmp_file.name
        
        # Extract text from PDF
        resume_text = matcher.extract_text_from_pdf(tmp_file_path)
        
        # Remove temporary file
        os.unlink(tmp_file_path)
        
        # Check if text extraction was successful
        if not resume_text or len(resume_text.strip()) < 50:
            return jsonify({
                "success": False,
                "error": "Could not extract enough text from PDF. Please ensure it's not an image-based PDF."
            }), 400
        
        # Calculate compatibility
        result = matcher.calculate_compatibility(resume_text, job_description)
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error processing resume: {str(e)}"
        }), 500

"""
Match resume text against a job description
"""
@app.route('/api/match-text', methods=['POST'])
def match_text():
    # Support both form data and JSON
    if request.is_json:
        data = request.get_json()
        resume_text = data.get('resume_text', '')
        job_description = data.get('job_description', '')
    else:
        resume_text = request.form.get('resume_text', '')
        job_description = request.form.get('job_description', '')
    
    if not resume_text or not job_description:
        return jsonify({
            "success": False,
            "error": "Both resume_text and job_description are required"
        }), 400
    
    try:
        result = matcher.calculate_compatibility(resume_text, job_description)
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error calculating compatibility: {str(e)}"
        }), 500

@app.route('/api/skills', methods=['GET'])
def get_supported_skills():
    return jsonify({
        "skills": matcher.common_skills,
        "total": len(matcher.common_skills)
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

"""
Error Handlers
"""
@app.errorhandler(413)
def too_large(e):
    return jsonify({
        "success": False,
        "error": "File is too large. Maximum size is 16MB."
    }), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)