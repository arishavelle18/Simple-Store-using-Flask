
from ast import arg
from flask import Flask,render_template,request,flash,redirect,url_for,session,logging,jsonify
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from flask_mail import Mail,Message
from forms import AddForm
from werkzeug.utils import secure_filename
import os 
from chat import get_response
from random import randint
from functools import wraps

app = Flask(__name__)

app.config["MYSQL_HOST"] = 'localhost'
app.config["MYSQL_USER"] = 'root'
app.config["MYSQL_PASSWORD"] = ''
app.config["MYSQL_DB"] = 'store'
app.config["MYSQL_CURSORCLASS"] = 'DictCursor'
# mail
app.config["MAIL_SERVER"] = ''
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"]=''
app.config["MAIL_PASSWORD"] = ''
app.config['MAIL_USE_TLS'] = False
app.config["MAIL_USE_SSL"] = True
# for uploding file
app.config["UPLOAD_FOLDER"]='static/files'

mail = Mail(app)
ALLOWED_EXTENSION = ["png","jpeg","jpg"]
otp = randint(000000,999999)

mysql = MySQL(app)

# check if the user is logged in 
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('Unauthorized, Please login','danger')
            return redirect(url_for('index_get'))
    return wrap


@app.get("/admin_login")
def admin_login():
    return render_template("adminlogin.html")

@app.post("/validate")
def login_validate():
    
    email = request.form['email']
    password_candidate = request.form['password']

        # Create cursor
    cur = mysql.connection.cursor()

        # get user by username
    result = cur.execute("SELECT * FROM users WHERE email = %s",[email])

    if result > 0 :
        # get stored hash
        data = cur.fetchone()
        password = data['password']
        

        # compare passwords
        if password_candidate == password:
            # session['logged_in'] = True
            # session['email'] = email

            # flash('You are now logged in','success')
            # return redirect(url_for('verify'))
            flash("We send code to your email to verify and proceed to the admin","success")
            msg = Message(subject="Verification",sender="thinklik123@gmail.com",recipients=[email])
            cur.execute("UPDATE users SET code = %s WHERE email = %s",(otp,email))
            msg.body = f"Verification code is {otp}"
            mysql.connection.commit()
            cur.close()
            return render_template('otp.html',data =email)
        else:
            error = 'Invalid Login'
            return render_template('adminlogin.html',error = error)
        cur.close()
    else:
        error = "Email not found"
        return render_template('adminlogin.html',error = error)



@app.post('/verify')
def verify():
    email = request.form["email"]
    otp = request.form["otp"]
           # Create cursor
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM users WHERE email = %s AND code = %s",(email,otp))
    if result == 0:
        flash("Code is wrong please try again","danger")
        return render_template('otp.html',data = email)
    flash("Login successfully","success")
    session['logged_in'] = True
    session['email'] = email
    activate = 1
    cur.execute("UPDATE users SET verified = %s WHERE email = %s",(activate,email))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for("home"))


@app.get('/home')
@is_logged_in
def home():
    return render_template('home.html')

@app.get("/logout")
@is_logged_in
def logout():
    cur = mysql.connection.cursor()
    deactivate = 0
    cur.execute("UPDATE users SET verified = %s WHERE email = %s",(deactivate,session['email']))
    mysql.connection.commit()
    cur.close()
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('admin_login'))


@app.get("/product")
@is_logged_in
def product():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM product")
    if result > 0:
        data = cur.fetchall()
        return render_template("product.html",data = data)
    return render_template("product.html")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSION

@app.route("/add_product",methods=["GET","POST"])
@is_logged_in
def add_product():
    if request.method == "POST":
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == "" :
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            name = request.form["name"]
            price = request.form["price"]
            size = request.form["size"]
            file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cur = mysql.connection.cursor()
            
            cur.execute("INSERT INTO product(product_name,product_price,product_size,product_image) VALUES(%s,%s,%s,%s)",(name,price,size,file))

            mysql.connection.commit()
            # close the fucking connection
            cur.close()

            return redirect(url_for("product"))

    return render_template("addproduct.html")

@app.get("/delete/<string:id>")
@is_logged_in
def delete_product(id):
    # Create cursor
    cur = mysql.connection.cursor()

        # get user by username
    result = cur.execute("SELECT * FROM product WHERE id = %s",[id])
    # check if yyou can delete it or not
    if result > 0:
        cur.execute("DELETE FROM product WHERE id = %s",[id])
        mysql.connection.commit()
        cur.close()
        flash("Product is successfully deleted","success")
        return redirect(url_for("product"))
    else:
        flash("Product is not found","danger")
        return redirect(url_for("product"))
        cur.close()

@app.get("/edit/<string:id>")
@is_logged_in
def edit_product(id):
    cur = mysql.connection.cursor()
        # get user by id
    result = cur.execute("SELECT * FROM product WHERE id = %s",[id])
      # check if yyou can delete it or not
    if result > 0:
        data = cur.fetchone()
        cur.close()
        return render_template("edit_product.html",data = data )
    else:
        flash("Product is not found","danger")
        return redirect(url_for("product"))
        cur.close()

@app.post("/update/<string:id>")
def update_product(id):
     name = request.form["name"]
     price = request.form["price"]
     size = request.form["size"]
     cur = mysql.connection.cursor()
     cur.execute("UPDATE product SET product_name = %s,product_price = %s, product_size = %s WHERE id = %s",(name,price,size,id))
     flash("Product is successfully update","success")
     mysql.connection.commit()
     cur.close()
     return redirect(url_for("product"))
     
@app.get('/form')
def form_buy():
    cur = mysql.connection.cursor()
    # get user by id
    cur.execute("SELECT * FROM product")
    data = cur.fetchall()
    return render_template("buy.html",data = data)

@app.post('/order_verify')
def order_verify():
    name = request.form['name']
    address = request.form['address']
    contact = request.form['contact']
    mode = request.form['mode']
    product_name = request.form['product_name']
    size = request.form['size']
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM product WHERE product_name = %s AND product_size = %s",(product_name,size))
    
    if result == 0 :
        flash("Size is not available","danger")
        return redirect(url_for("form_buy"))
    if mode == "" or product_name == "" or size == "":
        flash("Empty Field is not allowed","danger")
        return redirect(url_for("form_buy"))

    cur.execute("INSERT INTO orders(name,address,contact,mode,product_order,size) VALUES(%s,%s,%s,%s,%s,%s)",(name,address,contact,mode,product_name,size))

    mysql.connection.commit()
    # close the fucking connection
    cur.close()
    flash("Order Successfully","success")
    return redirect(url_for("index_get"))

@app.get("/pending")
@is_logged_in
def pending_list():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM orders WHERE type = %s",["pending"])
    if result > 0:
        data = cur.fetchall()
        cur.close()
        return render_template("pending.html",data = data)
    cur.close()
    return render_template("pending.html")

@app.get("/trash")
@is_logged_in
def trash_list():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM orders WHERE type = %s",["trash"])
    if result > 0:
        data = cur.fetchall()
        cur.close()
        return render_template("trash.html",data = data)
    cur.close()
    return render_template("trash.html")

@app.get("/confirm")
@is_logged_in
def confirm_list():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM orders WHERE type = %s",["confirm"])
    if result > 0:
        data = cur.fetchall()
        cur.close()
        return render_template("confirm.html",data = data)
    cur.close()
    return render_template("confirm.html")

@app.get("/change_list/<string:id>/<string:type>")
@is_logged_in
def change_list(id,type):
    cur = mysql.connection.cursor()
        # get user by id
    result = cur.execute("SELECT * FROM orders WHERE id = %s",[id])
      # check if yyou can delete it or not
    if result == 0:
        flash("Failed to connect","danger")
        return redirect(url_for("home"))
    cur.execute("UPDATE orders SET type = %s WHERE id = %s",(type,id))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for(f"{type}_list"))

@app.get("/delete_permanently/<string:id>")
@is_logged_in
def delete_permanently(id):
    # Create cursor
    cur = mysql.connection.cursor()

        # get user by username
    result = cur.execute("SELECT * FROM orders WHERE id = %s",[id])
    # check if yyou can delete it or not
    if result > 0:
        cur.execute("DELETE FROM orders WHERE id = %s",[id])
        mysql.connection.commit()
        cur.close()
        flash("Order is successfully deleted","success")
        return redirect(url_for("trash_list"))
    else:
        flash("Order is not found","danger")
        return redirect(url_for("trash_list"))
        cur.close()

@app.get('/')
def index_get():
    return render_template("chat.html")


@app.post("/predict")
def predict():
    text = request.form["message"]
    # TODO : check if text is valid
    response = get_response(text)
    message = {"answer":response}
    return jsonify(message)

if __name__ == "__main__":
    app.secret_key = sha256_crypt.hash("Vinthrift")
    app.run(debug=True)
    