import os
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from flask_cors import CORS 
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS

os.environ['HF_TOKEN'] = 'apnatokendalo'

UPLOAD_FOLDER = "uploads"
GENERATED_FOLDER = os.path.join("static", "generated")
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'webm', 'ogg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
CORS(app)


print("Loading ChatterboxTTS model... This may take a few minutes.")
model = ChatterboxTTS.from_pretrained(device="cuda")
print("Model loaded successfully.")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")

@app.route('/upload-voice', methods=['POST'])
def upload_voice():
    if 'audio_file' not in request.files:
        return jsonify({"error": "No audio file part in the request"}), 400
    file = request.files['audio_file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename("user_recording.wav") 
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(filepath)
            print(f"File saved successfully to {filepath}")
            return jsonify({
                "message": "Voice sample uploaded successfully!",
                "filename": filename
            }), 200
        except Exception as e:
            print(f"Error saving file: {e}")
            return jsonify({"error": f"Could not save file: {e}"}), 500
    else:
        return jsonify({"error": "File type not allowed"}), 400


@app.route('/generate-speech', methods=['POST'])
def generate_speech():
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({"error": "No text provided"}), 400

    print(f"Received text for generation: '{text}'")

    wav = model.generate(
            text, 
            audio_prompt_path=os.path.join(app.config['UPLOAD_FOLDER'], 'user_recording.wav')
        )

    output_filename = "generated_voice.wav"
    output_filepath = os.path.join(app.config['GENERATED_FOLDER'], output_filename)
        
    ta.save(output_filepath, wav, model.sr)
    print(f"Generated audio saved to {output_filepath}")
    final_audio_url = f"/static/generated/{output_filename}"

    return jsonify({
    "message": "Speech generated successfully",
   "audioUrl": final_audio_url
        }), 200



if __name__ == "__main__":
    app.run(debug=True, port=5000)