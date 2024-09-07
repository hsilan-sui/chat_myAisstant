# 專案大綱

- 本專案以 ESP32 為開發版 透過麥克風模組錄製使用者的語音命令，透過 openai 提供的語音轉文字 文字轉語音功能協助使用者完成需求，並透過伺服器回傳查詢結果透過 ESP32 的喇叭實時的輸出語音內容
- 實作分階段：
  - IOT: ESP32 開發版 以及 按鈕 麥克風模組 DAC 與喇叭模組
  - 伺服器端： FLASK
  - 前端：我想透過前端來搭配顯示 ESP32 的輸出情況(待準備)
    - 接 LINE BOT?

## 專案初始化

```bash
$ mkdir chat_myAisstant # 建立專案資料夾
$ cd chat_myAisstant # 進入該專案資料夾
$ pip3 install Flask
$ git init . # 在本地數據庫-建立空儲存庫

$ mkdir web_server
$ python3 -m venv web\_server/
$ source web\_server/bin/activate
$ cd web_server
$ touch server.py # 撰寫首頁訪問的路由並給予簡易字串顯示在路由上
# 撰寫好首頁API端點內容，就訪問該路由
$ flask --app server run --debug
# http://127.0.0.1:5000 (本機連線的網址)
# http://192.168.100.11:5000(供同一個wifi裝置連線的網址)
```

- 先簡易的撰寫 server.py:

```python
from flask import Flask

app = Flask(__name__)

#根目錄
@app.route("/")
def index():
    return "WELCOME TO MY CHAT ASSISTANT !!!SUI"

if __name__ == '__main__':
    # 指定IP為0.0.0.0 ＝> 可以供給在同一個內部網域的ESP32連線
    app.run(host='0.0.0.0', port=5000)
```
