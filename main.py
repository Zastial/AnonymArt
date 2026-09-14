import cv2
import numpy as np
import pyvirtualcam

MODEL = "data/face_detection_yunet.onnx"
COULEUR_BOITE = (0, 220, 0)
COULEURS_POINTS = [(255, 80, 0), (0, 80, 255), (0, 255, 255), (255, 0, 255), (255, 255, 0)]

def blur_face(frame, x, y, w, h, size=40):
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


        cv2.putText(frame, f"{len(visages)} visage(s)", (10, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (240, 240, 240), 1, cv2.LINE_AA)
        cv2.imshow("TP - Detection de visages", frame)

        with pyvirtualcam.Camera(width=1280, height=720, fps=20) as cam:
            print(f'Using virtual camera: {cam.device}')
            while True:
                cam.send(frame)
                cam.sleep_until_next_frame()

        if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_faces()