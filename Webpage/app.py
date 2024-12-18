import os
from flask import Flask, render_template, request, redirect
from datetime import datetime
from PIL import Image
import numpy as np
import tensorflow as tf
import cv2

app = Flask(__name__, static_folder="static")

model_image = tf.keras.models.load_model('./models/dr.h5')

model_video = tf.keras.models.load_model('./models/dr.h5')

class_labels = {
    0: "No DR (Không bị bệnh võng mạc do tiểu đường)",
    1: "Mild Non Proliferative DR (Bệnh võng mạc không tăng sinh mức độ nhẹ)",
    2: "Moderate Non Proliferative DR (Bệnh võng mạc không tăng sinh mức độ trung bình)",
    3: "Severe Non Proliferative DR (Bệnh võng mạc không tăng sinh mức độ nặng)",
    4: "Proliferative DR (Giai đoạn tăng sinh của bệnh võng mạc)"
}
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def classify_image(file_path):
    img = Image.open(file_path)
    img = img.resize((224, 224))
    img_array = np.array(img) 
    if img_array.shape[2] == 4:  
        img_array = img_array[:, :, :3]
    img_array = img_array.astype(np.uint8)
    img_array = np.expand_dims(img_array, axis=0)
    predictions = model_image.predict(img_array)
    threshold = 0.37757874193797547
    y_test_thresholded = predictions > threshold
    y_test_binary = y_test_thresholded.astype(int)
    y_test_adjusted = y_test_binary.sum(axis=1) - 1
    predicted_class = class_labels[y_test_adjusted[0]]
    stage = y_test_adjusted[0]
    return stage, predicted_class

def classify_video(file_path):
  
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        return "Error opening video file"

    total_frames = 0
    total_stage = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        total_frames += 1

        resized_frame = cv2.resize(frame, (224, 224))
        img_array = np.array(resized_frame)
        img_array = img_array.astype(np.uint8)
        img_array = np.expand_dims(img_array, axis=0)
        predictions = model_image.predict(img_array)

        threshold = 0.37757874193797547
        y_test_thresholded = predictions > threshold
        y_test_binary = y_test_thresholded.astype(int)
        y_test_adjusted = y_test_binary.sum(axis=1) - 1

        total_stage += y_test_adjusted[0]

    cap.release()

    if total_frames > 0:
        average_stage = total_stage / total_frames
    else:
        average_stage = 0

    predicted_class = class_labels[int(average_stage)]

    return predicted_class
@app.route('/')
def abc():
    return render_template('home.html', error=None)

@app.route('/activate')
def activate():
    return render_template('activate.html', error=None)
@app.route('/support', methods=['GET', 'POST'])
def support():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        # Đường dẫn tới file txt
        file_path = 'support_requests.txt'

                # Ghi thông tin vào file txt
        with open(file_path, 'a') as file:
            file.write(f'Name: {name}\n')
            file.write(f'Email: {email}\n')
            file.write(f'Phone: {phone}\n')
            file.write(f'Message: {message}\n')
            file.write('-' * 20 + '\n')
        return redirect('/')
    return render_template('support.html', error=None)

@app.route('/predict', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('result.html', error='No file part')

        file = request.files['file']
        username = request.form.get('username')  # Lấy username từ form
        age = request.form.get('age')  # Lấy tuổi từ form
        activate = request.form.get('activate')  # Lấy activate từ form
        address = request.form.get('address')  # Lấy activate từ form
        current_date = datetime.now().strftime('%d-%m-%Y')

        if file.filename == '':
            return render_template('result.html', error='No selected file')

        if file:
            file_path = os.path.join('static', file.filename)
            file.save(file_path)


            if file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                stage,predicted_class = classify_image(file_path)
            elif file.filename.lower().endswith(('.mp4', '.avi', '.mov')):
                predicted_class = classify_video(file_path)
            else:
                return render_template('result.html', error='Unsupported file format')

            return render_template('result.html', stage = stage,predicted_class=predicted_class, username=username, age=age, filename=file.filename, activate=activate, address=address, current_date=current_date)

    return render_template('index.html', error=None)



if __name__ == '__main__':
    app.run(debug=True)