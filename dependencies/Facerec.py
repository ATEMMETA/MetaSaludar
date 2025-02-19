import os, glob, cv2, face_recognition
import numpy as np

class Facerec:
    def __init__(self, images_path=None):  # Allow path to be passed during initialization
        self.known_face_encodings = []
        self.known_face_names = []
        self.frame_resizing = 0.5
        if images_path: # Load images if path is provided
            self.load_encoding_images(images_path)

    def load_encoding_images(self, images_path):
        """Load encoding images from path."""

        f_types = (os.path.join(images_path,"*.jpg"), os.path.join(images_path,'*.png'))
        images_path_list = [] # Better naming
        for files in f_types:
            images_path_list.extend(glob.glob(files))

        print(f"{len(images_path_list)} encoding images found.") # f-string for cleaner formatting

        for img_path in images_path_list:
            img = cv2.imread(img_path)
            if img is None: #check if the image was read successfully
                print(f"Error reading image: {img_path}")
                continue

            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            basename = os.path.basename(img_path)
            filename, _ = os.path.splitext(basename) # _ for unused variable

            try:
                encodings = face_recognition.face_encodings(rgb_img)
                if not encodings: #check if any face was detected
                    print(f"No face detected on {filename}")
                    continue
                img_encoding = encodings[0] # Take the first encoding if multiple faces are detected
            except Exception as e: # Catch potential errors during encoding
                print(f"Error encoding image {filename}: {e}")
                continue

            self.known_face_encodings.append(img_encoding)
            self.known_face_names.append(filename)

        print("Encoding images loaded")

    def detect_known_faces(self, frame):
        small_frame = cv2.resize(frame, (0, 0), fx=self.frame_resizing, fy=self.frame_resizing)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index] and face_distances[best_match_index] < 0.6: # Add a threshold
                name = self.known_face_names[best_match_index]

            face_names.append(name)

        face_locations = np.array(face_locations) * (1/self.frame_resizing) # More efficient resizing
        return face_locations.astype(int), face_names
