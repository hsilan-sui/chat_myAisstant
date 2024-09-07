from flask import Flask, request, jsonify
from flask_cors import CORS  # 引入 CORS 支持
import os

app = Flask(__name__)
CORS(app)  # 啟用 CORS

# 設定文件上傳的目錄
UPLOAD_FOLDER = './uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 全局變量，用於存儲接收到的音頻塊
received_blocks = {}
expected_blocks = -1  # 用於追蹤應該接收到多少塊音頻
audio_file_path = os.path.join(UPLOAD_FOLDER, "combined_recording.wav")  # 最終合成的音頻文件

# 根目錄
@app.route("/")
def hello():
    return "歡迎來到我的線上語音助理 ESP32開發區"

# 接收音頻塊並組合
@app.route("/upload_audio", methods=['POST'])
def upload_audio():
    global expected_blocks, received_blocks

    # 獲取 JSON 請求體中的數據
    data = request.get_json()
    if not data or 'block' not in data or 'audio_data' not in data:
        return jsonify({"message": "找不到音頻數據或塊編號"}), 400

    block_number = data['block']  # 獲取音頻塊的編號
    audio_data = data['audio_data']  # 獲取音頻數據

    # 將接收到的音頻塊存儲
    received_blocks[block_number] = audio_data

    # 檢查是否接收到了所有塊
    if len(received_blocks) == expected_blocks:
        # 開始組合音頻文件
        with open(audio_file_path, 'wb') as f:
            for i in range(expected_blocks):
                if i in received_blocks:
                    # 將每個音頻塊寫入文件
                    f.write(received_blocks[i].encode('latin-1'))  # 將數據寫為二進制格式

        # 清空接收到的塊
        received_blocks.clear()
        expected_blocks = -1
        return jsonify({"message": "所有音頻塊已接收並組合成功", "file_path": audio_file_path}), 200
    else:
        return jsonify({"message": f"音頻塊 {block_number} 已接收"}), 200

# 設定音頻塊總數
@app.route("/set_total_blocks", methods=['POST'])
def set_total_blocks():
    global expected_blocks
    data = request.get_json()
    if not data or 'total_blocks' not in data:
        return jsonify({"message": "請提供音頻塊總數"}), 400

    expected_blocks = data['total_blocks']
    received_blocks.clear()  # 重置接收到的音頻塊
    return jsonify({"message": f"音頻塊總數已設置為 {expected_blocks}"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
