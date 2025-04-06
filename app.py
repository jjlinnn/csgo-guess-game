from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import random, os

app = Flask(__name__)

# 数据库配置：Render 会自动提供 DATABASE_URL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 数据模型：选手表
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    team = db.Column(db.String(80))
    region = db.Column(db.String(50))
    flag = db.Column(db.String(10))
    age = db.Column(db.Integer)
    role = db.Column(db.String(50))
    majors = db.Column(db.Integer)

# 初始化目标选手
target_player = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/players")
def get_players():
    # 用于自动补全
    names = [p.name for p in Player.query.all()]
    return jsonify(names)

@app.route("/restart", methods=["POST"])
def restart():
    global target_player
    players = Player.query.all()
    if not players:
        return jsonify({"message": "数据库中没有选手数据，请先添加选手。"})
    target_player = random.choice(players)
    return jsonify({"message": "新游戏开始"})

@app.route("/guess", methods=["POST"])
def guess():
    global target_player
    data = request.get_json()
    guess_name = data.get("guess", "").strip().lower()

    guessed_player = Player.query.filter(
        db.func.lower(Player.name) == guess_name
    ).first()

    if not guessed_player:
        return jsonify({"result": "未找到该选手，请再试一次。"})

    if not target_player:
        return jsonify({"result": "请先点击再玩一把开始新游戏。"})

    # 比较逻辑
    def compare(field):
        guessed = getattr(guessed_player, field)
        target = getattr(target_player, field)
        if guessed == target:
            return "correct"
        elif guessed > target:
            return "down"
        else:
            return "up"

    feedback = {
        "age": compare("age"),
        "majors": compare("majors"),
        "region": "correct" if guessed_player.region == target_player.region else "wrong"
    }

    result_text = "🎉 恭喜你猜对了！" if guessed_player.name.lower() == target_player.name.lower() else "继续努力！"

    return jsonify({
        "result": result_text,
        "feedback": feedback,
        "player": {
            "name": guessed_player.name,
            "team": guessed_player.team,
            "region": guessed_player.region,
            "flag": guessed_player.flag,
            "age": guessed_player.age,
            "role": guessed_player.role,
            "majors": guessed_player.majors
        },
        "correct": guessed_player.name.lower() == target_player.name.lower()
    })

@app.route("/add_player", methods=["POST"])
def add_player():
    data = request.get_json()
    new_player = Player(
        name=data["name"],
        team=data["team"],
        region=data["region"],
        flag=data["flag"],
        age=data["age"],
        role=data["role"],
        majors=data["majors"]
    )
    db.session.add(new_player)
    db.session.commit()
    return jsonify({"message": f"已添加 {new_player.name}!"})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
