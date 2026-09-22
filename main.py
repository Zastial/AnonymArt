import os
import tkinter as tk
from tkinter import filedialog

import cv2
import numpy as np
import pyvirtualcam

MODEL = "data/face_detection_yunet.onnx"
COULEUR_BOITE = (0, 220, 0)
COULEURS_POINTS = [(255, 80, 0), (0, 80, 255), (0, 255, 255), (255, 0, 255), (255, 255, 0)]

def choisir_mode():
    """Affiche une fenêtre de choix : webcam en direct ou vidéo importée.

    Retourne un tuple (mode, chemin_video) où mode vaut "webcam" ou "video".
    chemin_video vaut None si mode == "webcam".
    """
    resultat = {"mode": None, "chemin": None}

    fenetre = tk.Tk()
    fenetre.title("AnonymArt")
    fenetre.resizable(False, False)

    largeur, hauteur = 380, 220
    fenetre.eval("tk::PlaceWindow . center")
    fenetre.geometry(f"{largeur}x{hauteur}")

    conteneur = tk.Frame(fenetre, padx=24, pady=24)
    conteneur.pack(fill="both", expand=True)

    titre = tk.Label(conteneur, text="Que voulez-vous flouter ?", font=("Segoe UI", 13, "bold"))
    titre.pack(pady=(0, 4))

    sous_titre = tk.Label(
        conteneur,
        text="Choisissez une source pour le floutage des visages.",
        font=("Segoe UI", 9),
        fg="#555555",
    )
    sous_titre.pack(pady=(0, 16))

    def choisir_webcam():
        resultat["mode"] = "webcam"
        fenetre.destroy()

    def choisir_video():
        chemin = filedialog.askopenfilename(
            title="Sélectionner une vidéo",
            filetypes=[
                ("Fichiers vidéo", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("Tous les fichiers", "*.*"),
            ],
        )
        if not chemin:
            return
        resultat["mode"] = "video"
        resultat["chemin"] = chemin
        fenetre.destroy()

    bouton_webcam = tk.Button(
        conteneur,
        text="📷  Activer le floutage sur la webcam",
        font=("Segoe UI", 10),
        command=choisir_webcam,
        height=2,
    )
    bouton_webcam.pack(fill="x", pady=(0, 10))

    bouton_video = tk.Button(
        conteneur,
        text="🎬  Importer une vidéo à flouter",
        font=("Segoe UI", 10),
        command=choisir_video,
        height=2,
    )
    bouton_video.pack(fill="x")

    fenetre.protocol("WM_DELETE_WINDOW", fenetre.destroy)
    fenetre.mainloop()

    if resultat["mode"] is None:
        raise SystemExit("Aucun mode sélectionné, arrêt du programme.")

    return resultat["mode"], resultat["chemin"]


def creer_detecteur():
    return cv2.FaceDetectorYN.create(MODEL, "", (320, 320), 0.3, 0.3, 5000)


def taille_entree(largeur, hauteur):
    """Arrondit la résolution au multiple de 32 inférieur, comme l'exige YuNet."""
    dw = max(32, (largeur // 32) * 32)
    dh = max(32, (hauteur // 32) * 32)
    return dw, dh


def flouter_visages(detector, frame, dw, dh):
    """Détecte les visages dans frame (résolu en dw x dh) et les floute en place."""
    hauteur, largeur = frame.shape[:2]
    petite = cv2.resize(frame, (dw, dh))
    _, visages = detector.detect(petite)

    if visages is None:
        visages = np.empty((0, 15), dtype=np.float32)

    sx, sy = largeur / dw, hauteur / dh
    for visage in visages:
        x, y, w, h = (visage[:4] * np.array([sx, sy, sx, sy])).astype(int)
        blur_face(frame, x, y, w, h)


def blur_video(chemin_video):
    """Floute les visages d'une vidéo importée et enregistre le résultat à côté du fichier source."""
    detector = creer_detecteur()

    cap = cv2.VideoCapture(chemin_video)
    if not cap.isOpened():
        raise SystemExit(f"Impossible d'ouvrir la vidéo : {chemin_video}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    largeur = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    hauteur = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    dw, dh = taille_entree(largeur, hauteur)
    detector.setInputSize((dw, dh))

    racine, _ = os.path.splitext(chemin_video)
    chemin_sortie = f"{racine}_floute.mp4"

    writer = cv2.VideoWriter(chemin_sortie, cv2.VideoWriter_fourcc(*"mp4v"),
                              fps, (largeur, hauteur))
    if not writer.isOpened():
        cap.release()
        raise SystemExit(f"Impossible de créer le fichier de sortie : {chemin_sortie}")

    index = 0
    print(f"Traitement de la vidéo : {chemin_video}")
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        flouter_visages(detector, frame, dw, dh)
        writer.write(frame)

        index += 1
        if total_frames > 0:
            print(f"\rImage {index}/{total_frames} ({index / total_frames:.0%})", end="", flush=True)

    print()
    cap.release()
    writer.release()

    print(f"Vidéo floutée enregistrée : {chemin_sortie}")
    return chemin_sortie


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
    detector = creer_detecteur()
    output_width, output_height = 1920, 1080

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("Impossible d'ouvrir la webcam.")

    ok, frame = cap.read()
    if not ok:
        raise SystemExit("Aucune image reçue depuis la webcam.")

    hauteur, largeur = frame.shape[:2]
    dw, dh = taille_entree(largeur, hauteur)
    detector.setInputSize((dw, dh))

    with pyvirtualcam.Camera(width=output_width, height=output_height, fps=20) as cam:
        print(f"Using virtual camera: {cam.device}")
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Flux interrompu.")
                break

            frame = cv2.flip(frame, 1)
            flouter_visages(detector, frame, dw, dh)

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
    mode, chemin_video = choisir_mode()

    if mode == "webcam":
        detect_faces()
    elif mode == "video":
        blur_video(chemin_video)