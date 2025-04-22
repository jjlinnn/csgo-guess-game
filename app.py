from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, redirect, url_for, render_template, flash
from flask_admin.contrib.sqla import ModelView
from flask_migrate import Migrate
import random, os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-for-local-dev")
# 数据库配置：Render 会自动提供 DATABASE_URL
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
#app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://jiajiedeng:kY08mwmlzh60lMoNbSqtNCvGQEzMB02J@dpg-cvp7idvgi27c73b1143g-a.oregon-postgres.render.com/csgo_d1t4"


db = SQLAlchemy(app)
migrate = Migrate(app, db)  

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, default=0)


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 数据模型：选手表
class Player(db.Model):  # 🔄 改名也可以保留 Player 不动，只改字段
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)  # 卡牌名称
    mana = db.Column(db.Integer)      # 本数
    attack = db.Column(db.Integer)    # 攻击力
    health = db.Column(db.Integer)    # 血量
    tribe = db.Column(db.String(50)) 

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
    return db.session.get(User, int(user_id))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/all_minions")
def all_minions():
    players = Player.query.order_by(Player.mana.asc()).all()
    result = [
        {
            "name": p.name,
            "mana": p.mana,
            "attack": p.attack,
            "health": p.health
        }
        for p in players
    ]
    return jsonify(result)

@app.route("/players")
def get_players():
    keyword = request.args.get("q", "").lower()
    if keyword:
        # 模糊匹配 SQL：名字中包含关键字即可
        results = Player.query.filter(Player.name.ilike(f"%{keyword}%")).all()
    else:
        results = Player.query.limit(50).all()  # 没有关键词就返回最多 50 个

    names = [p.name for p in results]
    return jsonify(names)


@app.route("/restart", methods=["POST"])
def restart():
    global target_player
    players = Player.query.all()
    target_player = random.choice(players)
    session["guess_count"] = 0  # ✅ 重置计数器
    return jsonify({"message": "新游戏开始"})

@app.route("/guess", methods=["POST"])
def guess():
    global target_player
    data = request.get_json()
    guess_name = data.get("guess", "").strip().lower()

    if "guess_count" not in session:
        session["guess_count"] = 0

    session["guess_count"] += 1
    guess_count = session["guess_count"]

    guessed_player = Player.query.filter(
        db.func.lower(Player.name) == guess_name
    ).first()

    if not guessed_player:
        return jsonify({"result": "未找到该选手，请再试一次。", "guess_count": guess_count})

    if not target_player:
        return jsonify({"result": "请先点击再玩一把开始新游戏。"})

    is_correct = guessed_player.name.lower() == target_player.name.lower()

    # === 如果猜对了，立刻返回正确结果 + 加积分 ===
    if is_correct:
        if current_user.is_authenticated:
            current_user.score = (current_user.score or 0) + 1
            db.session.commit()


        return jsonify({
            "result": "🎉 恭喜你猜对了！",
            "feedback": {
                "age": "correct",
                "majors": "correct",
                "region": "correct"
            },
            "player": {
                "name": guessed_player.name,
                "mana": guessed_player.mana,
                "attack": guessed_player.attack,
                "health": guessed_player.health,
                "tribe": guessed_player.tribe
            },
            "correct": True,
            "guess_count": guess_count,
            "game_over": True
        })

    # === 没猜中时构造提示 ===
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
        "mana": compare("mana"),
        "attack": compare("attack"),
        "health": compare("health")
    }

    # === 如果是第8次，强制游戏结束并公布答案 ===
    if guess_count >= 8:
        return jsonify({
            "result": f"😢 猜了 8 次都没猜中！正确答案是：{target_player.name}",
            "feedback": feedback,
            "player": {
                "name": guessed_player.name,
                "mana": guessed_player.mana,
                "attack": guessed_player.attack,
                "health": guessed_player.health,
                "tribe": guessed_player.tribe
            },
            "correct": False,
            "guess_count": guess_count,
            "game_over": True
        })

    # === 还可以继续猜 ===
    return jsonify({
        "result": "继续努力！",
        "feedback": feedback,
        "player": {
                "name": guessed_player.name,
                "mana": guessed_player.mana,
                "attack": guessed_player.attack,
                "health": guessed_player.health,
                "tribe": guessed_player.tribe
            },
        "correct": False,
        "guess_count": guess_count,
        "game_over": False
    })

@app.route("/add_player", methods=["POST"])
def add_player():
    data = request.get_json()
    new_player = Player(
        name=data["name"],
        mana=data["mana"],
        attack=data["attack"],
        health=data["health"],
        tribe=data["tribe"]
    )
    db.session.add(new_player)
    db.session.commit()
    return jsonify({"message": f"已添加 {new_player.name}!"})

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

# 注册 Flask-Admin 后台界面
admin = Admin(app, name='CSGO Admin', template_mode='bootstrap4')
admin.add_view(SecureModelView(Player, db.session))
admin.add_view(SecureModelView(User, db.session))
if __name__ == "__main__":
    with app.app_context():

        #db.drop_all()
        #db.create_all()
        try:
            db.session.execute('ALTER TABLE "user" ADD COLUMN score INTEGER DEFAULT 0;')
            db.session.commit()
            print("✅ 已添加 score 字段")
        except:
            print("⚠️ score 字段可能已存在，跳过")
        # ✅ 如果没有 admin 用户，就创建一个默认管理员
        if not User.query.filter_by(username="admin").first():
            admin_user = User(username="admin")
            admin_user.set_password("Djj@2024!")  # 你可以改成自己密码
            db.session.add(admin_user)
            db.session.commit()
            print("✅ 管理员账号 admin/123456 已创建")
            
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

