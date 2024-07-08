from flask import Flask, render_template, request, jsonify, send_file
from elevenlabs import play
from elevenlabs.client import ElevenLabs
import google.generativeai as genai
import PIL.Image
import io

# Configure Google Generative AI API
GOOGLE_API_KEY = "AIzaSyClHfsmtQgIT7SczQwDfYBW3MDJRfpPmOY"
genai.configure(api_key=GOOGLE_API_KEY)

# Configure Eleven Labs API
ELEVEN_API_KEY = "sk_75d849fd0074c81e2d2414ba39a552411bdfca74f9ef31e5"
client = ElevenLabs(api_key=ELEVEN_API_KEY)
# sk_0d3aa1285581235db6b47fd09a786da8a2ba706c72c70ed3
app = Flask(__name__)

# Route to render index.html
@app.route('/')
def index():
    return render_template('index.html')

# Route to render about.html
@app.route('/about')
def about():
    return render_template('about.html')

# Route to render contactus.html
@app.route('/contactus')
def contactus():
    return render_template('contactus.html')

# Route to render createStory.html
@app.route('/createStory')
def create_story():
    return render_template('createStory.html')

# API endpoint to process uploaded image
@app.route('/process_image', methods=['POST'])
def process_image():
    try:
        file = request.files['image']
        if file and file.filename != '':
            # Read the image
            img = PIL.Image.open(file)
            
            # Create the GenerativeModel
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

            # Start the chat session
            chat_session = model.start_chat(history=[])

            # Generate the story based on the image
            message = "I want you to be my data analyst and make a compelling storytelling based on the image of the chart provided."
            response = chat_session.send_message([message, img])
            story = response.candidates[0].content.parts[0].text

            # Remove quotes and newline characters
            story = story.replace('"', '').replace('\n', '').replace('*', '')

            return story
        else:
            return 'Error processing image. Please try again.', 400
    except Exception as e:
        return str(e), 500

# API endpoint to convert text to speech
@app.route('/text_to_speech', methods=['POST'])
def text_to_speech():
    try:
        data = request.json
        text = data.get('text')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        audio = client.generate(
            text=text,
            voice="Rachel",
            model="eleven_multilingual_v2"
        )
        play(audio)

        # Return a success response after playing the audio
        return jsonify({'message': 'Speech played successfully'}), 200

    except Exception as e:
        app.logger.error(f"Error generating speech: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
