from flask import Flask, render_template, request, session, redirect ,url_for, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
from werkzeug.utils import secure_filename
import os
from random import randint
from datetime import datetime, timedelta
app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'user_system'

mysql = MySQL(app)

app.secret_key ='111'

@app.route("/")
@app.route('/login' , methods = ['GET','POST'])
def login():
    text = ''
   
    if request.method == 'POST' and 'USERNAME' in request.form and 'PASSWORD' in request.form:
        
        name = request.form['USERNAME']
        password = request.form['PASSWORD']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE name = %s AND password = %s ', (name,password))
        user = cursor.fetchone()
        
        if user:
            u_id = user["userid"]
            cursor.execute('SELECT * FROM roles_table WHERE user_id = %s',(u_id,))
            u_role = cursor.fetchone()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if u_role:
                if u_role["role_name"] == "admin":
                    print("Admin log in successfull")
                    session['loggedin'] = True
                    session['userid'] = user['userid']
                    session['name'] = user['name']
                    session['imgsource'] = user['imgsource']
                    cursor.execute('INSERT INTO sessions_table(sessions_id,user_id,login_time) VALUES(NULL,%s,%s)',(u_id,now))
                    mysql.connection.commit()
                    return render_template("/admin.html")        
                elif u_role["role_name"] == "user":
                    session['loggedin'] = True
                    session['userid'] = user['userid']
                    session['name'] = user['name']
                    session['imgsource'] = user['imgsource']
                    cursor.execute('INSERT INTO sessions_table(sessions_id,user_id,login_time) VALUES(NULL,%s,%s)',(u_id,now))
                    mysql.connection.commit()
                    return render_template("user.html")
        else:
            return render_template("login.html", text = "incorrect login details")
    elif request.method == 'POST' and 'name' in request.form and 'password' in request.form :
        name = request.form['name']  
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE name = %s',(name,))
        userData = cursor.fetchone()
        if userData:
            text = "Account Exists"
        elif not name or not password:
            text = "ALL FIELDS REQUIRED"
        else:
            cursor.execute('INSERT INTO user VALUES(NULL,%s,%s,%s)',(name,password,"1.jpeg"))
            cursor.execute('SELECT userid FROM user WHERE name=%s',(name,))
            new_user = cursor.fetchone()
            u__id = new_user["userid"]
            cursor.execute('INSERT INTO roles_table VALUES(NULL,%s,%s)',(u__id,"user"))
            mysql.connection.commit()

            session['name'] = name
            return render_template("uploader.html")       
    return render_template("login.html",text = text)


@app.route("/logout")
def logout():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("UPDATE sessions_table SET logout_time = %s WHERE user_id = %s",(now,session['userid']))
    mysql.connection.commit()
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('name', None)
    session.pop('imgsource', None)
    return redirect(url_for('login'))


UPLOAD_FOLDER = './static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    if request.method == 'POST':
        if 'file1' not in request.files:
            return 'there is no file1 in form!'
        file1 = request.files['file1']
        cursor = mysql.connection.cursor()
        file1.filename = str(session['name'])+".jpeg"
        newName= file1.filename
        path = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
        file1.save(path)
        cursor.execute('UPDATE user SET imgsource = %s WHERE name = %s',(newName,session['name']))
        mysql.connection.commit()
        return render_template("login.html")
    return render_template("uploader.html")

@app.route("/admin", methods = ['GET','POST'])
def admin():
    if 'loggedin' in session:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM user')
            users = cursor.fetchall()
            cursor.execute('SELECT * FROM roles_table')
            u_roles = cursor.fetchall()
            return render_template("admin.html", users = users, u_roles = u_roles)
    return redirect(url_for('user'))

@app.route("/deleteuser", methods =['GET','POST'])
def deleteuser():
    userrole = request.args.get('role')
    username = request.args.get('username')
    if userrole == 'admin':
        flash("ADMIN USER CAN'T BE DELETED")
        return redirect(url_for('admin'))
    else:
        userid = request.args.get('userid')
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO deleted_users VALUES(NULL,%s,%s,%s)',(userid,username,now))
        cursor.execute('DELETE FROM user WHERE userid = %s',(userid,))
        cursor.execute('DELETE FROM roles_table WHERE user_id = %s',(userid,))
        mysql.connection.commit()
    return redirect(url_for('admin'))

@app.route("/changepassword", methods=['GET','POST'])
def changepassword():
    if 'loggedin' in session:
        userrole = request.args.get('role')
        userid = request.args.get('userid')
        if userrole == "admin":
            flash("ADMIN PASSWORD CAN'T BE CHANGED")
            return redirect(url_for('admin'))
        elif request.method == 'POST' and 'PASSWORD' in request.form:
            passw = request.form['PASSWORD']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE user SET password = %s WHERE userid = %s',(passw,userid))
            mysql.connection.commit()
            return redirect(url_for('admin'))
        return render_template("changepassword.html",userid = userid)
    
    return redirect(url_for('admin'))

@app.route("/useredit",methods = ['GET','POST'])
def useredit():
    text =''
    if 'loggedin' in session:
        userrole = request.args.get('role')
        userid = request.args.get('userid')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if userrole == 'admin':
            flash("ADMIN CAN'T BE MODIFIED")
            return redirect(url_for('admin'))
        elif request.method == 'POST' and 'name' in request.form and 'password' in request.form:
            name = request.form['name']  
            password = request.form['password']
            urole = request.form['role']
            cursor.execute('SELECT * FROM user WHERE name = %s',(name,))
            ud = cursor.fetchone()
            cursor.execute('SELECT name FROM user WHERE userid = %s',(userid,))
            current_user = cursor.fetchone()
            current_name = current_user["name"]
            
            if name == current_name:
                cursor.execute('UPDATE user SET password = %s WHERE userid = %s',(password,userid))
                cursor.execute('UPDATE roles_table SET role_name = %s WHERE user_id = %s',(urole,userid))
                mysql.connection.commit()
                flash("USER MODIFIED")
                return redirect(url_for('admin'))
            
            if ud:
                text = "USER EXISTS"
            elif not name:
                text = "NAME REQUIRED"
            else:    
                cursor.execute('UPDATE user SET name = %s,password = %s WHERE userid = %s',(name,password,userid))
                cursor.execute('UPDATE roles_table SET role_name = %s WHERE user_id = %s',(urole,userid))
                mysql.connection.commit()
                flash("USER MODIFIED")
                return redirect(url_for('admin'))
    return render_template("useredit.html",userid = userid,role = userrole, text=text)

@app.route('/adduser', methods = ['GET','POST'])
def adduser():
    text = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form :
        name = request.form['name']  
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE name = %s',(name,))
        userData = cursor.fetchone()
        if userData:
            text = "Account Exists"
        elif not name or not password:
            text = "ALL FIELDS REQUIRED"
        else:
            cursor.execute('INSERT INTO user VALUES(NULL,%s,%s,%s)',(name,password,"1.jpeg"))
            cursor.execute('SELECT userid FROM user WHERE name=%s',(name,))
            new__user = cursor.fetchone()
            u___id = new__user["userid"]
            cursor.execute('INSERT INTO roles_table VALUES(NULL,%s,%s)',(u___id,"user"))
            mysql.connection.commit()
            session['name'] = name
            return render_template("uploader1.html")       
    return render_template("adduser.html",text = text)

@app.route('/uploader1', methods=['GET', 'POST'])
def uploader1():
    if request.method == 'POST':
        if 'file1' not in request.files:
            return 'there is no file1 in form!'
        file1 = request.files['file1']
        cursor = mysql.connection.cursor()
        file1.filename = str(session['name'])+".jpeg"
        newName= file1.filename
        path = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
        file1.save(path)
        cursor.execute('UPDATE user SET imgsource = %s WHERE name = %s',(newName,session['name']))
        mysql.connection.commit()
        return redirect(url_for("admin"))
    return render_template("uploader1.html")

@app.route('/reset' , methods = ['GET','POST'])
def reset():
    if request.method == "POST":
        name = request.form['username']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE name = %s  ', (name,))
        user = cursor.fetchone()
        if user:
            number = randint(1,2000)
            now = datetime.now() + timedelta(minutes=1)
            cursor.execute('INSERT INTO password_reset values(NULL,%s,%s,%s)',(name,number,now))
            mysql.connection.commit()
            return render_template('reset2.html',text = "TOKEN GENERATED AND SAVED IN DATABASE::EXPIRATION TIME-->60 SECONDS")
        else:
            return render_template('reset.html',text = "Username not Valid")
    return render_template('reset.html')

@app.route('/reset2' , methods = ['GET','POST'])
def reset2():
    if request.method == "POST":
        name = request.form['username']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE name = %s  ', (name,))
        user = cursor.fetchone()
        if user:
            cursor.execute("SELECT max(id) FROM password_reset where user_name = %s",(name,))
            max_id = cursor.fetchone()
            max__id = max_id['max(id)']
            token = str(request.form['token'])
            cursor.execute("SELECT * FROM password_reset where id = %s",(max__id,))
            reset_details = cursor.fetchone()
            token__validator = str(reset_details['reset_token'])
            exp_time = str(reset_details['expiration_time'])
            now = str(datetime.now())
            if token == token__validator:
                if now < exp_time:
                    password = request.form['password']
                    cursor.execute("UPDATE user SET password = %s where name = %s",(password,name))
                    mysql.connection.commit()
                    return render_template('login.html', text = "PASSWORD UPDATED")
                else:
                    return render_template('login.html', text = "TIME EXPIRED")
            else:
                return render_template('reset2.html', text = "not a valid token")
        else:
            return render_template('reset2.html',text = "Username not Valid")
    return render_template('reset2.html')

if __name__ == "__main__":
    app.run()
