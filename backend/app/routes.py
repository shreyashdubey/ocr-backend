from flask import Blueprint, request, jsonify, send_from_directory
import os
import uuid
from datetime import datetime
import sqlite3
from werkzeug.utils import secure_filename
import logging
from .ocr_service import ocr_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ocr_bp = Blueprint('ocr', __name__, url_prefix='/api')

# Database setup
def get_db():
    conn = sqlite3.connect('instance/ocr_database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS scans (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TEXT NOT NULL,
                image_path TEXT NOT NULL,
                user_id TEXT,
                is_premium BOOLEAN DEFAULT FALSE
            );
        """)

# Initialize database
init_db()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@ocr_bp.route('/scan', methods=['POST'])
def perform_scan():
    logger.info("Received scan request")
    
    # Check if it's a premium request
    use_premium = request.args.get('premium', 'false').lower() == 'true'
    
    if 'image' not in request.files:
        logger.error("No image file in request")
        return jsonify({"error": "No image provided"}), 400

    image_file = request.files['image']
    
    if not image_file or image_file.filename == '':
        logger.error("Empty file or no filename")
        return jsonify({"error": "No image file provided"}), 400

    if not allowed_file(image_file.filename):
        logger.error(f"Invalid file type: {image_file.filename}")
        return jsonify({"error": f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    try:
        # Generate unique ID and save the image
        image_id = str(uuid.uuid4())
        filename = secure_filename(f"{image_id}.jpg")
        image_path = os.path.join('uploads', filename)
        
        # Ensure uploads directory exists
        os.makedirs('uploads', exist_ok=True)
        
        # Save the uploaded file
        image_file.save(image_path)
        logger.info(f"Image saved to {image_path}")

        # Process with appropriate OCR service
        text, confidence = ocr_service.process_image(image_path, use_premium)
        logger.info(f"OCR completed with confidence: {confidence}")

        # Save to database
        with get_db() as conn:
            conn.execute(
                "INSERT INTO scans (id, text, confidence, created_at, image_path, is_premium) VALUES (?, ?, ?, ?, ?, ?)",
                (image_id, text, confidence, datetime.now().isoformat(), image_path, use_premium)
            )

        response_data = {
            "id": image_id,
            "text": text,
            "confidence": confidence,
            "createdAt": datetime.now().isoformat(),
            "imageUrl": f"/api/images/{filename}",
            "isPremium": use_premium
        }
        logger.info("Scan completed successfully")
        return jsonify(response_data)

    except Exception as e:
        logger.exception("Error processing image")
        return jsonify({"error": str(e)}), 500

@ocr_bp.route('/scans', methods=['GET'])
def get_scan_history():
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    sort_by = request.args.get('sortBy', 'created_at')
    sort_direction = request.args.get('sortDirection', 'desc')

    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) as count FROM scans").fetchone()['count']
        
        query = f"""
            SELECT * FROM scans 
            ORDER BY {sort_by} {sort_direction}
            LIMIT ? OFFSET ?
        """
        scans = conn.execute(query, (limit, offset)).fetchall()
        
        return jsonify({
            "scans": [{
                "id": scan['id'],
                "text": scan['text'],
                "confidence": scan['confidence'],
                "createdAt": scan['created_at'],
                "imageUrl": f"/api/images/{os.path.basename(scan['image_path'])}",
                "isPremium": bool(scan['is_premium'])
            } for scan in scans],
            "total": total
        })

@ocr_bp.route('/scans/<id>', methods=['GET'])
def get_scan_by_id(id):
    with get_db() as conn:
        scan = conn.execute("SELECT * FROM scans WHERE id = ?", (id,)).fetchone()
        
        if scan is None:
            return jsonify({"error": "Scan not found"}), 404
            
        return jsonify({
            "id": scan['id'],
            "text": scan['text'],
            "confidence": scan['confidence'],
            "createdAt": scan['created_at'],
            "imageUrl": f"/api/images/{os.path.basename(scan['image_path'])}",
            "isPremium": bool(scan['is_premium'])
        })

@ocr_bp.route('/scans/<id>', methods=['DELETE'])
def delete_scan(id):
    with get_db() as conn:
        scan = conn.execute("SELECT image_path FROM scans WHERE id = ?", (id,)).fetchone()
        
        if scan is None:
            return jsonify({"error": "Scan not found"}), 404
            
        # Delete the image file
        try:
            os.remove(scan['image_path'])
        except OSError:
            pass
            
        # Delete from database
        conn.execute("DELETE FROM scans WHERE id = ?", (id,))
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Scan deleted successfully"
        })

@ocr_bp.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory('uploads', filename) 