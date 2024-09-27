from flask import Flask, request
from flask_cors import CORS
import os
import uuid
from openai import OpenAI
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 启用 CORS

client = OpenAI()

# 指定上传目录
UPLOAD_DIR = "uploads"

# 确保上传目录存在
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@app.route('/')
def index():
    return "ESP32與ChatGPT語音開發"

# 接收逐块音频上传，并为每次上传创建一个新文件
@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    # 生成唯一的文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"recording_{timestamp}_{uuid.uuid4().hex}.wav"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    audio_data = request.data  # 接收来自 ESP32 的二进制音频数据

    if not audio_data:
        return "没有接收到音频数据", 400

    # 将收到的音频数据保存为新文件
    with open(file_path, 'wb') as audio_file:
        audio_file.write(audio_data)

    print(f"音频文件保存到: {file_path}, 大小: {len(audio_data)} 字节")

    # return f"音频已保存到 {file_path}", 200
    # 將音頻轉換為文字
    transcription = transcribe_audio(file_path)
    return f"音频已保存到 {file_path}, 語音轉文字結果: {transcription}", 200

def transcribe_audio(file_path):
    try:
        # 使用 OpenAI 的 Whisper 模型進行語音轉文字
        with open(file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        print(transcript.text)
        #return transcript['text']
    except Exception as e:
        print(f"語音轉文字失敗: {e}")
        return "語音轉文字失敗"


# 处理文件上传完成后可以调用这个接口来补充一些逻辑（可选）
@app.route('/complete_upload', methods=['POST'])
def complete_upload():
    # 你可以在这里处理文件上传完成后的逻辑
    # 比如，如果想要处理一些额外操作，可以在这里补充
    return "文件上传已完成", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
