import os
from flask import Flask, request, jsonify
from pydub import AudioSegment
from pydub.utils import which

app = Flask(__name__)

# 創建保存音頻的目錄
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 設定 PCM 和 MP3 文件的保存路徑
pcm_audio_file_path = os.path.join(UPLOAD_FOLDER, "audio.pcm")
mp3_audio_file_path = os.path.join(UPLOAD_FOLDER, "audio.mp3")

# 指定 ffmpeg 或 avconv 的路徑，這對於 pydub 在 Mac 上很重要
AudioSegment.converter = which("ffmpeg")  # 如果使用 libav，將 "ffmpeg" 改為 "avconv"
print(f"使用的音頻轉換工具路徑: {AudioSegment.converter}")  # 確認路徑

@app.route('/')
def index():
    return "ESP32 與 Flask 音頻接收伺服器 - PCM 到 MP3 格式"

# 接收音頻數據並保存為 .pcm 文件
@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    is_final_chunk = request.headers.get('IsFinalChunk') == 'true'
    audio_data = request.data  # 接收來自ESP32的音頻數據

    # 檢查接收的音頻數據大小
    print(f"接收到音頻段，大小: {len(audio_data)} 字節")
    with open(pcm_audio_file_path, 'ab') as pcm_file:  # 使用 'ab' 模式來追加數據
        pcm_file.write(audio_data)

    # 最後一段音頻上傳後，進行轉換
    if is_final_chunk:
        print("接收到最後一段數據，開始轉換為 MP3 文件...")
        convert_pcm_to_mp3(pcm_audio_file_path, mp3_audio_file_path)
        return jsonify({"message": "音頻接收完成，已轉換為 MP3 格式", "mp3_file": mp3_audio_file_path}), 200

    return "音頻段接收成功", 200

# 將 PCM 文件轉換為 MP3
def convert_pcm_to_mp3(pcm_file_path, mp3_file_path):
    try:
        # 檢查 PCM 文件大小
        file_size = os.path.getsize(pcm_file_path)
        print(f"PCM 文件大小: {file_size} 字節")

        # 使用 pydub 將 PCM 轉換為 MP3
        audio = AudioSegment.from_file(pcm_file_path, format="raw", frame_rate=16000, channels=1, sample_width=2)
        
        # 檢查音頻數據長度
        print(f"音頻長度: {len(audio)} 毫秒")

        # 將轉換結果保存為 MP3
        audio.export(mp3_file_path, format="mp3")
        print(f"音頻已成功轉換為 MP3 文件: {mp3_file_path}")
    except Exception as e:
        print(f"音頻轉換失敗: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
