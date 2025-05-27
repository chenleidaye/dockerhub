import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, urljoin, urlparse, parse_qs

BASE_URL = "https://5721004.xyz"
SAVE_ROOT = "strm_files"
os.makedirs(SAVE_ROOT, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": BASE_URL
}

visited_dirs = set()

def should_update_file(file_path, new_content):
    """检查是否需要更新文件"""
    if not os.path.exists(file_path):
        return True
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip() != new_content.strip()
    except UnicodeDecodeError:
        return True

def get_real_url(m3u8_url):
    """解析真实播放地址"""
    parsed_url = urlparse(m3u8_url)
    query_dict = parse_qs(parsed_url.query)
    
    if 'path' in query_dict:
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        real_path = query_dict['path'][0]
        return urljoin(base_url + "/", real_path.lstrip('/'))
    return m3u8_url

def url_to_local_path(url):
    """将URL转换为本地路径"""
    parsed = urlparse(url)
    path_segments = [seg for seg in unquote(parsed.path).split('/') if seg and seg != '?']
    
    # 处理查询参数
    if parsed.query:
        query_segments = [seg for seg in unquote(parsed.query).split('/') if seg]
        path_segments.extend(query_segments)
    
    # 定位关键目录
    season_keys = {'bu', 's2', 's3', 's4', 's5', 'pc', 'pc2', 'pc3', 'pc4'}
    start_idx = next((i for i, seg in enumerate(path_segments) if seg.lower() in season_keys), 0)
    
    return os.path.join(SAVE_ROOT, *path_segments[start_idx:])

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
    
    count = 0
    if m3u8_files:
        local_dir = url_to_local_path(dir_url)
        os.makedirs(local_dir, exist_ok=True)
        print(f"\n📂 进入目录：{dir_url} -> 本地目录：{local_dir}")
        
        for strm_filename, m3u8_url in m3u8_files:
            strm_path = os.path.join(local_dir, strm_filename)
            real_url = get_real_url(m3u8_url)
            
            if should_update_file(strm_path, real_url):
                with open(strm_path, "w", encoding="utf-8") as f:
                    f.write(real_url)
                action = "✅ 更新" if os.path.exists(strm_path) else "🆕 新建"
                print(f"{action}：{strm_filename}")
                count += 1
            else:
                print(f"⏩ 跳过未变化：{strm_filename}")
        
        print(f"📥 本目录共处理 {count} 个视频")
    
    # 处理子目录
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
        
        if any(href.lower().endswith(ext) for ext in ['.m3u8', '.md', '.txt', '.jpg']):
            continue
        
        if any(key in sub_url for key in ['bu/', 's2/', 's3/', 's4/', 's5/', 'pc/']):
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
            if any(key in full_url for key in ['bu/', 's2/', 's3/', 's4/', 's5/', 'pc/', 'pc2/']):
                root_dirs.append(full_url)
    
    return root_dirs

if __name__ == "__main__":
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
