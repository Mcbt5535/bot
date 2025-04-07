import os
from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    Bot,
    Message,
    MessageEvent,
    MessageSegment,
    PrivateMessageEvent,
)
from nonebot.params import CommandArg
from nonebot_plugin_apscheduler import scheduler

from utils.deepseek.deepseek import ChatBackend
from utils.jmcomic1.jmdownload import download, create_password_protected_zip
from utils.video_download.tieba import download_tieba_video
from utils.AI_voice.AI_voice import say
from utils.downloader.downloader_top import download_url
import datetime

chat_backend = ChatBackend(api_key="sk-a978172cfd784775bcd1a0b47a36ec34")


def get_conv_id(event: MessageEvent):
    if isinstance(event, GroupMessageEvent):
        return f"group_{event.group_id}"
    elif isinstance(event, PrivateMessageEvent):
        return f"private_{event.user_id}"
    return "default"


# 定时任务：每天凌晨归档群聊记录
@scheduler.scheduled_job("cron", hour=0, minute=0)
async def daily_archive():
    current_time = datetime.datetime.now()
    for conv_id in list(chat_backend.conversations.keys()):
        if conv_id.startswith("group_"):
            # 修改点：归档时保留完整记录
            if chat_backend.save_conversation(conv_id, archive=True):
                print(f"Archived group conversation: {conv_id}")


help_cmd = on_command("help", priority=10, block=True)


@help_cmd.handle()
async def handle_help(event: MessageEvent):
    help_text = """
    欢迎使用  frogbot！以下是可用的命令：
    - /help：查看可用命令
    - /ds 消息：与机器人对话
    - /clear：清空对话记录
    - /jm id：下载指定的漫画,密码为id
    - /kkp: 下载磁力连接
    """
    await help_cmd.finish(f"{help_text}")


# 在nonebot处理器部分修改clear_cmd的定义和逻辑
clear_cmd = on_command("clear", priority=10, block=True)


@clear_cmd.handle()
async def handle_clear(event: MessageEvent):  # 修改为MessageEvent以同时处理私聊和群聊
    conv_id = get_conv_id(event)

    # 添加权限检查（可选）
    if isinstance(event, GroupMessageEvent):
        # 可以添加检查是否是管理员等权限逻辑
        pass

    if chat_backend.save_conversation(conv_id, archive=True):
        reply = "对话记录已归档并清空"
        if isinstance(event, GroupMessageEvent):
            reply += f"\n(群聊记录已归档，新的对话将重新开始)"
        await clear_cmd.finish(reply)
    else:
        await clear_cmd.finish("没有需要清空的记录")


# 主对话处理
ds_cmd = on_command("ds", rule=to_me(), priority=10, block=True)


@ds_cmd.handle()
async def handle_ds(event: MessageEvent, args: Message = CommandArg()):
    user_input = args.extract_plain_text().strip()
    if not user_input:
        await ds_cmd.finish("请输入您的问题")

    conv_id = get_conv_id(event)
    response = chat_backend.send_message(user_input, conv_id)

    # 修改点：日常保存时不归档，只更新latest文件
    chat_backend.save_conversation(conv_id)

    await ds_cmd.finish(response)


jm_cmd = on_command("jm", rule=to_me(), priority=10, block=True)


@jm_cmd.handle()
async def handle_jm(event: MessageEvent, args: Message = CommandArg()):
    id = args.extract_plain_text().strip()
    # id = 571984
    if not id:
        await jm_cmd.finish("请输入要下载的漫画ID")
    script_path = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_path, "..", "utils", "jmcomic1")
    download(script_path, f"{id}")
    # 使用示例
    source_folder = os.path.join(script_path, "download", f"{id}")
    file_path = create_password_protected_zip(source_folder, source_folder)
    if not os.path.exists(file_path):
        await jm_cmd.finish("下载失败")

    file_msg = MessageSegment("file", {"file": f"file://{file_path}"})
    await jm_cmd.finish(Message(file_msg))


tb_cmd = on_command("tb", rule=to_me(), priority=10, block=True)
@tb_cmd.handle()
async def handle_tb(event: MessageEvent, args: Message = CommandArg()):
    url = args.extract_plain_text().strip()
    if not url:
        await tb_cmd.finish("请输入要下载的视频url")
    # script_path = os.path.dirname(os.path.abspath(__file__))
    # script_path = os.path.join(script_path, "..", "utils", "video_download")
    save_path = download_tieba_video(f"{url}")
    try:
        file_msg = MessageSegment.video(file="file://" + save_path)
        await tb_cmd.finish(Message(file_msg))
    except Exception as e:
        pass
    # await tb_cmd.send(msg)
    
# voice_cmd = on_command("v", rule=to_me(), priority=10, block=True)
# @voice_cmd.handle()
# async def handle_voice(event: MessageEvent, args: Message = CommandArg()):
#     text = args.extract_plain_text().strip()
#     if not text:
#         await voice_cmd.finish("请输入要转换的文字")
#     # script_path = os.path.dirname(os.path.abspath(__file__))
#     # script_path = os.path.join(script_path, "..", "utils", "AI_voice")
#     voice_path = say(text)
#     file_msg = MessageSegment.record(file="file://" + voice_path)
#     await voice_cmd.finish(Message(file_msg))

kkp_cmd = on_command("kkp", rule=to_me(), priority=10, block=True)
@kkp_cmd.handle()
async def handle_kkp(event: MessageEvent, args: Message = CommandArg()):
    url = args.extract_plain_text().strip()
    
    if not url:
        await kkp_cmd.finish("请输入下载链接")
    try:
        msg = download_url(url)
        await kkp_cmd.finish(msg)
    except Exception as e:
        pass
    # script_path = os.path.dirname(os.path.abspath(__file__))