import os
# deepseek分析回答后sovits合成后发送语音
def say(text):
    print(text)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "data", "audio.wav")
    return file_path


