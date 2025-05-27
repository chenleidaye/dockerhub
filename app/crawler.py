import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, urljoin, urlparse, parse_qs

BASE_URL = "https://5721004.xyz"
SAVE_ROOT = "strm_files"  # 根保存目录
os.makedirs(SAVE_ROOT, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": BASE_URL
}

visited_dirs = set()

def url_to_local_path(url):
    parsed = urlparse(url)
    path_segments = [seg for seg in unquote(parsed.path).split('/') if seg and seg != '?']
    if parsed.query:
        query_segments = [seg for seg in unquote(parsed.query).split('/') if seg]
        path_segments.extend(query_segments)
    season_keys = {'bu', 's2', 's3', 's4', 's5', 'pc', 'pc2', 'pc3', 'pc4'}
    idx = 0
    for i, seg in enumerate(path_segments):
        if seg.lower() in season_keys:
            idx = i
            break
    path_segments = path_segments[idx:]
    return os.path.join(SAVE_ROOT, *path_segments)

def process_directory(dir_url):
    if dir_url in visited_dirs:
        return 0
    visited_dirs.add(dir_url)

    try:
        response = requests.get(dir_url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"🚨 目录访问失败: {e}")
        return 0

    response.encoding = 'utf-8'
    try:
        soup = BeautifulSoup(response.text, "lxml")
    except Exception as e:
        print(f"🚨 解析错误，跳过页面：{dir_url} -> 错误: {e}")
        return 0

    count = 0
    m3u8_files = []

    for a in soup.select('a.video[data-src]'):
        data_src = a.get("data-src")
        if not data_src:
            continue

        m3u8_url = urljoin(dir_url, data_src)
        raw_filename = unquote(data_src.split("/")[-1].split("?")[0])

        if raw_filename.lower() == "jinricp.m3u8":
            print(f"🚫 已屏蔽：{raw_filename}")
            continue

        strm_filename = raw_filename.replace(".m3u8", ".strm")
        m3u8_files.append((strm_filename, m3u8_url))

    if m3u8_files:
        local_dir = url_to_local_path(dir_url)
        os.makedirs(local_dir, exist_ok=True)
        print(f"\n📂 进入目录：{dir_url} -> 本地目录：{local_dir}")

        for strm_filename, m3u8_url in m3u8_files:
            strm_path = os.path.join(local_dir, strm_filename)
            if not os.path.exists(strm_path):
                parsed_url = urlparse(m3u8_url)
                query_dict = parse_qs(parsed_url.query)
                if 'path' in query_dict:
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                    real_path = query_dict['path'][0]
                    real_url = urljoin(base_url + "/", real_path.lstrip('/'))
                else:
                    real_url = m3u8_url

                with open(strm_path, "w", encoding="utf-8") as f:
                    f.write(real_url)
                print(f"✅ 生成：{strm_filename}")
                count += 1

        print(f"📥 本目录共处理 {count} 个视频")

    sub_dirs = []
    for li in soup.select('li.mdui-list-item.mdui-ripple'):
        a = li.find('a')
        if not a or not a.get('href'):
            continue

        href = a['href']
        if href.startswith(('javascript:', '#')):
            continue

        sub_url = urljoin(dir_url, href)

        if 'sample' in sub_url.lower():
            continue

        if any(href.lower().endswith(ext) for ext in ['.m3u8', '.md', '.txt', '.jpg', '.png', '.gif', '.jpeg']):
            continue

        if not any(key in sub_url for key in ['bu/', 's2/', 's3/', 's4/', 's5/', 'pc/', 'pc2/', 'pc3/', 'pc4/']):
            continue

        if sub_url == dir_url:
            continue

        sub_dirs.append(sub_url)

    for sub_url in sub_dirs:
        count += process_directory(sub_url)

    return count

def get_root_dirs():
    try:
        response = requests.get(BASE_URL, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"🚨 主页访问失败: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    root_dirs = []

    for a in soup.select('a.mdui-list-item.mdui-ripple'):
        href = a.get('href', '')
        if href.startswith('/') and href.endswith('/'):
            full_url = urljoin(BASE_URL, href)
            if any(key in full_url for key in ['bu/', 's2/', 's3/', 's4/', 's5/', 'pc/', 'pc2/', 'pc3/', 'pc4/']):
                root_dirs.append(full_url)

    return root_dirs


def main():
    print("🚀 开始扫描网站结构...")
    root_dirs = get_root_dirs()
    total = 0
    if not root_dirs:
        print("⚠️ 没有抓取到根目录，默认扫描 /s2/")
        root_dirs = [f"{BASE_URL}/s2/"]

    for root_dir in root_dirs:
        print(f"\n🔍 处理根目录：{root_dir}")
        total += process_directory(root_dir)

    print(f"\n🎉 全部完成！共生成 {total} 个.strm文件")
    print(f"文件根目录：{os.path.abspath(SAVE_ROOT)}")
    return total

if __name__ == "__main__":
    main()
