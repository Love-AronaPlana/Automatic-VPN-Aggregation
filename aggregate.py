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
    """从 URL 获取内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(url, headers=headers, timeout=10) # 设置 10 秒超时，添加 User-Agent
        response.raise_for_status() # 如果请求失败则抛出异常
        # 尝试检测是否是 Base64 编码
        content = response.text.strip()
        # 简单的 Base64 检测：长度是 4 的倍数，且只包含 Base64 字符
        # 注意：这可能误判某些非 Base64 文本，但对于订阅链接通常足够
        is_likely_base64 = len(content) % 4 == 0 and re.match(r'^[A-Za-z0-9+/=\s]*$', content)

        if is_likely_base64:
            print(f"  Content from {url} seems Base64 encoded, attempting decode...")
            decoded_content = decode_base64(content)
            if decoded_content:
                print(f"  Successfully decoded Base64 content.")
                return decoded_content
            else:
                print(f"  Failed to decode Base64 content, treating as plain text.", file=sys.stderr)
                return content # 解码失败，返回原始内容
        else:
            print(f"  Content from {url} treated as plain text.")
            return content # 不是 Base64，直接返回

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error processing content from {url}: {e}", file=sys.stderr)
        return None # 其他处理错误

def decode_base64(encoded_str):
    """尝试 Base64 解码，处理可能的 padding 问题"""
    try:
        # 移除可能的空白字符
        encoded_str = re.sub(r'\s', '', encoded_str)
        padding = '=' * (-len(encoded_str) % 4)
        decoded_bytes = base64.b64decode(encoded_str + padding)
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        # print(f"Error decoding Base64 string: {encoded_str[:50]}... Error: {e}", file=sys.stderr)
        return None # 返回 None 表示解码失败

def extract_proxy_links_from_text(text_content):
    """从文本内容中逐行提取代理链接 (ss, vmess, trojan, vless)"""
    proxy_links = set()
    if not text_content:
        return proxy_links

    # 使用正则表达式匹配常见的代理协议链接
    # 支持 ss://, vmess://, trojan://, vless://
    proxy_pattern = re.compile(r'^(ss|vmess|trojan|vless)://[^s]+')
    lines = text_content.splitlines()
    for line in lines:
        line = line.strip()
        if proxy_pattern.match(line):
            proxy_links.add(line)
    return proxy_links

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
    all_proxy_links = set()
    subscription_sources = read_sources_from_file(SOURCES_FILE)

    if not subscription_sources:
        print("No sources found or failed to read sources file. Exiting.", file=sys.stderr)
        try:
            open(OUTPUT_FILE, 'w').close()
            print(f"Created/Cleared {OUTPUT_FILE} as no sources were processed.")
        except IOError as e:
            print(f"Error creating/clearing file {OUTPUT_FILE}: {e}", file=sys.stderr)
        return

    proxy_pattern = re.compile(r'^(ss|vmess|trojan|vless)://[^s]+')
    for source in subscription_sources:
        if proxy_pattern.match(source.strip()):
            # 直接是代理链接
            all_proxy_links.add(source.strip())
            print(f"Added direct proxy link: {source[:50]}...")
        elif is_valid_url(source):
            # 是 URL，尝试获取内容
            print(f"Fetching content from URL: {source}")
            content = get_content_from_url(source)
            if content:
                # 从获取到的内容（可能是纯文本或解码后的文本）中提取代理链接
                found_links = extract_proxy_links_from_text(content)
                if found_links:
                    print(f"  Found {len(found_links)} proxy links in content from {source}.")
                    all_proxy_links.update(found_links)
                else:
                    print(f"  No proxy links found in content from {source}.")
            else:
                print(f"  Failed to get or process content from {source}.")
        else:
            print(f"Skipping invalid source: {source}", file=sys.stderr)

    # 写入文件
    if all_proxy_links:
        print(f"\nTotal unique proxy links found: {len(all_proxy_links)}")
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                for link in sorted(list(all_proxy_links)): # 排序后写入
                    f.write(link + '\n')
            print(f"Successfully wrote links to {OUTPUT_FILE}")
        except IOError as e:
            print(f"Error writing to file {OUTPUT_FILE}: {e}", file=sys.stderr)
    else:
        print("No proxy links found from any source.")
        try:
            open(OUTPUT_FILE, 'w').close()
            print(f"Created/Cleared {OUTPUT_FILE} as no links were found.")
        except IOError as e:
            print(f"Error creating/clearing file {OUTPUT_FILE}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()