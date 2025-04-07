import requests
from bs4 import BeautifulSoup
import re
import os


def download_tieba_video(url):
    # 设置请求头模拟浏览器访问
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://tieba.baidu.com/",
    }

    try:
        # 获取贴吧帖子内容
        response = requests.get(url, headers=headers)
        response.encoding = "utf-8"
        if response.status_code != 200:
            raise Exception(f"请求失败，状态码：{response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")

        # 查找一楼视频容器（根据贴吧最新页面结构调整选择器）
        video_container = soup.find("div", {"class": "video_src_wrapper"})
        name = soup.find("meta", {"name": "description"})
        pattern = r'content="(.*?)视频来自：百度贴吧"'
        match_name = re.search(pattern, str(name))
        embed_tag = video_container.find("embed")
        # 获取视频地址
        video_url = embed_tag["data-video"]

        # 如果未找到，尝试正则匹配
        if not video_url:
            match = re.search(r'"videoUrl":"(https?:\\/\\/[^"]+)"', response.text)
            if match:
                video_url = match.group(1).replace("\\", "")

        if not video_url:
            raise Exception("未找到视频地址")

        # 下载视频（添加视频请求的Referer）
        video_headers = headers.copy()
        video_headers["Referer"] = url
        video_response = requests.get(video_url, headers=video_headers, stream=True)

        if video_response.status_code != 200:
            raise Exception("视频下载失败")

        # 保存视频文件
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        os.makedirs(os.path.join(script_dir, "history"), exist_ok=True)
        save_path = os.path.join(script_dir, "history", match_name.group(1) + ".mp4")
        with open(save_path, "wb") as f:
            for chunk in video_response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        print(f"视频已保存至：{save_path}")
        return save_path
    except Exception as e:
        print(f"发生错误：{str(e)}")


# 使用示例
if __name__ == "__main__":
    tieba_url = input("请输入贴吧帖子地址：")
    download_tieba_video(tieba_url)