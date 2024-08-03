# This Website, code [HTML, CSS, JS, PYTHON] built BY MOHAMMAD AL JADALLAH, JORDANIAN. The best.
# This project was entered into the Google Gemini competition.

# ========================================================================================
# Warning: Elevenlabs do some restrictions on their api, so this is a limited version
# and you may not be able to run voices on the story you get due to the limitations.
# So you can use your API key of elevenlabs.
# Also, they do changes on their API, so if you face a problem we did not solve it yet... 

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from PIL import Image
import os
from elevenlabs import play
from elevenlabs.client import ElevenLabs
import google.generativeai as genai
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash

# Configure Google Generative AI API
GOOGLE_API_KEY = "AIzaSyClHfsmtQgIT7SczQwDfYBW3MDJRfpPmOY"
genai.configure(api_key=GOOGLE_API_KEY)

# Configure Eleven Labs API
ELEVEN_API_KEY = "sk_75d849fd0074c81e2d2414ba39a552411bdfca74f9ef31e5"
client = ElevenLabs(api_key=ELEVEN_API_KEY)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_content.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class UserContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(150), nullable=False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contactus')
def contactus():
    return render_template('contactus.html')

@app.route('/createStory')
def create_story():
    return render_template('createStory.html')

@app.route('/process_image', methods=['POST'])
def process_image():
    try:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save the image in a compatible format
            img = Image.open(file)
            img.save(filepath, format=img.format)

            # Generate text based on the image
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash-latest",
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ],
                generation_config={
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": 64,
                    "max_output_tokens": 8192,
                    "response_mime_type": "text/plain",
                },
            )

            chat_session = model.start_chat(history=[])

            message = "I want you to be my data analyst and make a compelling storytelling based on the image of the chart provided."
            response = chat_session.send_message([message, img])
            story = response.candidates[0].content.parts[0].text

            story = story.replace('"', '').replace('\n', '').replace('*', '')

            new_content = UserContent(text=story, image_filename=filename)
            db.session.add(new_content)
            db.session.commit()

            return story
        else:
            return 'Invalid file format. Please upload an image in PNG, JPG, JPEG, or GIF format.', 400
    except Exception as e:
        return str(e), 500


# Warning: Elevenlabs do some restrictions on their api, so this is a limited version
# and you may not be able to run voices on the story you get due to the limitations.
# So you can use your API key of elevenlabs.
# Also, they do changes on their API, so if you face a problem we did not solve it yet... 

@app.route('/text_to_speech', methods=['POST'])
def text_to_speech():
    try:
        data = request.json
        text = data.get('text')
        voice = data.get('voice', 'Rachel')  # Default to 'Rachel' if no voice is provided

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        app.logger.info(f"Generating speech for text: {text} with voice: {voice}")

        try:
            audio = client.generate(
                text=text,
                voice=voice,
                model="eleven_multilingual_v2"
            )
            play(audio)
        except Exception as e:
            app.logger.error(f"API error: {e}")
            return jsonify({'error': f"API error: {e}"}), 500

        return jsonify({'message': 'Speech played successfully'}), 200

    except Exception as e:
        app.logger.error(f"Error generating speech: {e}")
        return jsonify({'error': str(e)}), 500

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the provided username and password match the admin credentials
        admin_user = User.query.filter_by(username=username).first()
        if admin_user and check_password_hash(admin_user.password, password):
            # If credentials are correct, store the user_id in session
            session['user_id'] = admin_user.id
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password', 'error')

    # Render the login form if not authenticated or if method is GET
    return render_template('login.html')

@app.route('/admin')
def admin():
    if 'user_id' in session:
        contents = UserContent.query.all()
        return render_template('admin.html', contents=contents)
    else:
        return redirect(url_for('login'))

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    if not os.path.exists('static/uploads'):
        os.makedirs('static/uploads')

    with app.app_context():
        db.create_all()

    # Create a default admin user if not already created
    with app.app_context():
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            hashed_password = generate_password_hash('tfr$jmz?vQF#2Cw')
            new_user = User(username='admin', password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

    app.run(debug=True)
