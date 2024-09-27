from flask import Flask, request
from flask_cors import CORS
import os
import uuid
from openai import OpenAI  # 使用 openai 庫，而非 OpenAI
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 启用 CORS

client = OpenAI()

# 指定上传目录
UPLOAD_DIR = "uploads"

# 确保上传目录存在
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# 用于存储会话信息
file_sessions = {}

@app.route('/')
def index():
    return "ESP32與ChatGPT語音開發"

# 接收逐块音频上传，并将块合并到一个文件中
@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    session_id = request.headers.get('X-Session-ID')  # 用于标识同一次录音的唯一ID
    is_first_chunk = request.headers.get('X-First-Chunk', 'false')  # 是否为第一块

    if not session_id:
        return "没有提供会话ID", 400

    if session_id not in file_sessions:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"recording_{timestamp}_{uuid.uuid4().hex}.wav"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        file_sessions[session_id] = file_path

    file_path = file_sessions[session_id]

    audio_data = request.data  # 接收来自 ESP32 的二进制音频数据

    if not audio_data:
        return "没有接收到音频数据", 400

    # 如果是第一块，则新建文件，否则追加
    mode = 'wb' if is_first_chunk == 'true' else 'ab'

    with open(file_path, mode) as audio_file:
        audio_file.write(audio_data)

    print(f"音频数据追加到: {file_path}, 大小: {len(audio_data)} 字节")

    return f"音频已追加到 {file_path}", 200

# 处理文件上传完成
@app.route('/complete_upload', methods=['POST'])
def complete_upload():
    session_id = request.headers.get('X-Session-ID')

    if session_id not in file_sessions:
        return "文件上传会话不存在", 400

    file_path = file_sessions[session_id]

    # 在这里可以处理文件，比如将其发送到 OpenAI 的 Whisper 模型进行转录
    transcription = transcribe_audio(file_path)
    
    # 完成后删除 session 记录
    del file_sessions[session_id]

    return f"文件上传已完成, 語音轉文字結果: {transcription}", 200

def transcribe_audio(file_path):
    try:
        # 使用 OpenAI 的 Whisper 模型進行語音轉文字
        with open(file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        print(transcript.text)
        return transcript['text']
    except Exception as e:
        print(f"語音轉文字失敗: {e}")
        return "語音轉文字失敗"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
