import re
import requests
import base64
import sys
from urllib.parse import urlparse

# --- 配置区 --- START ---
# VLESS 订阅源文件，每行一个链接或 URL
SOURCES_FILE = "sources.txt"
# 输出文件名
OUTPUT_FILE = "aggregated_proxies.txt"
# --- 配置区 --- END ---

def is_valid_url(url):
    """检查字符串是否是有效的 URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_content_from_url(url):
    """从 URL 获取纯文本内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        # 直接返回原始文本内容
        print(f"  Successfully fetched content from {url}.")
        return response.text.strip()

    except requests.exceptions.Timeout:
        print(f"Error: Timeout fetching URL {url}", file=sys.stderr)
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error processing content from {url}: {e}", file=sys.stderr)
        return None

# Base64 解码函数不再需要，可以移除或注释掉
# def decode_base64(encoded_str): ...

def extract_ip_comment_lines(text_content):
    """从文本内容中逐行提取 'IP地址#注释' 格式的行"""
    ip_lines = set()
    if not text_content:
        return ip_lines

    # 匹配 IPv4 地址后跟 '#' 和任意字符的格式
    ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}#.*')
    lines = text_content.splitlines()
    for line in lines:
        line = line.strip()
        if ip_pattern.match(line):
            ip_lines.add(line)
    return ip_lines

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
    except IOError as e:
        print(f"Error reading sources file {filename}: {e}", file=sys.stderr)
    return sources

def main():
    all_ip_lines = set()
    subscription_sources = read_sources_from_file(SOURCES_FILE)

    if not subscription_sources:
        print("No sources found or failed to read sources file. Exiting.", file=sys.stderr)
        try:
            open(OUTPUT_FILE, 'w').close()
            print(f"Created/Cleared {OUTPUT_FILE} as no sources were processed.")
        except IOError as e:
            print(f"Error creating/clearing file {OUTPUT_FILE}: {e}", file=sys.stderr)
        return

    # 不再需要 proxy_pattern
    # proxy_pattern = re.compile(r'^\w+://.+')
    for source in subscription_sources:
        source = source.strip()
        if source.startswith('http://') or source.startswith('https://'):
            # 是 URL，尝试获取内容
            print(f"Fetching content from URL: {source}")
            content = get_content_from_url(source)
            if content:
                # 从获取到的纯文本内容中提取 IP#注释 格式的行
                found_lines = extract_ip_comment_lines(content)
                if found_lines:
                    print(f"  Found {len(found_lines)} potential IP lines in content from {source}.")
                    all_ip_lines.update(found_lines)
                else:
                    print(f"  No potential IP lines found in content from {source}.")
            else:
                print(f"  Failed to get or process content from {source}.")
        else:
            # 不是 URL，直接添加到结果集
            print(f"Adding direct entry: {source}")
            all_ip_lines.add(source)

    # 写入文件
    if all_ip_lines:
        print(f"\nTotal unique potential IP lines found: {len(all_ip_lines)}")
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                for line in sorted(list(all_ip_lines)): # 排序后写入
                    f.write(line + '\n')
            print(f"Successfully wrote potential IP lines to {OUTPUT_FILE}")
        except IOError as e:
            print(f"Error writing to file {OUTPUT_FILE}: {e}", file=sys.stderr)
    else:
        print("No potential IP lines found from any source.")
        try:
            open(OUTPUT_FILE, 'w').close()
            print(f"Created/Cleared {OUTPUT_FILE} as no potential IP lines were found.")
        except IOError as e:
            print(f"Error creating/clearing file {OUTPUT_FILE}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()