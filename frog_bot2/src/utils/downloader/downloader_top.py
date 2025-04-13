# qbittorrent_client.py

import re
import time
import qbittorrentapi

# ─── 配置区 ─────────────────────────────────────────────
QB_HOST = "http://192.168.122.1"
QB_PORT = 8888
QB_USERNAME = "admin"
QB_PASSWORD = "k2B38GneY"
METADATA_TIMEOUT = 60  # 最长等待元数据下载秒数
METADATA_INTERVAL = 1  # 轮询间隔秒数

# 匹配磁力链接并提取 info-hash
MAGNET_REGEX = re.compile(r"magnet:\?xt=urn:btih:([0-9A-Fa-f]+)(?:&\S*)?")


# ─── 核心功能函数 ────────────────────────────────────────
def connect_qb() -> qbittorrentapi.Client:
    """
    连接并登录 qBittorrent Web API，失败时抛出 qbittorrentapi.LoginFailed。
    """
    client = qbittorrentapi.Client(
        host=QB_HOST, port=QB_PORT, username=QB_USERNAME, password=QB_PASSWORD
    )
    client.auth_log_in()
    return client


def add_magnet(client: qbittorrentapi.Client, magnet_link: str):
    """
    向 qBittorrent 添加一个磁力下载任务。
    """
    client.torrents_add(urls=magnet_link)


def get_torrent_info(client: qbittorrentapi.Client, info_hash: str):
    """
    查询单个种子的信息，找不到返回 None。
    """
    infos = client.torrents_info(hashes=info_hash)
    return infos[0] if infos else None


def wait_for_metadata(client: qbittorrentapi.Client, info_hash: str):
    """
    轮询等待种子元数据下载完成（即 info.name 不再等于 info_hash）。
    超时返回 None。
    """
    deadline = time.time() + METADATA_TIMEOUT
    while time.time() < deadline:
        info = get_torrent_info(client, info_hash)
        if info and info.name.lower() != info_hash.lower():
            return info
        time.sleep(METADATA_INTERVAL)
    return None


# ─── 对外接口 ───────────────────────────────────────────
def download_url(url: str) -> str:
    """
    接收一条包含磁力链接的字符串，添加下载并返回结果字符串。
    """
    # 1. 提取 info-hash
    m = MAGNET_REGEX.search(url)
    if not m:
        return "❌ 未检测到磁力链接"
    info_hash = m.group(1).lower()
    magnet_link = f"magnet:?xt=urn:btih:{info_hash}"

    # 2. 登录 qBittorrent
    try:
        qb = connect_qb()
    except qbittorrentapi.LoginFailed as e:
        return f"❌ 登录 qBittorrent 失败：{e}"

    # 3. 添加下载任务
    try:
        add_magnet(qb, magnet_link)
    except Exception as e:
        return f"❌ 添加下载失败：{e}"

    # 4. 等待元数据完成，获取真实种子名和路径
    info = wait_for_metadata(qb, info_hash)
    if not info:
        return (
            f"✅ 已添加下载：\n{magnet_link}\n\n"
            "⚠️ 元数据下载超时，无法获取真实文件夹名"
        )

    full_path = f"{info.save_path}/{info.name}"
    return f"✅ 已添加下载：\n{magnet_link}\n\n" f"📂 下载文件夹：\n{full_path}"


# ─── 示例调用 ───────────────────────────────────────────
if __name__ == "__main__":
    test_link = "magnet:?xt=urn:btih:ABCDE12345..."
    print(download_url(test_link))
