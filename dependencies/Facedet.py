import face_recognition
import cv2
import os

class FaceDet:
    def __init__(self, output_dir):  # More descriptive name
        self.output_dir = output_dir
        os.makedirs(os.path.join(self.output_dir, "images"), exist_ok=True) # Create images directory if not present

    def find_face(self, image_path: str, name: str): # More descriptive name and type hint
        image = cv2.imread(image_path)
        if image is None: # Check if image loaded successfully
            print(f"Error: Could not read image at {image_path}")
            return False, None, None

        rgb_frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        if face_locations:  # Simplified condition: if the list is not empty
            # Draw rectangles on a copy to preserve the original image
            annotated_image = image.copy()
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(annotated_image, (left, top), (right, bottom), (0, 255, 0), 2) # Thicker rectangle

            output_image_path = os.path.join(self.output_dir, "images", f"{name}.jpg")
            cv2.imwrite(output_image_path, image)  # Save original image

            temp_image_path = os.path.join(os.getenv("TEMP"), f"{name}_det.jpg")
            cv2.imwrite(temp_image_path, annotated_image)  # Save annotated image

            return True, output_image_path, temp_image_path
        else:
            return False, None, None  # Return None for the paths if no face is found
