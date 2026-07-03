"""
Resume Scorer - Resume Compatibility Matcher
Flask API for semantic resume-to-job matching
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
import os
import logging
from datetime import datetime

from resume_matcher import ResumeJobMatcher

app = Flask(__name__)
CORS(app)

# Configuration file size and extension
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf'}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize matcher
try:
    matcher = ResumeJobMatcher()
    logger.info("ResumeJobMatcher initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ResumeJobMatcher: {str(e)}")
    matcher = None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return jsonify({
        "message": "Resume Compatibility Matcher",
        "status": "running",
        "version": "2.0",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "POST /api/match": "Upload PDF resume + job description",
            "POST /api/match-text": "Compare raw text resume vs job description",
            "GET /api/skills": "Get list of supported skills",
            "GET /api/model-info": "Model and features info"
        }
    }), 200


@app.route('/api/match', methods=['POST'])
def match_resume(): 
    if not matcher:
        logger.error("Matcher not initialized")
        return jsonify({
            "success": False,
            "error": "Service unavailable - matcher not initialized"
        }), 503

    # Validate resume file
    if 'resume' not in request.files:
        return jsonify({
            "success": False,
            "error": "Resume PDF file is required"
        }), 400

    file = request.files['resume']

    if file.filename == '':
        return jsonify({
            "success": False,
            "error": "No file selected"
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": "Only PDF files are supported"
        }), 400

    # Validate job description
    job_description = request.form.get('job_description', '').strip()
    if not job_description:
        return jsonify({
            "success": False,
            "error": "Job description is required"
        }), 400

    if len(job_description) < 20:
        return jsonify({
            "success": False,
            "error": "Job description is too short (minimum 20 characters)"
        }), 400

    try:
        filename = secure_filename(file.filename)
        logger.info(f"Processing resume upload: {filename}")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            file.save(tmp_file.name)
            tmp_file_path = tmp_file.name

        # Extract text from PDF
        resume_text = matcher.extract_text_from_pdf(tmp_file_path)

        # Clean up temporary file
        os.unlink(tmp_file_path)

        # Validate extracted text
        if not resume_text or len(resume_text.strip()) < 50:
            logger.warning(f"Insufficient text extracted from {filename}")
            return jsonify({
                "success": False,
                "error": "Could not extract sufficient text from resume. Please ensure it's a text-based PDF (not a scanned image)."
            }), 400

        # Calculate compatibility
        logger.info(f"Calculating compatibility for {filename}")
        result = matcher.calculate_compatibility(
            resume_text=resume_text,
            job_description=job_description
        )

        logger.info(f"Compatibility calculation complete. Score: {result['overall_score']}%")

        return jsonify({
            "success": True,
            "filename": filename,
            "data": result
        }), 200

    except Exception as e:
        logger.exception(f"Error processing resume {filename}")
        return jsonify({
            "success": False,
            "error": f"Error processing resume: {str(e)}"
        }), 500


# Compare raw resume text against a job description.
@app.route('/api/match-text', methods=['POST'])
def match_text():
    if not matcher:
        logger.error("Matcher not initialized")
        return jsonify({
            "success": False,
            "error": "Service unavailable - matcher not initialized"
        }), 503

    # Parse input (JSON or form data)
    if request.is_json:
        data = request.get_json()
        resume_text = data.get('resume_text', '').strip()
        job_description = data.get('job_description', '').strip()
    else:
        resume_text = request.form.get('resume_text', '').strip()
        job_description = request.form.get('job_description', '').strip()

    # Validate inputs
    if not resume_text or not job_description:
        return jsonify({
            "success": False,
            "error": "Both resume_text and job_description are required"
        }), 400

    if len(resume_text) < 20 or len(job_description) < 20:
        return jsonify({
            "success": False,
            "error": "Resume and job description must be at least 20 characters each"
        }), 400

    try:
        logger.info("Calculating text-based compatibility")
        result = matcher.calculate_compatibility(
            resume_text=resume_text,
            job_description=job_description
        )

        logger.info(f"Text compatibility calculation complete. Score: {result['overall_score']}%")

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except Exception as e:
        logger.exception("Error calculating compatibility")
        return jsonify({
            "success": False,
            "error": f"Error calculating compatibility: {str(e)}"
        }), 500


# Get list of all supported technical skills
@app.route('/api/skills', methods=['GET'])
def get_supported_skills():
    if not matcher:
        return jsonify({
            "success": False,
            "error": "Service unavailable"
        }), 503

    return jsonify({
        "success": True,
        "skills": sorted(matcher.common_skills),
        "total": len(matcher.common_skills)
    }), 200


# Get information about the embedding model and features
@app.route('/api/model-info', methods=['GET'])
def model_info():
    return jsonify({
        "success": True,
        "embedding_model": "all-MiniLM-L6-v2 (Sentence Transformers)",
        "model_size": "22.7 MB",
        "features": [
            "semantic similarity matching",
            "section-aware scoring (skills, experience, projects, education)",
            "skill normalization and standardization",
            "explainable recommendations",
            "years of experience extraction",
            "weighted multi-factor analysis"
        ],
        "scoring_weights": matcher.final_weights if matcher else None,
        "section_weights": matcher.section_weights if matcher else None
    }), 200


# Error Handlers 
@app.errorhandler(413)
def too_large(e):
    return jsonify({
        "success": False,
        "error": "Very large file size. Please compress the file and try again."
    }), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "error": "The requested endpoint couldn't be found."
    }), 404

@app.errorhandler(500)
def internal_error(e):
    logger.exception("Internal server error")
    return jsonify({
        "success": False,
        "error": "Internal server error."
    }), 500


if __name__ == '__main__':
    logger.info("Starting Flask server...")
    app.run(host='0.0.0.0', port=8000, debug=False)