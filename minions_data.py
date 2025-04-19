import requests
from bs4 import BeautifulSoup
import os

url = "https://battlegrounds.gamerhub.cn/cards"  # 比如页面引用了很多图片
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

save_dir = "all_downloaded_images"
os.makedirs(save_dir, exist_ok=True)

for img_tag in soup.find_all('img'):
    img_url = img_tag.get('src')
    if img_url and "all_images/32.0.3.219197" in img_url:
        full_url = "https://battlegrounds.gamerhub.cn/cards/" + img_url if img_url.startswith("/") else img_url
        filename = os.path.join(save_dir, full_url.split("/")[-1])
        print("下载:", full_url)
        img_data = requests.get(full_url).content
        with open(filename, 'wb') as f:
            f.write(img_data)
