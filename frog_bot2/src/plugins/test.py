import os

from nonebot import on_regex
from nonebot import on_command
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot, Message, MessageEvent
from nonebot.params import CommandArg

from utils.deepseek import ChatBackend

# from ds_backend import ChatBackend

# Test = on_regex(pattern=r"^测试$", priority=1)
test_cmd = on_command("出列", rule=to_me())
ds_cmd = on_command("ds", rule=to_me(),priority=10,block=True)
chat_backend = ChatBackend(api_key="")

# @Test.handle()
# async def Test_send(bot: Bot, event: GroupMessageEvent, state: T_State):
#     msg = "Bot启动正常"
#     await Test.finish(message=Message(msg))

@ds_cmd.handle()
async def handle_ds(args: Message = CommandArg()):
    # 提问内容
    # await ds_cmd.send("111")
    # await ds_cmd.send(f"222{args.extract_plain_text()}")
    if user_input := args.extract_plain_text():
        response = ""
        # await ds_cmd.send("333")
        for chunk in chat_backend.send_message(user_input):
            response += chunk
        
        await ds_cmd.finish(response)
    else:
        await ds_cmd.finish("请输入提问内容")

@test_cmd.handle()
async def handle_test(event: MessageEvent):
    await test_cmd.send("到")


# if __name__ == "__main__":
#     # 初始化 ChatBackend
    
#     # 发送消息并获取响应
