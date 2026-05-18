from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json

app = Flask(__name__)
app.secret_key = 'test-secret-key-123'

# 模拟数据库
products = [
    {"id": 1, "name": "iPhone 16", "price": 7999, "stock": 10},
    {"id": 2, "name": "MacBook Pro", "price": 14999, "stock": 5},
    {"id": 3, "name": "AirPods Pro", "price": 1999, "stock": 20},
    {"id": 4, "name": "iPad Air", "price": 4999, "stock": 8},
]

users = {
    "admin": {"password": "123456", "name": "管理员"},
    "test": {"password": "test123", "name": "测试用户"},
}

cart = {}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = users.get(username)
        if user and user["password"] == password:
            session["username"] = username
            session["name"] = user["name"]
            return redirect(url_for("products_list"))
        else:
            return render_template("login.html", error="用户名或密码错误")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))


@app.route("/products")
def products_list():
    return render_template("products.html", products=products)


@app.route("/cart")
def show_cart():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("cart.html", cart=cart)


@app.route("/api/cart/add", methods=["POST"])
def add_to_cart():
    if "username" not in session:
        return jsonify({"error": "请先登录"}), 401
    data = request.json
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    
    for p in products:
        if p["id"] == product_id:
            if p["stock"] < quantity:
                return jsonify({"error": "库存不足"}), 400
            if product_id not in cart:
                cart[product_id] = {"product": p, "quantity": 0}
            cart[product_id]["quantity"] += quantity
            return jsonify({"message": "已加入购物车"})
    return jsonify({"error": "商品不存在"}), 404


@app.route("/api/cart/get")
def get_cart():
    return jsonify({"items": list(cart.values())})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
