from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
# this function serves the login page on boot:
def index():
    return render_template("login.html")


app.run()