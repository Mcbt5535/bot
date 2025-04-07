import json
import datetime
import os
from openai import OpenAI


class ChatBackend:

    def __init__(self, api_key, script_dir=os.path.dirname(os.path.abspath(__file__))):
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.conversations = {}  # 存储所有对话记录
        self.attachment_content = ""
        self.model = "deepseek-chat"
        self.temperature = 0.2
        self.max_tokens = 8192
        self.top_p = 0.5
        self.frequency_penalty = 0.0
        self.script_dir = script_dir

    def set_parameters(self, **kwargs):
        for param in ["model", "temperature", "top_p", "frequency_penalty"]:
            if param in kwargs:
                setattr(self, param, kwargs[param])

    def add_attachment(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                self.attachment_content = file.read()
            return True
        except Exception as e:
            print(f"Error reading attachment: {e}")
            return False

    def _prepare_message(self, user_input):
        if self.attachment_content:
            user_input += f"\n\n[Attachment Content]\n{self.attachment_content}"
            self.attachment_content = ""
        return {"role": "user", "content": user_input}

    def get_conversation(self, conv_id):
        if conv_id not in self.conversations:
            self.conversations[conv_id] = {
                "messages": [],
                "last_active": datetime.datetime.now(),
            }
        return self.conversations[conv_id]

    def send_message(self, user_input, conv_id):
        try:
            conversation = self.get_conversation(conv_id)
            user_message = self._prepare_message(user_input)
            conversation["messages"].append(user_message)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=conversation["messages"],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
            )

            assistant_content = response.choices[0].message.content
            conversation["messages"].append(
                {"role": "assistant", "content": assistant_content}
            )
            conversation["last_active"] = datetime.datetime.now()

            return assistant_content
        except Exception as e:
            return f"API Error: {str(e)}"

    def save_conversation(self, conv_id, archive=False):
        """保存对话记录，archive=True时进行归档"""
        if conv_id not in self.conversations:
            return False

        conversation = self.conversations[conv_id]
        if not conversation["messages"]:
            return False

        # 确定存储路径
        base_dir = os.path.join(
            self.script_dir, "history", "archive" if archive else "active"
        )

        if conv_id.startswith("group_"):
            group_id = conv_id.split("_")[1]
            save_path = os.path.join(base_dir, "groups", group_id)
        elif conv_id.startswith("private_"):
            user_id = conv_id.split("_")[1]
            save_path = os.path.join(base_dir, "users", user_id)
        else:
            return False

        os.makedirs(save_path, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # 修改点：归档时生成时间戳文件，非归档时覆盖latest文件
        if archive:
            json_filename = f"{timestamp}.json"
            txt_filename = f"{timestamp}.txt"
            # 归档后重置对话
            del self.conversations[conv_id]
        else:
            json_filename = "latest.json"
            txt_filename = "latest.txt"

        # 保存JSON
        with open(os.path.join(save_path, json_filename), "w", encoding="utf-8") as f:
            json.dump(conversation["messages"], f, ensure_ascii=False, indent=2)

        # 保存TXT
        with open(os.path.join(save_path, txt_filename), "w", encoding="utf-8") as f:
            for msg in conversation["messages"]:
                f.write(f"{msg['role'].capitalize()}: {msg['content']}\n\n")

        return True
