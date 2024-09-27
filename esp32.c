#include <WiFi.h>
#include <HTTPClient.h>
#include "Arduino.h"
#include <driver/i2s.h>
#include <SPI.h>
#include <SD.h>

const char* ssid = "";
const char* password = "";
const char* serverUrl = "http://192.168.0.17:5001/upload_audio";  // Flask server URL

#define BUTTON_PIN 22
#define INMP441_LRCL 21
#define INMP441_BCLK 18
#define INMP441_DOUT 19

#define SAMPLE_RATE 16000

// SD card pins
#define SD_CS_PIN 5  // CS pin is GPIO 5
#define SD_SCK_PIN 14 // SCK pin is GPIO 14
#define SD_MOSI_PIN 13 // MOSI pin is GPIO 13
#define SD_MISO_PIN 23 // MISO pin is GPIO 23

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
    .data_out_num = -1,
    .data_in_num = INMP441_DOUT
};

bool isRecording = false;
File audioFile;
size_t audioIndex = 0;
int recordDuration = 10; // 錄製10秒

SPIClass spi = SPIClass(VSPI);

void setup() {
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    Serial.begin(115200);

    // 連接 WiFi
    connectToWiFi();

    // 初始化 SD 卡
    spi.begin(14, 23, 13, SD_CS_PIN);  // SCK, MISO, MOSI, CS
    if (!SD.begin(SD_CS_PIN, spi, 1000000)) {
        Serial.println("SD 卡初始化失敗");
        while (true);
    } else {
        Serial.println("SD 卡初始化成功");
    }

    // 安裝 I2S 驅動
    esp_err_t i2s_status = i2s_driver_install(I2S_NUM_0, &i2sIn_config, 0, NULL);
    if (i2s_status != ESP_OK) {
        Serial.println("I2S 驅動安裝失敗");
        while (true);
    }
    i2s_set_pin(I2S_NUM_0, &i2sInPins);
}

void loop() {
    static bool lastButtonState = HIGH;

    bool buttonState = digitalRead(BUTTON_PIN);

    // 按下按鈕開始錄音，按鈕放開或達到時長停止錄音
    if (buttonState == LOW && lastButtonState == HIGH && !isRecording) {
        startRecording();
    } else if (isRecording && (millis() - audioIndex >= recordDuration * 1000 || buttonState == HIGH)) {
        stopRecording();
    }

    lastButtonState = buttonState;

    if (isRecording) {
        recordAudio();
    }
}

void startRecording() {
    Serial.println("開始錄音...");
    isRecording = true;
    audioIndex = millis();  // 記錄開始時間

    // 打開 WAV 文件
    audioFile = SD.open("/recording.wav", FILE_WRITE);
    if (!audioFile) {
        Serial.println("無法打開文件寫入");
        isRecording = false;
        return;
    }

    // 寫入 WAV 文件頭
    writeWavHeader(audioFile, SAMPLE_RATE, 16, 1, 0);
}


void recordAudio() {
    size_t bytesRead;
    int16_t data[256];
    esp_err_t readStatus = i2s_read(I2S_NUM_0, &data, sizeof(data), &bytesRead, portMAX_DELAY);

    if (readStatus == ESP_OK && bytesRead > 0) {
    audioFile.write((byte*)data, bytesRead);  // 將數據寫入文件
    } else {
        Serial.println("I2S 讀取失敗或無數據");
    }
}

void stopRecording() {
    Serial.println("停止錄音");

    // 獲取寫入的文件大小
    uint32_t dataSize = audioFile.size() - 44;  // 減去 WAV 頭的44字節

    // 更新 WAV 文件頭中的數據大小
    writeWavHeader(audioFile, SAMPLE_RATE, 16, 1, dataSize);

    audioFile.close();
    isRecording = false;

    // 上傳錄音文件到伺服器
    uploadAudioFile("/recording.wav");
}


void writeWavHeader(File& file, uint32_t sampleRate, uint16_t bitsPerSample, uint16_t channels, uint32_t dataSize) {
    file.seek(0);
    file.write((const uint8_t*)"RIFF", 4);
    uint32_t fileSize = 36 + dataSize;
    file.write((const uint8_t*)&fileSize, 4);
    file.write((const uint8_t*)"WAVE", 4);
    file.write((const uint8_t*)"fmt ", 4);
    uint32_t fmtChunkSize = 16;
    file.write((const uint8_t*)&fmtChunkSize, 4);
    uint16_t audioFormat = 1;
    file.write((const uint8_t*)&audioFormat, 2);
    file.write((const uint8_t*)&channels, 2);
    file.write((const uint8_t*)&sampleRate, 4);
    uint32_t byteRate = sampleRate * channels * (bitsPerSample / 8);
    file.write((const uint8_t*)&byteRate, 4);
    uint16_t blockAlign = channels * (bitsPerSample / 8);
    file.write((const uint8_t*)&blockAlign, 2);
    file.write((const uint8_t*)&bitsPerSample, 2);
    file.write((const uint8_t*)"data", 4);
    file.write((const uint8_t*)&dataSize, 4);
}


void uploadAudioFile(const char* filename) {
    if (WiFi.status() != WL_CONNECTED) {
        connectToWiFi();
    }

    File audioFile = SD.open(filename, FILE_READ);
    if (!audioFile) {
        Serial.println("無法打開文件上傳");
        return;
    }

    size_t fileSize = audioFile.size();
    if (fileSize == 0) {
        Serial.println("文件大小為零");
        audioFile.close();
        return;
    }

    // 先嘗試分配緩衝區進行一次性上傳
    uint8_t* buffer = (uint8_t*)malloc(fileSize);
    if (buffer) {
        // 成功分配緩衝區
        Serial.println("成功分配緩衝區，嘗試一次性上傳");

        // 讀取整個文件並上傳
        audioFile.read(buffer, fileSize);
        audioFile.close();

        HTTPClient http;
        http.begin(serverUrl);
        http.addHeader("Content-Type", "audio/wav");

        int httpResponseCode = http.POST(buffer, fileSize);
        free(buffer);

        if (httpResponseCode > 0) {
            String response = http.getString();
            Serial.println(httpResponseCode);
            Serial.println(response);
        } else {
            Serial.println("一次性上傳失敗，錯誤代碼：" + String(httpResponseCode));
        }

        http.end();
    } else {
        // 無法分配足夠內存，逐塊上傳
        Serial.println("無法分配緩衝區，逐塊上傳");

        HTTPClient http;
        uint8_t smallBuffer[1024];  // 定義較小的緩衝區
        int httpResponseCode;

        while (audioFile.available()) {
            size_t bytesRead = audioFile.read(smallBuffer, sizeof(smallBuffer));  // 逐塊讀取文件
            http.begin(serverUrl);
            http.addHeader("Content-Type", "audio/wav");
            httpResponseCode = http.POST(smallBuffer, bytesRead);  // 上傳該塊數據
            http.end();  // 每次POST完畢後結束HTTP連接

            if (httpResponseCode <= 0) {
                Serial.println("POST 發送失敗，錯誤代碼：" + String(httpResponseCode));
                break;
            }
        }

        if (httpResponseCode > 0) {
            String response = http.getString();
            Serial.println(httpResponseCode);
            Serial.println(response);
        } else {
            Serial.println("逐塊上傳失敗，錯誤代碼：" + String(httpResponseCode));
        }
    }

    audioFile.close();
}

void connectToWiFi() {
    WiFi.begin(ssid, password);
    Serial.println("正在連接 WiFi...");
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println(".");
    }
    Serial.println("WiFi 已連接");
    // 顯示本地 IP 位址
    Serial.print("本地 IP 地址: ");
    Serial.println(WiFi.localIP());
}