from flask import Flask, request, jsonify
from flask_cors import CORS  # 引入 CORS 支持
import wave
import os

app = Flask(__name__)
CORS(app)  # 啟用 CORS

# 音頻保存資料夾
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return "ESP32與chatgpt語音開發"

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    try:
        audio_data = request.data  # 接收來自 ESP32 的二進制音頻數據
        
        # 設置WAV文件的參數
        num_channels = 1  # 單聲道
        sample_width = 2  # 16位音頻（2字節）
        frame_rate = 16000  # 采樣率，與ESP32端設置保持一致
        
        # 保存為 WAV 文件
        file_path = os.path.join(UPLOAD_FOLDER, "record.wav")
        with wave.open(file_path, 'wb') as wav_file:
            wav_file.setnchannels(num_channels)  # 設置通道數
            wav_file.setsampwidth(sample_width)  # 設置樣本寬度（2字節，16位音頻）
            wav_file.setframerate(frame_rate)  # 設置采樣率
            wav_file.writeframes(audio_data)  # 寫入音頻數據
        
        return jsonify({"message": "音頻接收成功", "file": file_path}), 200
    
    except Exception as e:
        return jsonify({"message": f"音頻接收失敗: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
