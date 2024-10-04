from flask import Flask, request, jsonify, send_file
import requests
from flask_cors import CORS
import os
import subprocess
from openai import OpenAI
from gtts import gTTS
from langdetect import detect
import paho.mqtt.client as mqtt

app = Flask(__name__)
CORS(app)

client = OpenAI()

# MQTT broker details
mqtt_broker = "broker.mqttgo.io"
mqtt_port = 1883
mqtt_topic = "sui/audio/new"

# 增加 MQTT 发布回调函数
def on_publish(client, userdata, mid):
    print("MQTT 消息已成功發佈，ID:", mid)

mqtt_client = mqtt.Client()
mqtt_client.on_publish = on_publish  # 设置发布回调函数
mqtt_client.connect(mqtt_broker, mqtt_port, 60)

# 指定上传目录
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# 每次都覆蓋相同名稱的文件
WAV_FILE = os.path.join(UPLOAD_DIR, "recording.wav")
TTS_FILE = os.path.join(UPLOAD_DIR, "output.wav")  # 固定 TTS 文件名稱

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    # 接收 ESP32 上傳的音頻並保存為 recording.wav
    file_path = WAV_FILE
    audio_data = request.data
    if not audio_data:
        return "没有接收到ESP32上傳的音檔資料", 400

    # 保存錄音數據
    with open(file_path, 'wb') as audio_file:
        audio_file.write(audio_data)

    # 將錄音轉為文字並查詢答案
    transcription = transcribe_audio(file_path)
    if transcription:
        answer = query_openai(transcription)
        if answer:
            tts_file = text_to_speech_to_wav(answer)
        else:
            tts_file = os.path.join(UPLOAD_DIR, "noanswer.wav")  # 使用固定的音檔
    else:
        tts_file = os.path.join(UPLOAD_DIR, "noanswer.wav")  # 使用固定的音檔

    # 確保音檔存在，通知 ESP32 播放
    if tts_file and os.path.exists(tts_file):
        # 在发布消息前检查 MQTT 连接状态
        if not mqtt_client.is_connected():
            mqtt_client.reconnect()

        result = mqtt_client.publish(mqtt_topic, "play")  # 通知 ESP32 播放音頻
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print("MQTT 消息成功發佈")
        else:
            print("MQTT 消息發佈失敗，代碼:", result.rc)
        return jsonify({"message": "音頻處理成功", "tts_file": tts_file})
    else:
        return "TTS 或播放音檔失敗", 500


def transcribe_audio(audio_file):
    try:
        with open(audio_file, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        print(f"STT音檔轉換失敗: {e}")
        return None

def query_openai(question):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # 或 "gpt-4" 視情況而定
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question}
            ],
            max_tokens=300
        )
        print(response.choices[0].message.content)
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI 查詢失敗: {e}")
        return "無法回答此問題"

# def text_to_speech_to_wav(text):
#     try:
#         # 自动检测文本的语言
#         detected_language = detect(text)
#         print(f"检测到的语言: {detected_language}")
        
#         # 创建 TTS 对象，使用自动检测到的语言
#         tts = gTTS(text, lang=detected_language)
#         mp3_file = os.path.join(UPLOAD_DIR, "output.mp3")
#         tts.save(mp3_file)

#         ffmpeg_command = [
#             "ffmpeg", "-y", "-i", mp3_file, "-ar", "20000", "-ac", "1", "-b:a", "128k", TTS_FILE
#         ]
#         subprocess.run(ffmpeg_command, check=True)

#         return TTS_FILE
#     except subprocess.CalledProcessError as e:
#         print(f"FFmpeg 轉換失敗: {e}")
#         return None
#     except Exception as e:
#         print(f"TTS 失敗: {e}")
#         return None    
def text_to_speech_to_wav(text):
    try:
        tts = gTTS(text, lang='zh-TW')
        mp3_file = os.path.join(UPLOAD_DIR, "output.mp3")
        tts.save(mp3_file)

        ffmpeg_command = [
            "ffmpeg", "-y", "-i", mp3_file, "-ar", "20000", "-ac", "1", "-b:a", "128k", TTS_FILE
        ]
        subprocess.run(ffmpeg_command, check=True)

        return TTS_FILE
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg 轉換失敗: {e}")
        return None
    except Exception as e:
        print(f"TTS 失敗: {e}")
        return None

@app.route('/wav_audio', methods=['GET'])
def stream_wav():
    if os.path.exists(TTS_FILE):
        return send_file(TTS_FILE, mimetype='audio/wav')
    else:
        return "WAV 文件不存在", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
