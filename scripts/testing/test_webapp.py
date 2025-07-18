#!/usr/bin/env python3
"""Minimal Flask app for testing chat functionality"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__, 
           template_folder='src/web/templates',
           static_folder='src/web/static')

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Mock LLM responses for testing
mock_responses = [
    "Hello! I'm Miku, your AI companion. How can I help you today?",
    "That's interesting! Tell me more about that.",
    "I understand. Is there anything specific you'd like to talk about?",
    "Great question! Let me think about that for a moment.",
    "I'm here to chat with you. What's on your mind?",
    "That sounds wonderful! I'd love to hear more details.",
    "I see what you mean. What do you think about it?",
    "Thanks for sharing that with me. How are you feeling about it?"
]

response_index = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    global response_index
    
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Use mock response for now
        response = mock_responses[response_index % len(mock_responses)]
        response_index += 1
        
        # Add some personality based on user input
        if 'hello' in user_message.lower() or 'hi' in user_message.lower():
            response = "Hello there! I'm Miku, and I'm so happy to meet you! How are you doing today?"
        elif 'how are you' in user_message.lower():
            response = "I'm doing wonderfully, thank you for asking! I'm excited to chat with you. How about you?"
        elif 'goodbye' in user_message.lower() or 'bye' in user_message.lower():
            response = "Goodbye for now! It was lovely talking with you. Take care!"
        
        return jsonify({
            'response': response,
            'user_message': user_message
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    print("Starting minimal AI companion web interface...")
    print("Visit http://localhost:5000 to test the chat functionality")
    app.run(host='0.0.0.0', port=5000, debug=True)
