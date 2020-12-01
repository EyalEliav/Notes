from flask import Flask,send_file,render_template,request,redirect
import sqlite3
import uuid
from note import Note
from validate_email import validate_email
import os
import smtplib
from threading import Thread
from time import sleep
import flask
import random







def wait_to_delete(code):
    sleep(300)
    conn = sqlite3.connect('Notes.db')
    c = conn.cursor()
    c.execute("DELETE FROM tempCodes WHERE code = (?)",(code,))


app = Flask(__name__,template_folder='src')
app.run(host="0.0.0.0")

@app.route('/',methods = ['GET','POST'])
def send_homePage():
    return render_template("index.html")

@app.route('/sub_user',methods = ['GET','POST'])
def forgot_password():
    conn = sqlite3.connect('Notes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = (?)",(request.form['Uname'],))
    conn.commit()
    l = c.fetchall()
    if len(l) < 1:
        return render_template("forgot.html", error = "user not exist")
    unique_code = str(uuid.uuid4())
    c.execute("INSERT INTO tempCodes VALUES (?,?)", (request.form['Uname'], unique_code))
    conn.commit()
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login('myonlinenotesil@gmail.com', 'Eyal-Eliav01')
    sbj = "Notes - forgot password"
    body = "This is your unique code : " + unique_code + ". this code will expire in 5 minutes"
    msg = f'Subject: {sbj}\n\n{body}'
    user_mail = l[0][2]
    th = Thread(target = wait_to_delete, args=(unique_code,))
    th.start()
    smtp.sendmail('eyaleliav15@gmail.com', user_mail, msg)
    return render_template("restore_password.html")
	
@app.route('/login',methods = ['POST'])
def try_login():
    conn = sqlite3.connect('Notes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = (?)",(request.form['Uname'],))
    conn.commit()
    l = c.fetchall()
    if len(l) < 1:
        return render_template("index.html", error = "user not exist")
    if request.form['Password'] != l[0][1]:
        return render_template("index.html", error = "wrong password")
    nts = []
    c.execute("SELECT * FROM notes WHERE cookie = (?)", (l[0][3],))
    conn.commit()
    l = c.fetchall()
    conn.commit()
    for it in l:
        nts.append(Note(it[1], it[2], it[3]))
    nts.reverse()
    resp = flask.make_response(render_template("account.html", notes=nts, user=request.form['Uname']))
    c.execute("SELECT cookie FROM users WHERE username = (?)", (request.form['Uname'],))
    conn.commit()
    l = c.fetchall()
    conn.commit()
    resp.set_cookie("cookie", l[0][0])
    return resp


@app.route('/resPass',methods = ['POST'])
def pass_res():
    if request.form['Password'] != request.form['conPassword']:
        return render_template("restore_password.html", error = "passwords are not equal")
    conn = sqlite3.connect('Notes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM tempCodes WHERE code = (?)", (request.form['Code'],))
    conn.commit()
    l = c.fetchall()
    if len(l) < 1:
        return render_template("restore_password.html", error = "code does not exists")
    if len(request.form['Password']) < 8 :
        return render_template("restore_password.html", error = "password must be at least 8 characters")
    c.execute("UPDATE users SET password = :pass WHERE username = :user", {'pass':request.form['Password'],'user':l[0][0]})
    conn.commit()
    return render_template("index.html")
    

@app.route('/deleteNote',methods = ['GET'])
def delete_note():
    id = request.args.get('arg')
    conn = sqlite3.connect('Notes.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE cookie = (?)", (request.cookies.get("cookie")[0:36],))
    conn.commit()
    l = c.fetchall()
    usr = l[0][0]
    c.execute("DELETE FROM notes WHERE id = (?)", (id,))
    conn.commit()
    c.execute("SELECT * FROM notes WHERE cookie = (?)", (request.cookies.get("cookie")[0:36],))
    conn.commit()
    l = c.fetchall()
    nts = []
    for n in l:
        nts.append(Note(n[1], n[2],n[3]))
    nts.reverse()
    return render_template("account.html", notes=nts, user=usr)



@app.route('/signUp',methods = ['GET'])
def sign_up():
    return render_template("signUp.html")

@app.route('/addNote',methods = ['POST'])
def add_note():
    cookie = request.cookies.get("cookie")[0:36]
    conn = sqlite3.connect('Notes.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE cookie = (?)", (cookie,))
    conn.commit()
    l = c.fetchall()
    usr = l[0][0]
    if request.form['sub'] == "" or request.form['body'] == "":
        c.execute("SELECT * FROM notes WHERE cookie = (?)", (cookie,))
        conn.commit()
        l = c.fetchall()
        nts = []
        for n in l:
            nts.append(Note(n[1], n[2],n[3]))
        nts.reverse()
        return render_template("account.html", notes=nts, error="subject and body cannot be empty", user=usr)
    uid = str(uuid.uuid4())
    c.execute("INSERT INTO notes VALUES (?,?,?,?)", (cookie, request.form['sub'], request.form['body'], uid))
    conn.commit()
    c.execute("SELECT * FROM notes WHERE cookie = (?)", (cookie,))
    conn.commit()
    l = c.fetchall()
    nts = []
    for n in l:
        nts.append(Note(n[1], n[2], n[3]))
    nts.reverse()
    return render_template("account.html", notes=nts, user=usr)


@app.route('/forgot',methods = ['GET'])
def forgot_pass():
    return render_template("forgot.html")






@app.route('/trysignUp',methods = ['POST'])
def try_sign_up():
    conn = sqlite3.connect('Notes.db')
    c = conn.cursor()
    if request.form['Password'] != request.form['conPassword']:
        return render_template("signUp.html", error = "passwords are not equal")
    if len(request.form['Password']) < 8 :
        return render_template("signUp.html", error = "password must be at least 8 characters")
    if not(validate_email(request.form['Mail'])):
        return render_template("signUp.html", error = "Invalid email")
    c.execute("SELECT * FROM users WHERE email = (?)", (request.form['Mail'],))
    conn.commit()
    l = c.fetchall()
    if len(l) > 0:
        return render_template("signUp.html", error = "Email already exists")
    c.execute("SELECT * FROM users WHERE username = (?)", (request.form['Uname'],))
    conn.commit()
    l = c.fetchall()
    if len(l) > 0:
        return render_template("signUp.html", error = "Username taken")
    c.execute("SELECT * FROM users WHERE username = (?)", (request.form['Uname'],))
    conn.commit()
    l = c.fetchall()
    if len(l) > 0 :
        return render_template("signUp.html", error = "username already taken")
    c.execute("INSERT INTO users VALUES (?,?,?,?)",(request.form['Uname'], request.form['Password'], request.form['Mail'], str(uuid.uuid4())))
    conn.commit()
    return render_template("index.html")





#-------------------------------------------Creating the tables - run only 1 time---------------------------------------------
#conn = sqlite3.connect('Notes.db')
#c = conn.cursor()

#c.execute("""CREATE TABLE users (
#    username text,
#    password text,
#    email text,
#    cookie text
#)""")

#c.execute("""CREATE TABLE notes (
#    cookie text,
#    subject text,
#    body text,
#    id text
#)""")


#c.execute("""CREATE TABLE tempCodes (
#    username text,
#    code text
#)""")

#conn.commit()

#conn.close()

#-----------------------------------------------------------------------------------------------------------------------------------