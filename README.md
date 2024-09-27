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

$ python3 server.py
 #* Running on http://127.0.0.1:5001(本機連線的網址)
 #* Running on http://192.168.0.17:5001(供同一個wifi裝置連線的網址)
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
    app.run(host='0.0.0.0',debug=True, port=5000)
```

## 從 esp32 錄音 成功上傳到 flask

```c
#include <WiFi.h>
#include <HTTPClient.h>
#include "Arduino.h"
#include <driver/i2s.h>

const char* ssid = "";
const char* password = "";
const char* serverUrl = "http://192.168.0.17:5001/upload_audio";  // Flask伺服器的URL

#define BUTTON_PIN 23  // 定義按鈕引腳
#define INMP441_LRCL 21  // 將 Word Select 對應到 GPIO 21/I2S_WS
#define INMP441_BCLK 18  // 將 Bit Clock 對應到 GPIO 18/I2S_SD
#define INMP441_DOUT 19  // 將 Data Out 對應到 GPIO 19/I2S_SCK
#define SAMPLE_RATE 16000  // 設置采樣率

i2s_config_t i2sIn_config = {
    .mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = i2s_bits_per_sample_t(16),
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S_MSB,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = 512
};

i2s_pin_config_t i2sInPins = {
    .bck_io_num = INMP441_BCLK,
    .ws_io_num = INMP441_LRCL,
    .data_out_num = -1,  // 不使用輸出
    .data_in_num = INMP441_DOUT
};

bool isRecording = false;  // 紀錄是否正在錄音
int16_t audioBuffer[16000];  // 緩存音頻數據 (錄製1秒鐘)
size_t audioIndex = 0;  // 當前錄製的音頻數據索引

void setup() {
    pinMode(BUTTON_PIN, INPUT_PULLUP);  // 設置按鈕為輸入模式

    Serial.begin(115200);

    // 設置 WiFi 連接
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("正在連接 WiFi...");
    }
    Serial.println("WiFi 已連接");

    // 安裝 I2S 驅動並設置引腳
    i2s_driver_install(I2S_NUM_0, &i2sIn_config, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &i2sInPins);
}

void loop() {
    if (digitalRead(BUTTON_PIN) == LOW) {  // 按下按鈕時開始錄音
        if (!isRecording) {
            Serial.println("開始錄音...");
            isRecording = true;
            audioIndex = 0;
        }

        // 繼續錄製音頻數據，直到音頻緩衝區已滿
        size_t bytes_read;
        int16_t data[256];  // 臨時緩衝讀取的音頻資料
        esp_err_t read_status = i2s_read(I2S_NUM_0, &data, sizeof(data), &bytes_read, portMAX_DELAY);

        if (read_status == ESP_OK && audioIndex < 16000) {
            memcpy(audioBuffer + audioIndex, data, bytes_read);
            audioIndex += bytes_read / 2;  // 每個樣本是16位（2字節）
        }
    } else if (isRecording) {  // 鬆開按鈕時停止錄音並上傳
        Serial.println("停止錄音並上傳...");
        isRecording = false;

        // 將音頻數據上傳到 Flask 伺服器
        sendAudioToServer(audioBuffer, audioIndex * 2);  // audioIndex 為樣本數，乘以2為字節數
    }
}

void sendAudioToServer(int16_t* audioData, size_t length) {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(serverUrl);  // 指定HTTP POST的目標URL

        // 將音頻數據轉換為字節數組
        uint8_t* byteData = (uint8_t*)audioData;

        http.addHeader("Content-Type", "application/octet-stream");  // 發送原始二進制數據
        int httpResponseCode = http.POST(byteData, length);  // 發送POST請求

        if (httpResponseCode > 0) {
            String response = http.getString();  // 獲取伺服器的回應
            Serial.println(httpResponseCode);
            Serial.println(response);
        } else {
            Serial.println("POST 發送失敗: ");
            Serial.println(httpResponseCode);
        }

        http.end();  // 釋放資源
    } else {
        Serial.println("WiFi 未連接");
    }
}

```
