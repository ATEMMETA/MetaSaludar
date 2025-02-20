from flask import Flask, render_template, request, redirect, url_for, flash
import cv2
import numpy as np
import os
from dependencies.Facerec import Facerec
from dependencies.Facedet import FaceDet

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Important for flash messages

# --- Initialize Face Recognition ---
images_path = "images"  # Path to your images directory
fr = Facerec(images_path)
fr.load_encoding_images(images_path)
fd = FaceDet(images_path)

# --- Camera setup ---
cam_n = 0 #Or your rtsp url
cap = cv2.VideoCapture(cam_n)
if not cap.isOpened():
    raise IOError("Cannot open webcam")

frame_width = int(cap.get(3))
frame_height = int(cap.get(4))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'addface' in request.form:
            name = request.form['name']
            if 'image' in request.files:
                image = request.files['image']
                # Check if the uploaded file is an image
                allowed_extensions = {'.jpg', '.jpeg', '.png'}
                if any(image.filename.lower().endswith(ext) for ext in allowed_extensions):
                    try:
                        image_bytes = image.read()
                        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

                        success, original_image_path, detected_image_path = fd.find_face(image, name)

                        if success:
                            fr.load_encoding_images(images_path)  # Reload encodings
                            flash(f"Face added for {name}!", "success")
                        else:
                            flash("No face detected in the image.", "error")
                    except Exception as e:
                        flash(f"An error occurred: {e}", "error")
                else:
                    flash("Invalid file type. Please upload a JPG, JPEG, or PNG image.", "error")
            else:
                flash("Please attach an image to the command.", "error")

            return redirect(url_for('index'))

    # --- Face Recognition (Live) ---
    ret, frame = cap.read()
    face_locations, face_names = fr.detect_known_faces(frame)
    for (y1, x2, y2, x1), name in zip(face_locations, face_names):
        color = (0, 0, 225) if name == "Unknown" else (0, 225, 0)
        cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, color, 1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)


    ret, frame_encoded = cv2.imencode('.jpg', frame)
    frame_bytes = frame_encoded.tobytes()

    return render_template('index.html', frame_bytes=frame_bytes)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)  # use_reloader=False for Colab
