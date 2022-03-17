from flask import Flask,render_template,request,redirect,jsonify
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker 
from sqlalchemy.sql import text
import logging
import json
import random,string

app = Flask(__name__)
engine = create_engine('mysql+mysqlconnector://morise:testtest@localhost/educ_morise')
session = sessionmaker(bind=engine)()

def randomname(n):
   randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
   return ''.join(randlst)

@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/form', methods=['POST'])
def post():
    html_name = request.form['form_name']
    html_pass = request.form['form_pass']
    token = randomname(10)
    t = text("SELECT * from  users WHERE name = '" + html_name + "'")
    results = session.execute(t)
    for result in results: 
        true_password = result.password
    if(true_password == html_pass):
        t = text("UPDATE users SET token = '" + token + "' WHERE name = '" + html_name + "' AND password = '"+ html_pass +"';")
        result = session.execute(t)
        session.commit()
        redirect_url = "/home?token=" + token
        # redirect_url = "/"+html_name+"?token="+token
        return redirect(redirect_url)
    else:
        return "login failed"

@app.route('/home')
def hello():
    req = request.args
    token = req.get("token")
    t = text("SELECT * from  users WHERE token = '" + token + "'")
    results = session.execute(t)
    for result in results: 
        name = result.name
        grade = result.grade 
    return render_template('hello.html', title='呼び出し側でタイトル設定', name=name, grade=grade)

#ここから追加
@app.route('/line-auth')
def line_auth():
    req = request.args
    token = req.get("token")
    response_type = "code"
    client_id = ""
    redirect_uri = ""
    state = token
    scope = "notify"
    url = ""
    return redirect(url + "?response_type="+response_type+"&client_id="+client_id+"&redirect_uri="+redirect_uri+"&state="+state+"&scope="+scope)


@app.route('/line-auth/callback')
def line_callback():
    req = request.args
    code = req.get("code")
    logging.error(code)
    token = req.get("state")
    # logging.error(state)

    url = ""
    redirect_uri = ""
    headers = {"Content-Type":"application/x-www-form-urlencoded"}
    data ={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri ,
        "client_id":"",
        "client_secret":""
    }
    response = requests.post(url,headers = headers,data= data)
    line_token = json.loads(response.text)["access_token"]
#tokenで識別されたユーザーのline_tokenカラムにline_tokenを入れてあげる
    redirect_url = "/after-line-login?token="+token
    return redirect(redirect_url)

@app.route('/after-line-login')
def after_line_login():
    return render_template("after-line-login.html")

@app.route('/send-message-form',methods=['POST'])
def send_message():
    message = request.form['message']
    token = request.form['token']
    #tokenからline_tokenを取得(SELECT)
    s=text("select * from users where token ='"+token+"';")
    results=session.execute(s)

    for result in results:
        line_token = result["line_token"]
        name = result["name"]
        grade = result["grade"]

    headers = {
        "Content-Type":"application/x-www-form-urlencoded",
        "Authorization":"Bearer "+str(line_token)
    }
    body = {"message":message}
    url = "https://notify-bot.line.me/oauth/token"
    response = requests.post(url,headers = headers,data= body)
    return render_template('after-line-login.html', name=name, grade=grade)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
