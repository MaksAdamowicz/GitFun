import cv2


def load_face_detector():
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_detector = cv2.CascadeClassifier(cascade_path)

    if face_detector.empty():
        raise RuntimeError(f"Could not load face cascade: {cascade_path}")

    return face_detector


def detect_faces_live(camera_index=0):
    face_detector = load_face_detector()
    camera = cv2.VideoCapture(camera_index)

    if not camera.isOpened():
        raise RuntimeError("Could not open the camera.")

    print("Camera opened. Press 'q' or Esc to quit.")

    try:
        while True:
            success, frame = camera.read()
            if not success:
                print("Could not read a frame from the camera.")
                break

            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(
                gray_frame,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(40, 40),
            )

            for x, y, width, height in faces:
                cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    "Face",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

            cv2.imshow("Live Face Detection", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()


def main():
    detect_faces_live()


if __name__ == "__main__":
    main()
