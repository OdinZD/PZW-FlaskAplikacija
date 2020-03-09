import os
from flask import Flask, render_template, url_for, session, request, redirect, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email
from forms import Login_Form, Register_Form
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3


# Potrebno za kreiranje baze
def create_app():
    basedir = os.path.abspath(os.path.dirname(__file__))
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'ovojetajnikljuc!'

    Bootstrap(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
        os.path.join(basedir, 'data.sqlite')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    return app


app = create_app()

db = SQLAlchemy(app)


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    bought = db.Column(db.Text())

    def __repr__(self):
        return '{}, {}, {}'.format(self.username, self.email, self.password, self.bought)


class Products(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text(), unique=True)
    price = db.Column(db.Integer())
    description = db.Column(db.Text())

    def __repr__(self):
        return '{}, {}, {}'.format(self.name, self.price, self.description)


@app.route('/', methods=['GET'])
def index():
    products = Products.query.all()
    return render_template('index.html', products=products)

#
@app.route('/add/<int:id>', methods=['GET', 'POST'])
def addToCart(id):

    temp_product = []

    if session.get('cart') is None or session.get('cart') == []:
        cart = []
    else:
        cart = session.get('cart')

    if request.method == 'GET' and session.get('user') is None:
        flash('You have to login first!')
        return redirect(url_for('login'))
    elif request.method == 'GET' and session.get('user') is not None:
        product = Products.query.get(id)
        # Lista proizvoda bez descriptiona
        temp_product.append(product.name)
        temp_product.append(product.price)

        cart.append(temp_product)
        session['cart'] = cart

        flash('You successfully added ' + product.name + ' into cart!')

        return redirect(url_for('index'))


@app.route('/remove/<int:id>', methods=['GET'])
def removeFromCart(id):

    cart = session.get('cart')

    if request.method == 'GET' and session.get('user') is None:
        return redirect(url_for('index'))
    elif request.method == 'GET' and session.get('user') is not None:
        del cart[id]
        session['cart'] = cart
        return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = Login_Form()
    users = Users.query.all()

    if request.method == 'GET' and session.get('user') is None:
        return render_template('login.html', form=form)
    elif request.method == 'GET' and session.get('user') is not None:
        return redirect(url_for('index'))

    elif request.method == 'POST' and form.validate_on_submit():
        #radi iteraciju kroz usere i provjerava prvo username pa password
        for i in users:
            if i.username == form.username.data:
                if check_password_hash(i.password, form.password.data):
                    session['user'] = form.username.data
                    flash('Welcome ' + form.username.data)
                    return redirect(url_for('index'))
                else:
                    flash('Wrong username or password!')
                    return redirect(url_for('login'))
            #ako ne postoji username prelazi na sljedeceg usera
            else:
                continue

    flash('There is no user with that username!')
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'GET' and session.get('user') is None:
        return render_template('login.html')
    elif request.method == 'GET' and session.get('user') is not None:
        session['user'] = None
        session['cart'] = []
        return redirect(url_for('index'))


@app.route('/cart', methods=['GET', 'POST'])
def cart():

    cart = session.get('cart')

    if request.method == 'GET' and session.get('user') is not None:
        return render_template('cart.html', cart=cart)
    elif request.method == 'GET' and session.get('user') is None:
        return redirect(url_for('index'))


@app.route('/checkout', methods=['GET'])
def checkout():

    # za update
    conn = sqlite3.connect('data.sqlite')

    users = Users.query.all()
    cart = session.get('cart')
   

    if request.method == 'GET' and session.get('user') is None:
        return redirect(url_for('index'))
    elif request.method == 'GET' and session.get('user') is not None:
        for i in users:
            if i.username == session.get('user'):
                userId = users.index(i) + 1
                #provjerava dali postoji išta kod tog usera kupljeno
                if i.bought == None:
                    sql = 'UPDATE users SET bought = ? WHERE users.id = ?'
                    cur = conn.cursor()
                    cur.execute(sql, (str(cart), userId))
                else:
                    #pretvara string u aray i ponovo ga zapise
                    oldBought = eval(i.bought)
                    for i in cart:
                        oldBought.append(i)
                    sql = 'UPDATE users SET bought = ? WHERE users.id = ?'
                    cur = conn.cursor()
                    cur.execute(sql, (str(oldBought), userId))

                conn.commit()
                session['cart'] = []
                flash('Thank you for your purchase!')
                cur.close()
                return redirect(url_for('index'))


@app.route('/purchases', methods=['GET'])
def purchases():
    users = Users.query.all()
    if request.method == 'GET' and session.get('user') is None:
        return redirect(url_for('login'))
    elif request.method == 'GET' and session.get('user') is not None:
        for i in users:
            if i.username == session.get('user'):
                if i.bought == None:
                    return render_template('purchases.html', items=[])
                else:
                    items = eval(i.bought)
                    return render_template('purchases.html', items=items)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = Register_Form()

    if request.method == 'GET' and session.get('user') is None:
        return render_template('signup.html', form=form)
    elif request.method == 'GET' and session.get('user') is not None:
        return redirect(url_for('index'))
    elif request.method == 'POST' and form.validate_on_submit():
        new_user = Users(username=form.username.data, email=form.email.data,
                         password=generate_password_hash(form.password.data))
        try: #prokušava zapisati usera
            db.session.add(new_user)
            db.session.commit()
            session['user'] = form.username.data
            flash('Your registration was successful!')
            return redirect(url_for('index'))
        except exc.IntegrityError as e:
            db.session().rollback()
            flash('There is already user with that username!')
            return redirect(url_for('signup'))


