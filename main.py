from flask import Flask, redirect, request, jsonify, json
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable = False)
    amount = db.Column(db.Float, nullable = False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "amount": self.amount
        }




@app.route("/")
def home():
    return {"status": "api is running"}


@app.route("/api/expenses", methods=["GET"])
def get_expenses():
    expenses = Expense.query.all()

    return jsonify([
        expense.to_dict() for expense in expenses
    ])


@app.route("/api/expenses/<int:id>", methods=["GET"])
def get_by_id(id):
    expense = Expense.query.get_or_404(id)
    return jsonify(expense.to_dict())


@app.route("/api/expenses", methods=["POST"])
def post_expense():
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