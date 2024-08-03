from flask import Flask, render_template, request, redirect, send_from_directory, jsonify, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
import joblib
import pandas as pd
import cv2
import threading
import speech_recognition as sr
import queue

app = Flask(__name__, static_folder='static/build', static_url_path='')

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///users.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
model = joblib.load('models/sales_model.pkl')

db = SQLAlchemy(app)
app.app_context().push()

class Users(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    def __repr__(self) -> str:
        return f"{self.email}-{self.password}"

# Queue to hold transcriptions for SSE
transcription_queue = queue.Queue()

# Speech Recognition Function
def listen_and_transcribe(output_file):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with open(output_file, 'w') as file:
        print("Listening... Press 'Ctrl + C' to stop.")
        while True:
            try:
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    print("Listening...")
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                try:
                    text = recognizer.recognize_google(audio)
                    print(f"Transcribed: {text}")
                    file.write(text + '\n')
                    file.flush()
                    transcription_queue.put(text)  # Add transcription to the queue
                except sr.UnknownValueError:
                    print("Google Speech Recognition could not understand the audio.")
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service; {e}")
            except sr.WaitTimeoutError:
                print("Listening timed out while waiting for phrase to start.")
            except KeyboardInterrupt:
                print("Interrupted by user")
                break

# Route to start transcription
@app.route('/start_transcription')
def start_transcription():
    output_file = "output.txt"
    threading.Thread(target=listen_and_transcribe, args=(output_file,)).start()
    return jsonify({"message": "Transcription started!"})

# Route for SSE stream
@app.route('/transcription_stream')
def transcription_stream():
    def stream():
        while True:
            transcription = transcription_queue.get()
            yield f"data: {transcription}\n\n"
    
    return Response(stream_with_context(stream()), content_type='text/event-stream')

# Serve the transcription page
@app.route('/transcribe')
def transcribe_page():
    return render_template('transcribe.html')

# Existing route definitions...

def generate_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            frame = cv2.resize(frame, (1280, 720))
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/', methods=['GET', 'POST'])
def hello_world():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        login = Users.query.filter_by(email=email).first()
        if login:
            alluser = Users.query.all()
            if login.email == email and login.password == password:
                message = "yes"
                return render_template('index.html', message=message, alluser=alluser)
        return redirect("/")

    return render_template('index.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'GET':
        return send_from_directory(app.static_folder, 'index.html')
    else:
        csv_file = r'final2.csv'
        data = pd.read_csv(csv_file)
        data2 = request.json

        email = int(data2['email'])
        password = int(data2['password'])

        if password == 1:
            selected_data = data[(data['Risk'] < 0.0124) & (data['close'] < email)]
        elif password == 2:
            selected_data = data[(data['Risk'] >= 0.0124) & (data['Risk'] < 0.0161) & (data['close'] < email)]
        else:
            selected_data = data[(data['Risk'] > 0.0161) & (data['close'] < email)]

        selected_data_list = selected_data['company_name'].tolist()
        website_links = selected_data['website_link'].tolist()

        predictions = [{'prediction_text': symbol, 'website_link': link} for symbol, link in zip(selected_data_list, website_links)]
        return jsonify(predictions)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'GET':
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/show')
def products():
    alluser = Users.query.all()
    print(alluser)
    return 'this is production page'

@app.route('/update/<int:sno>', methods=['GET', 'POST'])
def update(sno):
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        alluser = Users.query.filter_by(sno=sno).first()
        alluser.email = email
        alluser.password = password
        db.session.add(alluser)
        db.session.commit()
        return redirect("/")
    alluser = Users.query.filter_by(sno=sno).first()
    return render_template('update.html', alluser=alluser)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        alluser = Users(email=email, password=password)
        db.session.add(alluser)
        db.session.commit()
        return redirect("/")
    
    alluser = Users.query.all()
    return render_template('register.html', alluser=alluser)

@app.route('/delete/<int:sno>')
def delete(sno):
    alluser = Users.query.filter_by(sno=sno).first()
    db.session.delete(alluser)
    db.session.commit()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
