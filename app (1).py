import os
import numpy as np
import tensorflow as tf
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image
import io

app = Flask(__name__)

# Load the trained CNN model
MODEL_PATH = "models/skin_disease_model.h5"  # Ensure this path matches your actual model location
if not os.path.exists(MODEL_PATH):
    model = None
    print("Error: Model file not found!")
else:
    try:
        model = load_model(MODEL_PATH)
        print("Model loaded successfully!")
    except Exception as e:
        model = None
        print(f"Error loading model: {e}")

# Define the classes (Update according to your trained model)
class_labels = ["Acne", "Eczema", "Psoriasis", "Melanoma", "Healthy Skin"]

# Upload folder
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def preprocess_image(image_path):
    """Preprocess image for model prediction"""
    try:
        img = Image.open(image_path).convert("RGB")
        img = img.resize((224, 224))  # Change based on your model input size
        img_array = np.array(img) / 255.0  # Normalize
        img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
        return img_array
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

@app.route("/", methods=["GET"])
def home():
    return "Welcome to the TeleDerm Backend!"

@app.route("/status", methods=["GET"])
def status():
    """Check if the model is loaded"""
    if model is None:
        return jsonify({"status": "Model is not loaded"}), 500
    return jsonify({"status": "Model is loaded and ready"}), 200

@app.route("/predict", methods=["POST"])
def predict():
    """Handle image upload and model prediction"""
    if model is None:
        return jsonify({"error": "Model is not loaded"}), 500

    if "image" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    # Preprocess image
    img_array = preprocess_image(file_path)
    if img_array is None:
        return jsonify({"error": "Failed to process image"}), 500

    # Predict
    try:
        predictions = model.predict(img_array)
        predicted_class = class_labels[np.argmax(predictions)]
        confidence_score = float(np.max(predictions))

        response = {
            "predicted_class": predicted_class,
            "confidence": confidence_score,
            "predictions": predictions.tolist()
        }
        return jsonify(response)
    
    except Exception as e:
        return jsonify({"error": f"Prediction error: {str(e)}"}), 500

@app.route("/upload_model", methods=["POST"])
def upload_model():
    """Upload a new model"""
    if "model_file" not in request.files:
        return jsonify({"error": "No model file uploaded"}), 400

    file = request.files["model_file"]
    file_path = os.path.join("models", "skin_disease_model.h5")

    try:
        file.save(file_path)
        global model
        model = load_model(file_path)
        return jsonify({"message": "Model uploaded and loaded successfully!"})
    except Exception as e:
        return jsonify({"error": f"Error loading model: {str(e)}"}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK"}), 200

if __name__ == "__main__":
    if not os.path.exists("models"):
        os.makedirs("models")

    app.run(debug=True)
