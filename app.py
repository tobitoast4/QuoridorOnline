from flask import Flask, request, render_template, redirect, url_for, session, make_response, session, flash, get_flashed_messages
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from wtforms.validators import ValidationError

import database._course
from user import User

import urllib.parse
import json

from forms import RegisterForm, LoginForm, BuyNowForm, BuyForm
from database.database import *


app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config["SECRET_KEY"] = "asdf7878"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(customer_id):
    return get_customer_by_id(customer_id)  # get this data from database


@app.template_filter()
def currency_format(value):
    value = float(value)
    value = round(value, 2)
    return "{:,.2f} €".format(value).replace(".", ",")


@app.route('/')
def home():
    return redirect(url_for("shop"))


@app.route('/course')
def course():
    resp = make_response(render_template("pages/course.html"))
    courses_data_str = str(get_all_courses()).replace(" ", "").replace("'", '"')
    resp.set_cookie("courses_data", urllib.parse.quote_plus(courses_data_str))
    return resp


@app.route('/about')
def about():
    return render_template("pages/about.html")


@app.route('/shop')
def shop():
    order = request.args.get('orderBy', default="newest", type=str)  # newest, oldest, price_asc, price_desc
    search = request.args.get('search', default="", type=str)
    selected_categories = request.args.get('categories', default="", type=str)
    price = request.args.get('price', default="", type=str)

    highest_price = get_highest_product_price()
    min_value = 0
    max_value = highest_price

    if price != "":
        prices = price.split("+")
        min_value = int(prices[0])
        max_value = int(prices[1])

    silder_price_data = {
        "highest_price": highest_price,
        "min_value": min_value,
        "max_value": max_value,
        "min_value_percent": round(min_value / highest_price * 100),
        "max_value_percent": round(max_value / highest_price * 100)
    }

    # finally get the data from the database based on the given url parameters
    products = get_products_filtered(order, min_value, max_value, selected_categories, search)
    categories = get_all_product_categories()

    return render_template("pages/shop.html", products=products, categories=categories, orderBy=order,
                           search=search, selected_categories=selected_categories, silder_price_data=silder_price_data)


@app.route('/product')
def product():
    product_id = request.args.get('id', default=1, type=int)
    p = get_one_product(product_id)
    return render_template("pages/product.html", product=p)


@app.route('/cart', methods=["GET", "POST"])
def cart():
    form = BuyNowForm()
    if form.validate_on_submit():
        return redirect(url_for("buy"))
    resp = make_response(render_template("pages/cart.html", form=form, delivery_cost=DEFAULT_DELIVERY_COST))
    product_data_str = str(get_product_data_for_cart()).replace(" ", "").replace("'", '"')
    resp.set_cookie("product_data", urllib.parse.quote_plus(product_data_str))
    return resp


@app.route('/buy', methods=["GET", "POST"])
@login_required
def buy():
    form = BuyForm()
    if form.validate_on_submit():
        use_alt_delivery_address = form.use_alt_delivery_address.data
        if use_alt_delivery_address == "true":
            firstname = form.firstname.data
            lastname = form.lastname.data
            email = form.email.data
            phone = form.phone.data
            street = form.street.data
            house_number = form.house_number.data
            postal_code = form.postal_code.data
            city = form.city.data
            country = form.country.data
            state = form.state.data
            address_id = add_new_address(street, house_number, postal_code, city, country, state)
            recipient_id = add_new_recipient(firstname, lastname, email, phone, address_id)
        else:
            recipient_id = current_user.id
        current_user_id = current_user.id
        order_state_id = 1                      # TODO: CHANGE THIS
        payment_method = form.payment_method.data
        products_as_dict_str = form.products_as_dict.data

        products_as_dict_str = products_as_dict_str.replace("'", "\"")
        products_as_dict = json.loads(products_as_dict_str)
        insert_new_order(current_user_id, recipient_id, order_state_id, payment_method, products_as_dict)

        return redirect(url_for("order_finished"))
    user = get_customer_with_address_by_id(current_user.id)[0]
    print(user)
    payment_methods = get_all_payment_methods()
    resp = make_response(render_template("pages/buy.html", form=form, payment_methods=payment_methods, user=user))
    product_data_str = str(get_product_data_for_cart()).replace(" ", "").replace("'", '"')
    resp.set_cookie("product_data", urllib.parse.quote_plus(product_data_str))
    return resp


@app.route('/order_finished')
@login_required
def order_finished():
    return render_template("pages/order_finished.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        firstname = form.firstname.data
        lastname = form.lastname.data
        email = form.email.data
        if get_customer_by_email(email) is not None:
            flash(f"The email '{email}' is already in use. Please choose another one.")
            return redirect(url_for("register"))
        phone = form.phone.data
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        street = form.street.data
        house_number = form.house_number.data
        postal_code = form.postal_code.data
        city = form.city.data
        country = form.country.data
        state = form.state.data

        address_id = add_new_address(street, house_number, postal_code, city, country, state)
        add_new_customer(firstname, lastname, email, hashed_password, phone, address_id)

        flash("Sie haben sich erfolgreich registriert! Sie können sich jetzt anmelden.")
        return redirect(url_for("home"))

    return render_template("pages/register.html", form=form)


@app.route('/is_email_available', methods=["GET"])
def is_email_available():
    email = request.args.get('email')
    if get_customer_by_email(email) is not None:
        return '<div style="font-size: 13px; color: red; margin-bottom: 15px">Die eingegebene Email-Adresse wird bereits verwendet. Bitte gib eine andere ein.</div>'
    return '<div style="margin-bottom: 15px"></div>'


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    next_page = request.args.get('next')
    if "user_id" in session:
        return redirect(url_for("home"))
    if form.validate_on_submit():
        # check if user exists in db https://youtu.be/71EU8gnZqZQ?t=1615
        email = form.email.data
        user = get_customer_by_email(email)
        if user is None:
            flash(f"User with email address '{email}' does not exist.")
            return redirect(url_for("login"))
        if not bcrypt.check_password_hash(user.password, form.password.data):
            flash(f"The entered password is not correct.")
            return redirect(url_for("login"))
        session['logged_in'] = True
        session['user_id'] = user.id
        session['email'] = user.email_address
        login_user(user)
        if next_page is not None:
            return redirect(url_for(next_page[1:]))
        flash(f"Sie haben sich erfolgreich eingeloggt!")
        return redirect(url_for("home"))
    return render_template("pages/login.html", form=form)


@app.route("/logout", methods=["GET"])
def logout():
    session['logged_in'] = False
    session.pop('user_id', None)
    session.pop('email', None)
    logout_user()

    return redirect(url_for("home"))


@app.route('/profile')
@login_required
def profile():
    user = get_customer_by_id(session['user_id'])
    address = get_address_by_id(user.default_address_id)
    return render_template("pages/profile.html", user=user, address=address)


@app.route('/orders')
@login_required
def orders():
    current_user_id = current_user.id
    orders_of_user = get_customer_orders_by_customer_id(current_user_id)
    for order in orders_of_user:
        order_id = order["order_id"]
        products_of_order = get_customer_order_product_with_product_by_customer_order_id(order_id)
        order["products"] = products_of_order
        if order["recipient_id"] == order["customer_id"]:  # recipient is same as customer
            order["delivery_data"] = get_customer_with_address_by_id(order["customer_id"])[0]
        else:
            order["delivery_data"] = get_recipient_with_address_by_id(order["recipient_id"])[0]

    return render_template("pages/orders.html", orders=orders_of_user)


@app.route('/settings')
@login_required
def settings():
    return render_template("pages/settings.html")


if __name__ == '__main__':
    # app.run(host="0.0.0.0") # use me for prod
    app.run(host="127.0.0.1", port=5009, debug=True)