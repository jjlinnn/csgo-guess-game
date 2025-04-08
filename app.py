from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, redirect, url_for, render_template, flash
import random, os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-for-local-dev")
# 数据库配置：Render 会自动提供 DATABASE_URL
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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

class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == "admin"

# 初始化目标选手
target_player = None

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            return "用户名已存在"
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect("/")
        return "用户名或密码错误"
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

# 注册 Flask-Admin 后台界面
admin = Admin(app, name='CSGO Admin', template_mode='bootstrap4')
admin.add_view(SecureModelView(Player, db.session))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # ✅ 如果没有 admin 用户，就创建一个默认管理员
        if not User.query.filter_by(username="admin").first():
            admin_user = User(username="admin")
            admin_user.set_password("Djj@2024!")  # 你可以改成自己密码
            db.session.add(admin_user)
            db.session.commit()
            print("✅ 管理员账号 admin/123456 已创建")
            
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

