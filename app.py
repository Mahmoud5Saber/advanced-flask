from flask import Flask, render_template, jsonify, request
import logging
import os
import psutil  # To fetch system performance metrics
from flask_session import Session
import re
from cachelib.file import FileSystemCache

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "M@s1471236m@S")  # Replace with a strong key
app.config["SESSION_TYPE"] = "cachelib"
app.config["SESSION_CACHELIB"] = FileSystemCache("./flask_session")  #  New format
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_KEY_PREFIX"] = "session:"

# Initialize session
Session(app)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Home page route
@app.route("/")
def home():
    return render_template("index.html")

# Performance page route
@app.route("/performance")
def performance():
    return render_template("performance.html")

# API for real-time performance data
@app.route("/performance-data")
def performance_data():
    try:
        cpu_usage = psutil.cpu_percent(interval=2)  
        memory_info = psutil.virtual_memory()
        disk_usage = psutil.disk_usage('/')

        metrics = {
            "cpu_usage": f"{cpu_usage:.2f}%",  
            "memory_usage": f"{memory_info.percent:.2f}%",
            "disk_usage": f"{disk_usage.percent:.2f}%"
        }
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error fetching performance metrics: {e}")
        return jsonify({"error": "Unable to retrieve performance metrics"}), 500

# API test endpoint
@app.route("/api", methods=["POST"])
def api():
    data = request.get_json()
  
    if not data or "input" not in data:
        return jsonify({"error": "Invalid input"}), 400

    # Simple validation to block HTML/JS tags
    if re.search(r"<[^>]*>", data["input"]):
        return jsonify({"error": "Invalid characters detected"}), 400

    return jsonify({"message": "Input received", "status": "success"}), 200

# Health check endpoint
@app.route("/health",methods=["GET"])
def health_check():
    return render_template("health.html")

# 404 Error handler
@app.errorhandler(404)
def page_not_found(error):
    logger.warning(f"Page not found: {request.url}")
    return render_template("404.html"), 404

# General error handler
@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"Unhandled error: {error}")
    error_message = str(error) if app.debug else "Internal server error"  # Corrected usage
    return render_template("error.html", error=error_message), 500

# Run the app locally at port 5050 with debug mode enabled
debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
if __name__ == '__main__': 
    app.run(host='0.0.0.0', port=5050, debug=debug_mode,threaded=True)
