from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


# Login checked
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("You have to sign in", "danger")
            return redirect(url_for("signin"))

    return decorated_function


# User registration form class
class RegisterForm(Form):
    name = StringField("Name Surname", validators=[validators.length(min=4, max=50), validators.DataRequired()])
    email = StringField("Email", validators=[validators.Email(message="Please, input valid email address")])
    username = StringField("User Name", validators=[validators.length(min=4, max=25)])
    password = PasswordField("Password", validators=[
        validators.DataRequired("Please, input password"),
        validators.EqualTo(fieldname="confirm", message="Password isn't match")
    ])
    confirm = PasswordField("Confirm Password")


class SignIn(Form):
    username = StringField("User Name")
    password = PasswordField("Password")


class ArticleForm(Form):
    title = StringField("Article Subject", validators=[validators.Length(min=5, max=100)])
    content = TextAreaField("Article Content", validators=[validators.length(min=10)])


app = Flask(__name__)
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "McMc4VUaEzwLviBY"
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

app.secret_key = "ybbblog"

mysql = MySQL(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/article/<string:id>")
def article(getid):

    url = "article.html"
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM ARTICLES WHERE ID = %s"
    result = cursor.execute(query, (getid,))
    if result > 0:
        articledetail = cursor.fetchone()
        return render_template(url, article=articledetail)
    else:
        return render_template(url)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        query = "INSERT INTO USERS(NAME, EMAIL, USERNAME, PASSWORD) VALUES(%s, %s, %s, %s)"
        cursor.execute(query, (name, email, username, password))
        mysql.connection.commit()
        cursor.close()
        flash("Successfully sign up", "success")

        return redirect(url_for("signin"))
    else:
        return render_template("register.html", form=form)


# Login processs
@app.route("/signin", methods=["GET", "POST"])
def signin():
    form = SignIn(request.form)

    if request.method == "POST" and form.validate():
        username = form.username.data
        password = form.password.data

        cursor = mysql.connection.cursor()
        query = "SELECT * FROM USERS WHERE USERNAME = %s"
        
        result = cursor.execute(query, (username,))
        
        if result > 0:
            data = cursor.fetchone()
            if sha256_crypt.verify(password, data["password"]):
                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))
            else:
                flash("Invalid information", "danger")
                return redirect(url_for("signin"))
        else:
            flash("No records found", "danger")
            return redirect(url_for("signin"))
    else:
        return render_template("signin.html", form=form)


@app.route("/signout")
def signout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():

    url = "dashboard.html"
    cursor = mysql.connection.cursor()

    query = "SELECT * FROM ARTICLES WHERE AUTHOR = %s"
    result = cursor.execute(query, (session["username"],))

    if result > 0:
        articlesdetail = cursor.fetchall()
        return render_template(url, articles=articlesdetail)
    else:
        return render_template(url)


@app.route("/articles")
def articles():

    url = "articles.html"
    
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM ARTICLES"
    result = cursor.execute(query)
    if result > 0:
        articles = cursor.fetchall()

        return render_template(url, articles=articles)
    else:
        return render_template(url)


# Add article
@app.route("/addarticle", methods=["GET", "POST"])
def addarticle():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO ARTICLES(TITLE, AUTHOR, CONTENT) VALUES(%s, %s, %s)"
        cursor.execute(sorgu, (title, session["username"], content))

        mysql.connection.commit()

        cursor.close()
        flash("Article added successfully", "success")

        return redirect(url_for("dashboard"))
    else:
        return render_template("addarticle.html", form=form)


@app.route("/delete/<string:id>")
@login_required
def delete(getid):
    cursor = mysql.connection.cursor()

    query = "SELECT *  FROM ARTICLES WHERE AUTHOR = %s AND ID = %s"

    result = cursor.execute(query, (session["username"], getid))

    if result > 0:
        querydelete = "DELETE FROM ARTICLES WHERE ID = %s"
        cursor.execute(querydelete, (getid,))
        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("There isn't a article or you don't have authorized", "danger")
        return redirect(url_for("index"))


@app.route("/update/<string:id>", methods=["GET", "POST"])
@login_required
def update(getid):
    
    if request.method == "GET":
        cursor = mysql.connection.cursor()

        query = "SELECT * FROM ARTICLES WHERE ID = %s AND AUTHOR = %s"
        result = cursor.execute(query, (getid, session["username"]))

        if result == 0:
            flash("There isn't a article like this or you don't have an authorized","danger")
            return redirect(url_for("index"))
        else:
            articledetail = cursor.fetchone()
            form = ArticleForm()

            form.title.data = articledetail["title"]
            form.content.data = articledetail["content"]
            return render_template("update.html", form=form)
    else:

        form = ArticleForm(request.form)
        newtitle = form.title.data
        newcontent = form.content.data

        query2 = "UPDATE ARTICLES SET TITLE = %s, CONTENT = %s WHERE ID = %s"

        cursor = mysql.connection.cursor()
        cursor.execute(query2, (newtitle, newcontent, id))
        mysql.connection.commit()
        flash("Article updated successfully","success")
        return redirect(url_for("dashboard"))


# Searching
@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()
        query = "SELECT * FROM ARTICLES WHERE TITLE LIKE '%" + keyword + "%'"
        result = cursor.execute(query)

        if result == 0:
            flash("No articles matching the searched word were found", "warning")
            return redirect(url_for("articles"))
        else:
            articlesdetail = cursor.fetchall()
            return render_template("articles.html", articles=articlesdetail)


if __name__ == "__main__":
    app.run(debug=True)

