from flask import Flask

app = Flask(__name__)

#根目錄
@app.route("/")
def hello():
    return "歡迎來到我的線上語音助理 ESP32開發區"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)