import os
import logging
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configuration
# Use SQLite for local development, PostgreSQL for production
use_sqlite = os.getenv('USE_SQLITE', 'true').lower() == 'true'
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME', 'flaskapp')
db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD', 'postgres')

if use_sqlite:
    # SQLite for local development (no setup required)
    database_url = 'sqlite:///flaskapp.db'
else:
    # PostgreSQL for production
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Simple model for demonstration
class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_agent = db.Column(db.String(200))

    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat(),
            'user_agent': self.user_agent
        }

@app.route('/')
def hello():
    logger.info("Root endpoint accessed")
    try:
        # Try to log visit to database
        visit = Visit(
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', 'Unknown')
        )
        db.session.add(visit)
        db.session.commit()
        visit_count = Visit.query.count()
        return jsonify({
            "message": "Hello from Flask running in Docker!",
            "visit_count": visit_count,
            "visit_id": visit.id
        })
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({
            "message": "Hello from Flask running in Docker!",
            "database": "unavailable",
            "error": str(e)
        }), 200

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return jsonify({
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }), 200 if db_status == "healthy" else 503

@app.route('/visits')
def visits():
    """Get all visits"""
    try:
        visits = Visit.query.order_by(Visit.timestamp.desc()).limit(10).all()
        return jsonify({
            "visits": [v.to_dict() for v in visits],
            "total": Visit.query.count()
        })
    except Exception as e:
        logger.error(f"Error fetching visits: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Initialize database tables
def init_db():
    """Initialize database tables"""
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
