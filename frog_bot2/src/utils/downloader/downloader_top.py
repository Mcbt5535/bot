# bot/plugins/qbittorrent_magnet.py

import re
import qbittorrentapi


# 1. 匹配磁力链接的正则
MAGNET_REGEX = r"(magnet:\?xt=urn:btih:[a-zA-Z0-9]+[^\s]*)"


# 2. 下载函数
def download_url(url: str):
    """
    下载磁力链接并添加到 qBittorrent 下载任务。
    """
    match = re.search(MAGNET_REGEX, url)
    print(f"1 {match}")
    if not match:
        return f"❌ 未检测到磁力链接"  # 理论上不会进来

    magnet_link = match.group(1)
    print(f"2 {magnet_link}")
    info_hash = match.group(2).lower()
    print(f"3 {info_hash}")
    
    # 3. 连接 qBittorrent Web API
    qb = qbittorrentapi.Client(
        host="http://192.168.122.1",  # 注意加 http://
        port=8888,
        username="admin",
        password="k2B38GneY",
    )

    try:
        qb.auth_log_in()  # 登录
    except qbittorrentapi.LoginFailed as e:
        return f"❌ 无法登录 qBittorrent：{e}"

    # 4. 添加任务
    try:
        qb.torrents_add(urls=magnet_link)
    except Exception as e:
        return f"❌ 添加下载失败：{e}"

    # 5. 回复用户
    # return f"✅ 已添加下载：\n{magnet_link}"


    try:
        # hashes 参数可以传单个 hash，也可以是逗号分隔的多个
        infos = qb.torrents_info(hashes=info_hash)
        if not infos:
            raise ValueError("未能获取到种子信息")
        info = infos[0]
        folder_name = info.name               # 种子名，通常也是文件夹名
        save_path   = info.save_path          # 完整的保存目录，不含种子名
        full_path   = f"{save_path}/{folder_name}"
    except Exception as e:
        # 如果查询失败，也不影响下载，只是返回不了文件夹名
        return f"✅ 已添加下载：{magnet_link}\n⚠️ 添加成功，但获取文件夹名时出错：{e}"
        
    str1 = f"✅ 已添加下载：\n"
    str1 += f"{magnet_link}\n\n"
    str1 += f"📂 下载文件夹：\n"
    str1 += f"{full_path}"
    
    return str1