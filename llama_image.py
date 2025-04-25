import base64
import requests

# 读取图片并转为 base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

# 构建请求
def analyze_image_with_llama(image_path, prompt="请描述这张图片"):
    image_base64 = encode_image_to_base64(image_path)
    url = "http://localhost:11434/api/generate"  # 默认 Ollama API 端口
    payload = {
        "model": "llama3.2-vision",
        "prompt": prompt,
        "images": [image_base64],
        "stream": False
    }
    response = requests.post(url, json=payload)
    return response.json()["response"]

# 使用示例
if __name__ == "__main__":
    result = analyze_image_with_llama("C:\\Users\\jj191\\Desktop\\11.png", prompt="please show me the mana of this card, which is the number on the top left, and the attack and life value, they are on the bottom of the card, the ledt is the attack and life is on the right side")
    print("模型输出：", result)