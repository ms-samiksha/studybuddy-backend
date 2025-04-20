# face/capture_face.py
import cv2
import os
import re

# Global variable for button click
save_clicked = False
button_rect = (50, 400, 100, 40)  # (x, y, width, height)

def mouse_callback(event, x, y, flags, param):
    global save_clicked
    if event == cv2.EVENT_LBUTTONDOWN:
        bx, by, bw, bh = button_rect
        if bx <= x <= bx + bw and by <= y <= by + bh:
            save_clicked = True
            print("DEBUG: Save button clicked")

def capture_face(user_id, username, output_dir="face"):
    global save_clicked
    save_clicked = False
    print(f"DEBUG: Starting capture_face for user_id: {user_id}, username: {username}")

    # Validate username
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        print("DEBUG: Invalid username")
        return None, "Invalid username. Use only letters, numbers, or underscores."

    # Create user folder
    user_folder = os.path.join(output_dir, username)
    try:
        os.makedirs(user_folder, exist_ok=True)
        print(f"DEBUG: User folder created/verified: {user_folder}")
    except Exception as e:
        print(f"DEBUG: Error creating user folder: {str(e)}")
        return None, f"Error creating folder: {str(e)}"

    image_path = os.path.join(user_folder, f"{user_id}.jpg")
    print(f"DEBUG: Output image path: {image_path}")

    # Initialize webcam
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("DEBUG: Error: Could not open webcam")
            return None, "Could not open webcam"
    except Exception as e:
        print(f"DEBUG: Error initializing webcam: {str(e)}")
        return None, f"Error initializing webcam: {str(e)}"

    # Load face detector
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if face_cascade.empty():
            print("DEBUG: Error: Could not load face cascade")
            cap.release()
            return None, "Could not load face cascade"
    except Exception as e:
        print(f"DEBUG: Error loading face cascade: {str(e)}")
        cap.release()
        return None, f"Error loading face cascade: {str(e)}"

    print("DEBUG: Webcam started. Click 'Save' or press 's' to save (face must be detected). Press 'q' to quit.")

    gui_enabled = True
    cv2.namedWindow("Capture Face")
    cv2.setMouseCallback("Capture Face", mouse_callback)

    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                print("DEBUG: Failed to grab frame from webcam")
                cap.release()
                return None, "Failed to capture image"

            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.01, minNeighbors=2, minSize=(30, 30))
            print(f"DEBUG: Detected {len(faces)} faces")

            # Draw rectangles around detected faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # Show number of faces detected
            cv2.putText(frame, f"Faces: {len(faces)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            # Draw save button
            bx, by, bw, bh = button_rect
            cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 255, 0), -1)
            cv2.putText(frame, "Save", (bx + 10, by + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

            # Handle GUI operations
            if gui_enabled:
                try:
                    cv2.imshow("Capture Face", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if (save_clicked or key == ord('s')) and len(faces) > 0:
                        try:
                            cv2.imwrite(image_path, frame)
                            print(f"DEBUG: Saved face image at {image_path}")
                            cap.release()
                            cv2.destroyAllWindows()
                            return image_path, None
                        except Exception as e:
                            print(f"DEBUG: Error saving image: {str(e)}")
                            cap.release()
                            cv2.destroyAllWindows()
                            return None, f"Error saving image: {str(e)}"
                    elif key == ord('q'):
                        print("DEBUG: Quitting without saving")
                        cap.release()
                        cv2.destroyAllWindows()
                        return None, "User quit without saving"
                except Exception as e:
                    print(f"DEBUG: GUI error (imshow/waitKey): {str(e)}. Switching to non-GUI mode.")
                    gui_enabled = False
                    try:
                        cv2.destroyAllWindows()
                    except:
                        pass

            # Non-GUI mode
            if not gui_enabled:
                key = cv2.waitKey(1) & 0xFF
                if key == ord('s') and len(faces) > 0:
                    try:
                        cv2.imwrite(image_path, frame)
                        print(f"DEBUG: Saved face image at {image_path}")
                        cap.release()
                        return image_path, None
                    except Exception as e:
                        print(f"DEBUG: Error saving image: {str(e)}")
                        cap.release()
                        return None, f"Error saving image: {str(e)}"
                elif key == ord('q'):
                    print("DEBUG: Quitting without saving")
                    cap.release()
                    return None, "User quit without saving"

        except Exception as e:
            print(f"DEBUG: Error in capture loop: {str(e)}")
            cap.release()
            if gui_enabled:
                try:
                    cv2.destroyAllWindows()
                except:
                    pass
            return None, f"Error in capture loop: {str(e)}"

    cap.release()
    if gui_enabled:
        try:
            cv2.destroyAllWindows()
        except:
            pass
    return None, "Capture loop exited unexpectedly"