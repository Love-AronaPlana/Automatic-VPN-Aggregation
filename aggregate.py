import re
import requests
import base64
import sys
from urllib.parse import urlparse

# --- 配置区 --- START ---
# VLESS 订阅源文件，每行一个链接或 URL
SOURCES_FILE = "sources.txt"
# 输出文件名
OUTPUT_FILE = "aggregated_vless.txt"
# --- 配置区 --- END ---

def is_valid_url(url):
    """检查字符串是否是有效的 URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_links_from_url(url):
    """从 URL 获取内容"""
    try:
        response = requests.get(url, timeout=10) # 设置 10 秒超时
        response.raise_for_status() # 如果请求失败则抛出异常
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}", file=sys.stderr)
        return None

def decode_base64(encoded_str):
    """尝试 Base64 解码"""
    try:
        # 处理可能的 padding 问题
        padding = '=' * (-len(encoded_str) % 4)
        decoded_bytes = base64.b64decode(encoded_str + padding)
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        # print(f"Error decoding Base64 string: {encoded_str[:50]}... Error: {e}", file=sys.stderr)
        return None # 返回 None 表示解码失败

def extract_vless_links(content):
    """从文本内容中提取 VLESS 链接"""
    # 正则表达式匹配 vless:// 开头的链接
    vless_pattern = r"vless:\/\/[a-zA-Z0-9\+\/\=\-\.\_\@\:\#\?]+"
    return re.findall(vless_pattern, content)

def read_sources_from_file(filename):
    """从文件读取订阅源，每行一个"""
    sources = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'): # 忽略空行和注释行
                    sources.append(line)
        print(f"Read {len(sources)} sources from {filename}")
    except FileNotFoundError:
        print(f"Error: Sources file '{filename}' not found.", file=sys.stderr)
        # 可以选择退出或返回空列表
        # sys.exit(1)
    except IOError as e:
        print(f"Error reading sources file {filename}: {e}", file=sys.stderr)
        # sys.exit(1)
    return sources

def main():
    all_vless_links = set()
    subscription_sources = read_sources_from_file(SOURCES_FILE)

    if not subscription_sources:
        print("No sources found or failed to read sources file. Exiting.", file=sys.stderr)
        # 确保即使没有源也创建/清空输出文件
        try:
            open(OUTPUT_FILE, 'w').close()
            print(f"Created/Cleared {OUTPUT_FILE} as no sources were processed.")
        except IOError as e:
            print(f"Error creating/clearing file {OUTPUT_FILE}: {e}", file=sys.stderr)
        return # 提前退出

    for source in subscription_sources:
        content = None
        if source.startswith("vless://"):
            # 直接是 VLESS 链接
            all_vless_links.add(source.strip())
            print(f"Added direct VLESS link: {source[:50]}...")
            continue
        elif is_valid_url(source):
            # 是 URL，尝试获取内容
            print(f"Fetching content from URL: {source}")
            content = get_links_from_url(source)
            if not content:
                continue # 获取失败，跳过
        else:
            print(f"Skipping invalid source: {source}", file=sys.stderr)
            continue

        # 尝试提取 VLESS 链接
        found_links = extract_vless_links(content)
        if found_links:
            print(f"  Found {len(found_links)} VLESS links directly.")
            for link in found_links:
                all_vless_links.add(link.strip())
        else:
            # 如果直接提取不到，尝试 Base64 解码后再提取
            print(f"  No direct VLESS links found, attempting Base64 decode...")
            decoded_content = decode_base64(content.strip()) # 先移除首尾空白再解码
            if decoded_content:
                decoded_links = extract_vless_links(decoded_content)
                if decoded_links:
                    print(f"  Found {len(decoded_links)} VLESS links after Base64 decode.")
                    for link in decoded_links:
                        all_vless_links.add(link.strip())
                else:
                    print(f"  No VLESS links found after Base64 decode.")
            else:
                 print(f"  Failed to decode Base64 content or decoded content is empty.")

    # 写入文件
    if all_vless_links:
        print(f"\nTotal unique VLESS links found: {len(all_vless_links)}")
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                for link in sorted(list(all_vless_links)): # 排序后写入
                    f.write(link + '\n')
            print(f"Successfully wrote links to {OUTPUT_FILE}")
        except IOError as e:
            print(f"Error writing to file {OUTPUT_FILE}: {e}", file=sys.stderr)
    else:
        print("No VLESS links found from any source.")
        # 如果没有找到链接，可以选择创建一个空文件或保留旧文件
        # 这里选择创建/覆盖为空文件
        try:
            open(OUTPUT_FILE, 'w').close()
            print(f"Created/Cleared {OUTPUT_FILE} as no links were found.")
        except IOError as e:
            print(f"Error creating/clearing file {OUTPUT_FILE}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()