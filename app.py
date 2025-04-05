from flask import Flask, render_template, request, jsonify
import json, random

app = Flask(__name__)

# 加载选手数据
with open("data/players.json", "r") as f:
    PLAYERS = json.load(f)

# 随机选择一个目标选手
target_player = random.choice(PLAYERS)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/players")
def get_players():
    names = [p["name"] for p in PLAYERS]
    return jsonify(names)

@app.route("/restart", methods=["POST"])
def restart():
    global target_player
    target_player = random.choice(PLAYERS)
    return jsonify({"message": "New game started."})

@app.route("/guess", methods=["POST"])
def guess():
    data = request.get_json()
    guess_name = data.get("guess", "").strip().lower()

    guessed_player = next((p for p in PLAYERS if p["name"].lower() == guess_name), None)

    if not guessed_player:
        return jsonify({"result": "未找到该选手，请再试一次。"})

    feedback = {}

    def compare(field):
        if guessed_player[field] == target_player[field]:
            return "correct"
        elif guessed_player[field] > target_player[field]:
            return "down"
        else:
            return "up"

    feedback["age"] = compare("age")
    feedback["majors"] = compare("majors")
    feedback["region"] = "correct" if guessed_player["region"] == target_player["region"] else "wrong"

    result_text = "🎉 恭喜你猜对了！" if guessed_player["name"].lower() == target_player["name"].lower() else "继续努力！"

    return jsonify({
        "result": result_text,
        "feedback": feedback,
        "player": guessed_player,
        "correct": guessed_player["name"].lower() == target_player["name"].lower()
    })
@app.route("/add_player", methods=["POST"])
def add_player():
    new_player = request.get_json()

    # 加载当前数据
    with open("data/players.json", "r") as f:
        players = json.load(f)

    # 添加新数据
    players.append(new_player)

    # 写入文件
    with open("data/players.json", "w") as f:
        json.dump(players, f, indent=2)

    return jsonify({"message": f"成功添加选手：{new_player['name']}"})


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
