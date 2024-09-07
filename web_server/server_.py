from flask import Flask, request, jsonify
from flask_cors import CORS  # 引入 CORS 支持
import os

app = Flask(__name__)
CORS(app)  # 啟用 CORS


#設定文件上傳的目錄
    #(在與server.py同層目錄中檢查是否有uploads目錄夾 無就創建)
UPLOAD_FOLDER = './uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

    #根目錄
@app.route("/")
def hello():
    return "歡迎來到我的線上語音助理 ESP32開發區"

    #接收音頻端點   
@app.route("/upload_audio", methods=['POST'])
def upload_audio():
    if 'file' not in request.files:
        return jsonify({"message": "找不到音頻文件檔"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"message": "沒有選擇任何音頻文件檔"}), 400

    #保存音頻文件到上傳目錄
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    return jsonify({"message": "音頻文件檔案上傳成功！", "file_path": file_path}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)