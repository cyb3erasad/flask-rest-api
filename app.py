from flask import Flask, redirect, request, jsonify, json
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from datetime import timedelta

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "secret"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable = False)
    amount = db.Column(db.Float, nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", name="fk_expense_user"),  nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "amount": self.amount
        }
    
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable = False)
    password = db.Column(db.String(200), nullable = False)    

    __table_args__ = (db.UniqueConstraint("email", name="uq_users_email"),) 

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
        

@app.route("/api/register", methods=["POST"])
def register():
    data = request.json

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exist"}), 409
    
    user = User(email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Account created successfully"}), 201

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"message": "Invalid credentials"}), 401
    
    token = create_access_token(identity=user.id)

    return jsonify({
        "access_token": token,
        "message": "Login successfull"
    })


@app.route("/")
def home():
    return {"status": "api is running"}


@app.route("/api/expenses", methods=["GET"])
@jwt_required()
def get_expenses():
    user_id = get_jwt_identity()
    expenses = Expense.query.all()

    return jsonify([
        expense.to_dict() for expense in expenses
    ])


@app.route("/api/expenses/<int:id>", methods=["GET"])
def get_by_id(id):
    expense = Expense.query.get_or_404(id)
    return jsonify(expense.to_dict())


@app.route("/api/expenses", methods=["POST"])
@jwt_required()
def post_expense():
    user_id = get_jwt_identity()
    data = request.json
    title = data.get("title")
    amount = data.get("amount")
    
    if not title or not amount:
        return jsonify({"error": "title and amount required"}), 400 
    
    expense = Expense(title=title, amount=amount)
    db.session.add(expense)
    db.session.commit()


    return jsonify({
        "message": "Expense added",
        "expense": expense.to_dict()
        }
    ), 201


@app.route("/api/expenses/<int:id>", methods=["PUT"])
def put_expense(id):
    expense = Expense.query.get_or_404(id)

    data = request.json
    expense.title = data.get("title", expense.title)
    expense.amount = data.get("amount", expense.amount)

    db.session.commit()
    return jsonify({
        "message": "Expense update successfully",
        "expense": expense.to_dict()
    })

@app.route("/api/expenses/<int:id>", methods=["DELETE"])
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()

    return jsonify({"message": "Expense deleted successfully"})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)