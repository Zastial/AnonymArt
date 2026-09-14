import cv2
import numpy as np
import pyvirtualcam

MODEL = "data/face_detection_yunet.onnx"
COULEUR_BOITE = (0, 220, 0)
COULEURS_POINTS = [(255, 80, 0), (0, 80, 255), (0, 255, 255), (255, 0, 255), (255, 255, 0)]

def blur_face(frame, x, y, w, h, size=20):
    """Blur the zone (x, y, w, h) in the frame."""
    h_img, w_img = frame.shape[:2]

    x1, y1 = max(x, 0), max(y, 0)
    x2, y2 = min(x + w, w_img), min(y + h, h_img)
    if x2 <= x1 or y2 <= y1:
        return

    region = frame[y1:y2, x1:x2]
    nx = max(1, (x2 - x1) // size)
    ny = max(1, (y2 - y1) // size)

    petite = cv2.resize(region, (nx, ny), interpolation=cv2.INTER_AREA)
    frame[y1:y2, x1:x2] = cv2.resize(petite, (x2 - x1, y2 - y1),
                                     interpolation=cv2.INTER_NEAREST)


def detect_faces():
    detector = cv2.FaceDetectorYN.create(MODEL, "", (320, 320), 0.4, 0.3, 5000)
    output_width, output_height = 1920, 1080

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("Impossible d'ouvrir la webcam.")

    ok, frame = cap.read()
    if not ok:
        raise SystemExit("Aucune image reçue depuis la webcam.")

    hauteur, largeur = frame.shape[:2]
    dw = max(32, (largeur // 32) * 32)
    dh = max(32, (hauteur // 32) * 32)
    detector.setInputSize((dw, dh))

    with pyvirtualcam.Camera(width=output_width, height=output_height, fps=20) as cam:
        print(f"Using virtual camera: {cam.device}")
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Flux interrompu.")
                break

            frame = cv2.flip(frame, 1)
            petite = cv2.resize(frame, (dw, dh))
            _, visages = detector.detect(petite)

            if visages is None:
                visages = np.empty((0, 15), dtype=np.float32)

            sx, sy = largeur / dw, hauteur / dh
            for visage in visages:
                x, y, w, h = (visage[:4] * np.array([sx, sy, sx, sy])).astype(int)
                blur_face(frame, x, y, w, h)

            output_frame = cv2.resize(frame, (output_width, output_height),
                                      interpolation=cv2.INTER_LINEAR)
            output_frame = cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB)
            output_frame = cv2.flip(output_frame, 1)
            cam.send(output_frame)
            cam.sleep_until_next_frame()

            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_faces()