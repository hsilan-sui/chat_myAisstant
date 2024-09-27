from flask import Flask, request
from flask_cors import CORS
import os
import wave

app = Flask(__name__)
CORS(app)  # 启用 CORS

# 指定上传目录
UPLOAD_DIR = "uploads"
file_name = "recording.wav"
file_path = os.path.join(UPLOAD_DIR, file_name)

# 确保上传目录存在
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# 全局变量，用于标记是否是第一次上传
is_first_chunk = True

@app.route('/')
def index():
    return "ESP32與ChatGPT語音開發"

# 接收逐块音频上传
@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    global is_first_chunk
    audio_data = request.data  # 接收来自 ESP32 的二进制音频数据

    if not audio_data:
        return "没有接收到音频数据", 400

    # 如果是第一次上传，删除之前的音频文件并创建一个新的文件
    if is_first_chunk:
        if os.path.exists(file_path):
            os.remove(file_path)  # 删除旧的录音文件
        with open(file_path, 'wb') as audio_file:
            # 第一次上传时，不做数据写入，只是创建新文件
            pass
        is_first_chunk = False  # 标记为不是第一次上传

    # 将收到的音频数据追加到文件中
    with open(file_path, 'ab') as audio_file:
        audio_file.write(audio_data)

    print(f"音频数据追加到: {file_path}, 大小: {len(audio_data)} 字节")

    return f"音频块已接收并追加到 {file_path}", 200

# 处理文件上传完成并添加 WAV 文件头
@app.route('/complete_upload', methods=['POST'])
def complete_upload():
    global is_first_chunk
    is_first_chunk = True  # 重置为下一次录音做准备

    try:
        if not os.path.exists(file_path):
            return "音频文件不存在", 400

        with open(file_path, 'r+b') as f:
            # 确定文件大小
            file_size = os.path.getsize(file_path)
            print(f"文件大小为: {file_size} 字节")

            # 设置WAV文件的参数
            num_channels = 1  # 单声道
            sample_width = 2  # 16位音频（2字节）
            frame_rate = 16000  # 采样率，16kHz
            num_frames = (file_size - 44) // (num_channels * sample_width)  # 减去WAV头大小

            # 回到文件头位置
            f.seek(0)

            # 写入RIFF头
            f.write(b'RIFF')
            f.write((file_size - 8).to_bytes(4, 'little'))  # 文件大小减去RIFF和WAVE标识的8字节
            f.write(b'WAVE')

            # fmt子块
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))  # fmt子块大小
            f.write((1).to_bytes(2, 'little'))  # 音频格式（1表示PCM）
            f.write(num_channels.to_bytes(2, 'little'))  # 声道数
            f.write(frame_rate.to_bytes(4, 'little'))  # 采样率
            byte_rate = frame_rate * num_channels * sample_width
            f.write(byte_rate.to_bytes(4, 'little'))  # 字节率
            block_align = num_channels * sample_width
            f.write(block_align.to_bytes(2, 'little'))  # 块对齐
            f.write(sample_width.to_bytes(2, 'little'))  # 每个采样的位数

            # data子块
            f.write(b'data')
            f.write((file_size - 44).to_bytes(4, 'little'))  # 数据部分的大小

        return "WAV 文件头已添加", 200
    except Exception as e:
        print(f"添加WAV文件头时出错: {e}")
        return "无法完成上传", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

# from flask import Flask, request
# from flask_cors import CORS
# import os
# import wave

# app = Flask(__name__)
# CORS(app)  # 启用 CORS

# # 指定上传目录
# UPLOAD_DIR = "uploads"

# # 确保上传目录存在
# if not os.path.exists(UPLOAD_DIR):
#     os.makedirs(UPLOAD_DIR)

# # 使用全局变量保存文件路径
# file_path = os.path.join(UPLOAD_DIR, "recording.wav")

# @app.route('/')
# def index():
#     return "ESP32與ChatGPT語音開發"

# @app.route('/upload_audio', methods=['POST'])
# def upload_audio():
#     audio_data = request.data  # 接收来自 ESP32 的二进制音频数据

#     if not audio_data:
#         return "没有接收到音频数据", 400

#     # 将收到的音频数据追加到文件中
#     with open(file_path, 'ab') as audio_file:
#         audio_file.write(audio_data)

#     print(f"音频数据保存到: {file_path}, 大小: {len(audio_data)} 字节")

#     return f"音频块已接收并保存到 {file_path}", 200

# # 处理文件上传完成并添加 WAV 文件头
# @app.route('/complete_upload', methods=['POST'])
# def complete_upload():
#     try:
#         with open(file_path, 'r+b') as f:
#             # 确定文件大小
#             file_size = os.path.getsize(file_path)
#             print(f"文件大小为: {file_size} 字节")

#             # 设置WAV文件的参数
#             num_channels = 1  # 单声道
#             sample_width = 2  # 16位音频（2字节）
#             frame_rate = 16000  # 采样率，16kHz
#             num_frames = (file_size - 44) // (num_channels * sample_width)  # 减去WAV头大小

#             # 回到文件头位置
#             f.seek(0)

#             # 写入RIFF头
#             f.write(b'RIFF')
#             f.write((file_size - 8).to_bytes(4, 'little'))  # 文件大小减去RIFF和WAVE标识的8字节
#             f.write(b'WAVE')

#             # fmt子块
#             f.write(b'fmt ')
#             f.write((16).to_bytes(4, 'little'))  # fmt子块大小
#             f.write((1).to_bytes(2, 'little'))  # 音频格式（1表示PCM）
#             f.write(num_channels.to_bytes(2, 'little'))  # 声道数
#             f.write(frame_rate.to_bytes(4, 'little'))  # 采样率
#             byte_rate = frame_rate * num_channels * sample_width
#             f.write(byte_rate.to_bytes(4, 'little'))  # 字节率
#             block_align = num_channels * sample_width
#             f.write(block_align.to_bytes(2, 'little'))  # 块对齐
#             f.write(sample_width.to_bytes(2, 'little'))  # 每个采样的位数

#             # data子块
#             f.write(b'data')
#             f.write((file_size - 44).to_bytes(4, 'little'))  # 数据部分的大小

#         return "WAV 文件头已添加", 200
#     except Exception as e:
#         print(f"添加WAV文件头时出错: {e}")
#         return "无法完成上传", 500

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5001, debug=True)

# from flask import Flask, request
# from flask_cors import CORS
# import os

# app = Flask(__name__)
# CORS(app)  # 启用 CORS

# # 指定上传目录
# UPLOAD_DIR = "uploads"

# # 确保上传目录存在
# if not os.path.exists(UPLOAD_DIR):
#     os.makedirs(UPLOAD_DIR)

# # 使用全局变量保存文件路径
# file_path = os.path.join(UPLOAD_DIR, "recording.wav")

# @app.route('/')
# def index():
#     return "ESP32與ChatGPT語音開發"

# @app.route('/upload_audio', methods=['POST'])
# def upload_audio():
#     audio_data = request.data  # 接收来自 ESP32 的二进制音频数据

#     if not audio_data:
#         return "没有接收到音频数据", 400

#     # 将收到的音频数据追加到文件中
#     with open(file_path, 'ab') as audio_file:
#         audio_file.write(audio_data)

#     print(f"音频数据保存到: {file_path}, 大小: {len(audio_data)} 字节")

#     return f"音频块已接收并保存到 {file_path}", 200

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5001, debug=True)

# from flask import Flask, request
# from flask_cors import CORS
# import wave
# import os

# app = Flask(__name__)
# CORS(app)  # 启用 CORS

# # 指定上传目录
# UPLOAD_DIR = "uploads"

# # 确保上传目录存在
# if not os.path.exists(UPLOAD_DIR):
#     os.makedirs(UPLOAD_DIR)

# @app.route('/')
# def index():
#     return "ESP32與ChatGPT語音開發"

# @app.route('/upload_audio', methods=['POST'])
# def upload_audio():
#     audio_data = request.data  # 接收来自 ESP32 的二进制音频数据
    
#     # 设置WAV文件的参数
#     num_channels = 1  # 单声道
#     sample_width = 2  # 16位音频（2字节）
#     frame_rate = 16000  # 采样率，16kHz
    
#     # 使用固定的文件名，保存到 uploads 目录下
#     file_path = os.path.join(UPLOAD_DIR, "recording.wav")
    
#     # 保存为 WAV 文件
#     with wave.open(file_path, 'wb') as wav_file:
#         wav_file.setnchannels(num_channels)
#         wav_file.setsampwidth(sample_width)
#         wav_file.setframerate(frame_rate)
#         wav_file.writeframes(audio_data)
    
#     return f"音频保存成功: {file_path}", 200

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5001, debug=True)
