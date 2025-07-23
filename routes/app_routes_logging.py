# Frontend Logging Routes - Handle console logs from browser
from flask import Blueprint, request, jsonify
import logging
import json
from datetime import datetime
import os

# Create blueprint for logging routes
logging_bp = Blueprint('logging', __name__)

# Create dedicated logger for frontend logs
frontend_logger = logging.getLogger('frontend')

# Get logs directory from config manager
try:
    from config.config_manager import get_logs_path
    logs_dir = str(get_logs_path())
except ImportError:
    # Fallback for development
    from config.config_manager import ConfigManager
    config_manager = ConfigManager()
    logs_dir = str(config_manager.get_logs_path())

# Ensure logs directory exists
os.makedirs(logs_dir, exist_ok=True)

# Create separate handler for frontend logs
from logging.handlers import RotatingFileHandler
frontend_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'frontend_console.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
frontend_handler.setLevel(logging.INFO)
frontend_handler.setFormatter(logging.Formatter(
    '%(asctime)s - FRONTEND - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
frontend_logger.addHandler(frontend_handler)
frontend_logger.setLevel(logging.INFO)

@logging_bp.route('/logs')
def log_viewer():
    """Log viewer interface"""
    from flask import render_template
    return render_template('logs.html')

@logging_bp.route('/api/logs/frontend', methods=['POST'])
def receive_frontend_logs():
    """Receive and process frontend console logs"""
    try:
        data = request.get_json()
        
        if not data or 'logs' not in data:
            return jsonify({'error': 'No logs provided'}), 400
        
        logs = data['logs']
        session_id = data.get('session_id', 'unknown')
        
        # Process each log entry
        for log_entry in logs:
            try:
                level = log_entry.get('level', 'info').upper()
                message = log_entry.get('message', '')
                timestamp = log_entry.get('timestamp', '')
                url = log_entry.get('url', '')
                
                # Format log message with context
                formatted_message = f"[{session_id}] [{url}] {message}"
                
                # Log based on level
                if level == 'ERROR':
                    frontend_logger.error(formatted_message)
                elif level == 'WARN':
                    frontend_logger.warning(formatted_message)
                elif level == 'DEBUG':
                    frontend_logger.debug(formatted_message)
                else:  # INFO, LOG
                    frontend_logger.info(formatted_message)
                    
            except Exception as e:
                frontend_logger.error(f"Error processing log entry: {e}")
        
        return jsonify({
            'success': True,
            'processed': len(logs),
            'message': f'Processed {len(logs)} log entries'
        })
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error in frontend logging endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@logging_bp.route('/api/logs/download/<log_type>', methods=['GET'])
def download_logs(log_type):
    """Download log files"""
    try:
        log_files = {
            'app': 'ai2d_chat.log',
            'chat': 'chat_activity.log',
            'frontend': 'frontend_console.log'
        }
        
        if log_type not in log_files:
            return jsonify({'error': 'Invalid log type'}), 400
        
        log_path = os.path.join(logs_dir, log_files[log_type])
        
        if not os.path.exists(log_path):
            return jsonify({'error': 'Log file not found'}), 404
        
        from flask import send_file
        return send_file(log_path, as_attachment=True, 
                        download_name=f"{log_type}_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error downloading logs: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@logging_bp.route('/api/logs/status', methods=['GET'])
def log_status():
    """Get logging system status"""
    try:
        status = {
            'logs_directory': logs_dir,
            'available_logs': [],
            'log_files': {}
        }
        
        # Check available log files
        log_files = ['ai2d_chat.log', 'chat_activity.log', 'frontend_console.log']
        
        for log_file in log_files:
            log_path = os.path.join(logs_dir, log_file)
            if os.path.exists(log_path):
                stat = os.stat(log_path)
                status['available_logs'].append(log_file)
                status['log_files'][log_file] = {
                    'size_bytes': stat.st_size,
                    'size_mb': round(stat.st_size / (1024*1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'readable': os.access(log_path, os.R_OK)
                }
        
        return jsonify(status)
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error getting log status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Helper function to log chat activities from other modules
def log_chat_activity(activity_type, data):
    """Helper function to log chat activities"""
    try:
        chat_logger = logging.getLogger('chat')
        message = f"{activity_type}: {json.dumps(data, default=str)}"
        chat_logger.info(message)
    except Exception as e:
        logging.getLogger(__name__).error(f"Error logging chat activity: {e}")
