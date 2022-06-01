
from flask import Flask,render_template,request,flash,redirect,url_for,session,logging
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from flask_mail import Mail,Message
from forms import AddForm
from werkzeug.utils import secure_filename
import os 

app = Flask(__name__)

app.config["MYSQL_HOST"] = 'localhost'
app.config["MYSQL_USER"] = 'root'
app.config["MYSQL_PASSWORD"] = ''
app.config["MYSQL_DB"] = 'store'
app.config["MYSQL_CURSORCLASS"] = 'DictCursor'
# mail
app.config["MAIL_SERVER"] = ''
app.config["MAIL_PORT"] = 
app.config["MAIL_USERNAME"]=''
app.config["MAIL_PASSWORD"] = ''
app.config['MAIL_USE_TLS'] = False
app.config["MAIL_USE_SSL"] = True
# for uploding file
app.config["UPLOAD_FOLDER"]='static/files'

mail = Mail(app)
ALLOWED_EXTENSION = ["png","jpeg","jpg"]


mysql = MySQL(app)

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
            session['logged_in'] = True
            session['email'] = email

            flash('You are now logged in','success')
            return redirect(url_for('verify'))
        else:
            error = 'Invalid Login'
            return render_template('adminlogin.html',error = error)
        cur.close()
    else:
        error = "Email not found"
        return render_template('adminlogin.html',error = error)

@app.get('/verify')
def verify():
    flash("Please verify your email to process to the admin","success")
    msg = Message(subject="Verification",sender="thinklik123@gmail.com",recipients=[session['email']])
    msg.body = f"Verification link {request.url_root}verify/{session['email']}"
    return render_template('adminlogin.html')

@app.get('/verify/<string:email>')
def check_email(email):
    # Create cursor
    cur = mysql.connection.cursor()

        # get user by username
    result = cur.execute("SELECT * FROM users WHERE email = %s",[email])
    if result > 0 :
        # get stored hash
        activate = 1
        cur.execute("UPDATE users SET verified = %s WHERE email = %s",(activate,email))
    else:
        msg = 'No Data Found'
        return msg
    mysql.connection.commit()
    cur.close()
    flash('Your account is successfully verified','success')
    return redirect(url_for('home'))

@app.get('/home')
def home():
    return render_template('home.html')

@app.get("/logout")
def logout():
    cur = mysql.connection.cursor()
    deactivate = 0
    cur.execute("UPDATE users SET verified = %s WHERE email = %s",(deactivate,session['email']))
    mysql.connection.commit()
    cur.close()
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('admin_login'))

@app.get('/form')
def order_form():
    return render_template('order.html')

@app.get("/product")
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

@app.get('/hehe')
def hehe():
    return "pumasok"
if __name__ == "__main__":
    app.secret_key = sha256_crypt.hash("Vinthrift")
    app.run(debug=True)
    