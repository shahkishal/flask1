from flask import Flask , render_template,request,redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///users.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.app_context().push()

class Users(db.Model):
    sno = db.Column(db.Integer ,primary_key=True)
    email = db.Column(db.String(200) ,nullable=False)
    password = db.Column(db.String(200) ,nullable=False)
    def __repr__(self) -> str:
        return f"{self.email}-{self.password}"
@app.route('/',methods=['GET' , 'POST'])
def hello_world():
    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        login = Users.query.filter_by(email=email).first()
        if(login):
            alluser = Users.query.all()
            if(login.email==email and login.password==password ):
                message = "yes"
                return render_template('index.html',message = message,alluser=alluser)

            return redirect("/")

    alluser = Users.query.all()
    return render_template('index.html',alluser=alluser)

@app.route('/show')
def products():
    alluser = Users.query.all()
    print(alluser)
    return 'this is production page'

@app.route('/update/<int:sno>',methods=['GET' , 'POST'])
def update(sno):
    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        alluser = Users.query.filter_by(sno=sno).first()
        alluser.email = email
        alluser.password = password
        db.session.add(alluser)
        db.session.commit()
        return redirect("/")
    alluser = Users.query.filter_by(sno=sno).first()
    return render_template('update.html',alluser=alluser)

@app.route('/register',methods=['GET' , 'POST'])
def register():
    print("hi")
    if request.method=='POST':
       
        email = request.form['email']
        password = request.form['password']
        alluser = Users(email=email,password=password)
        db.session.add(alluser)
        db.session.commit()
        return redirect("/")
    
    alluser = Users.query.all()
    return render_template('register.html',alluser=alluser)


@app.route('/delete/<int:sno>')
def delete(sno):
    alluser = Users.query.filter_by(sno=sno).first()
    db.session.delete(alluser)
    db.session.commit()
    return redirect("/")




if __name__ == "__main__":
    app.run(debug=True)