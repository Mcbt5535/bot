import os

import jmcomic
import pyzipper


def download(script_path: str, id: str):
    os.environ["JM_DIR"] = script_path
    # 创建配置对象
    option_path = os.path.join(script_path, "options.yml")
    option = jmcomic.create_option_by_file(option_path)
    # Pmyname
    # 使用option对象来下载本子
    jmcomic.download_album(f"{id}", option)

def create_password_protected_zip(source_folder: str, output_path=None):
    """
    将指定文件夹下的所有文件压缩成带密码的ZIP文件

    参数:
        source_folder: 要压缩的文件夹路径
        output_path: 输出的ZIP文件完整路径(可选，包含路径和文件名)
    """
    # 如果未指定输出路径，则使用文件夹名 + .zip，保存在当前目录
    if output_path is None:
        folder_name = os.path.basename(os.path.normpath(source_folder))
        output_path = f"{folder_name}.zip"
    else:
        # 确保输出路径有.zip扩展名
        if not output_path.lower().endswith(".zip"):
            output_path += ".zip"

    # 获取密码(使用文件夹名)
    password = os.path.basename(os.path.normpath(source_folder))

    # 确保源文件夹存在
    if not os.path.exists(source_folder):
        raise FileNotFoundError(f"文件夹不存在: {source_folder}")

    # 创建输出目录(如果不存在)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 创建带密码的ZIP文件
    with pyzipper.AESZipFile(
        output_path, "w", compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES
    ) as zipf:
        # 设置密码(转换为bytes)
        zipf.setpassword(password.encode("utf-8"))

        # 遍历文件夹中的所有文件
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                file_path = os.path.join(root, file)

                # 计算在ZIP中的相对路径
                arcname = os.path.relpath(file_path, start=source_folder)

                # 将文件添加到ZIP中
                zipf.write(file_path, arcname)

    print(f"已创建带密码的ZIP文件: {output_path}")
    print(f"解压密码: {password}")
    return output_path


if __name__ == "__main__":
    script_path = os.path.dirname(os.path.abspath(__file__))
    id = 430371
    download(script_path, f"{id}")
    # 使用示例
    source_folder = os.path.join(script_path, "download", f"{id}")
    create_password_protected_zip(source_folder, source_folder)
