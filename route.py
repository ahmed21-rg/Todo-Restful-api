from flask import Flask, jsonify,request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,login_manager,UserMixin,login_user,current_user,login_required
from flask_bcrypt import Bcrypt, check_password_hash, generate_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config ['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URI")
app.config ['SECRET_KEY'] = os.getenv("SECRET_KEY")
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150), nullable=False)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))



@app.route('/register', methods=['POST'])      # creates account
def home():
    data = request.get_json()
    hashed_pw = bcrypt.generate_password_hash(data["password"]).decode('utf-8')
    new_user = User(username=data["username"], password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])     # login
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data["username"]).first()
    if user and check_password_hash(user.password, data["password"]):
        login_user(user)
        return jsonify({'message': 'Login successful'}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/get_todo', methods=['GET'])   # get all todos
@login_required
def get_todo():
    todo = Todo.query.filter_by(user_id=current_user.id).all()
    return jsonify([{'id': t.id, 'task': t.task, 'status': t.status} for t in todo]), 200     # listcomprehension to convert todos to a list of dictionaries

@app.route('/create_todo', methods=['POST'])   # create todo
@login_required
def create_todo():
    data = request.get_json()
    if not data or "task" not in data:
        return jsonify({'message': 'Task is required'}), 400
    status_value = str(data.get("status", "")).lower() in {"true", "1", "  yes"}  #str("True").lower() in ["true", "1", "yes"]
# "true" in ["true", "1", "yes"] → True ✅  str("False").lower() in ["true", "1", "yes"]
# "false" in ["true", "1", "yes"] → False ❌str(1).lower() in ["true", "1", "yes"]
# "1" in ["true", "1", "yes"] → True ✅  str("yes").lower() in ["true", "1", "yes"]   
# "yes" in ["true", "1", "yes"] → True ✅

    new_todo = Todo(task=data["task"],
                    status=status_value,
                    user_id=current_user.id
                    )    #link todo to current user
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({"id":new_todo.id, "task":new_todo.task, "status":new_todo.status}), 201

@app.route('/update_todos/<int:id>', methods=['PUT'])   # update todo
@login_required
def update_task(id):
    data = request.get_json()
    todo = Todo.query.filter_by(id=id, user_id=current_user.id).first()

    if not todo:
        return jsonify({"message": "Todo not found"}), 404

    todo.task = data.get("task", todo.task)
    todo.status = data.get("status", todo.status)
    db.session.commit()
    return jsonify({"id":todo.id, "task":todo.task, "status":todo.status}), 200

@app.route('/del_todos/<int:id>', methods=['DELETE'])   # delete todo
@login_required
def delete_task(id):
    todo = Todo.query.filter_by(id=id, user_id=current_user.id).first()

    if not todo:
        return jsonify({"message": "Todo not found"}), 404

    db.session.delete(todo)
    db.session.commit()
    return jsonify({"message": "Todo deleted successfully"}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)
