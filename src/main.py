from flask import Flask, render_template
from models.llm_handler import LLMHandler
from models.tts_handler import TTSHandler
from database.db_manager import DBManager
from utils.system_detector import SystemDetector

app = Flask(__name__)

# Initialize components
db_manager = DBManager()
llm_handler = LLMHandler()
tts_handler = TTSHandler()
system_detector = SystemDetector()

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)