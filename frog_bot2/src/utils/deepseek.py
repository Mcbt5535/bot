import json
import datetime
import os
from openai import OpenAI


class ChatBackend:

    def __init__(self, api_key, script_dir=os.path.dirname(os.path.abspath(__file__))):
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.messages = []
        self.attachment_content = ""
        self.model = "deepseek-chat"
        self.temperature = 0.2
        self.max_tokens = 8192
        self.top_p = 1
        self.frequency_penalty = 0.0
        self.script_dir = script_dir
        self.current_log_filename = None
        self.lib_sent = False

    def set_parameters(self, **kwargs):
        # 更新模型相关参数
        for param in ["model", "temperature", "top_p", "frequency_penalty"]:
            if param in kwargs:
                setattr(self, param, kwargs[param])

    def add_attachment(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.attachment_content = file.read()
            return True
        except Exception as e:
            print(f"Error reading attachment: {e}")
            return False

    def _prepare_message(self, user_input):
        # 若有附件内容，则附加到用户输入后面
        if self.attachment_content:
            user_input += f"\n\n[Attachment Content]\n{self.attachment_content}"
            self.attachment_content = ""
        return {"role": "user", "content": user_input}

    def send_message(self, user_input):
        try:
            user_message = self._prepare_message(user_input)
            self.messages.append(user_message)
            response = self.client.chat.completions.create(model=self.model, messages=self.messages, temperature=self.temperature, max_tokens=self.max_tokens, top_p=self.top_p, frequency_penalty=self.frequency_penalty, stream=True)
            assistant_content = ""
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    new_text = chunk.choices[0].delta.content
                    assistant_content += new_text
                    yield new_text
            self.messages = []
        except Exception as e:
            yield f"API Error: {str(e)}"

    def finalize_response(self, assistant_content):
        # 完整记录助手回复并保存历史记录
        assistant_message = {"role": "assistant", "content": assistant_content}
        self.messages.append(assistant_message)
        self.save_history()

    def save_history(self):
        try:
            history_dir = os.path.join(self.script_dir, "history")
            if not os.path.exists(history_dir):
                os.makedirs(history_dir)
            if not self.current_log_filename:
                current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                self.current_log_filename = f"chat_history_{current_time}"
            json_filename = os.path.join(history_dir, f"{self.current_log_filename}.json")
            txt_filename = os.path.join(history_dir, f"{self.current_log_filename}.txt")
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=2)
            with open(txt_filename, 'w', encoding='utf-8') as f:
                for message in self.messages:
                    f.write(f"{message['role'].capitalize()}: {message['content']}\n\n")
            return True
        except Exception as e:
            print(f"Save Error: {e}")
            return False

    def load_history(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                history = json.load(f)
            self.messages.extend(history)
            return True
        except FileNotFoundError:
            print("No history file found, starting fresh.")
            return False
        except Exception as e:
            print(f"Load Error: {e}")
            return False

    def import_from_text(self, text_filename):
        try:
            with open(text_filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            self.messages.append({"role": "system", "content": content})
            print(f"Imported content from {text_filename}")
            return True
        except Exception as e:
            print(f"Import failed: {e}")
            return False
