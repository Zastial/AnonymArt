# AnonymArt

AnonymArt ouvre la webcam, détecte les visages avec **YuNet**, puis floute les zones détectées. L'image traitée peut aussi être envoyée vers une caméra virtuelle avec `pyvirtualcam`.

## Prérequis

- Python 3.9 à 3.14
- Une webcam
- Le fichier `face_detection_yunet.onnx` à la racine du projet
- Une caméra virtuelle si la sortie doit être utilisée dans Zoom, Teams, OBS, etc.

## Installation

Depuis le dossier du projet, créez un environnement virtuel.

### Linux et macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si PowerShell bloque l'activation, utilisez l'invite de commandes Windows :

```bat
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Vérifiez l'installation :

```bash
python -c "import cv2, numpy, pyvirtualcam; print(cv2.__version__)"
```

La version attendue d'OpenCV est `5.0.0`.

> N'installez pas `opencv-python-headless` et n'installez pas plusieurs paquets `opencv-*` dans le même environnement. `cv2.imshow()` nécessite la version graphique `opencv-python`.

## Modèle YuNet

Le modèle est déjà fourni dans ce dépôt sous le nom `face_detection_yunet.onnx`. S'il est absent, téléchargez la version compatible avec OpenCV 5 :

```bash
curl -L -o face_detection_yunet.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2026may.onnx
```

Le fichier doit faire environ 230 Ko. Un fichier d'environ 130 octets indique généralement un pointeur Git LFS et ne peut pas être utilisé par OpenCV.

## Caméra virtuelle

`pyvirtualcam` est une interface Python : il lui faut une caméra virtuelle installée par le système.

- **macOS** : installez [OBS Studio](https://obsproject.com/download), puis activez `OBS Virtual Camera`.
- **Windows** : installez [OBS Studio](https://obsproject.com/download), puis activez `OBS Virtual Camera`.
- **Linux** : installez une caméra `v4l2loopback`, par exemple `v4l2loopback-dkms` et `v4l2loopback-utils` selon votre distribution. OBS Studio peut ensuite fournir la caméra virtuelle.

Sans caméra virtuelle, la détection locale avec la fenêtre OpenCV peut fonctionner, mais la sortie ne sera pas disponible dans les autres applications.

## Lancer le programme

Activez d'abord `.venv`, puis lancez :

```bash
python main.py
```

Autorisez l'accès à la caméra lorsque le système le demande. Dans la fenêtre OpenCV, `q` ou `Échap` quitte le programme.

## Dépannage

### La webcam ne s'ouvre pas

- Vérifiez que la caméra n'est pas déjà utilisée par Zoom, Teams, OBS ou une autre application.
- Sur macOS, autorisez le terminal ou l'éditeur utilisé dans **Réglages système > Confidentialité et sécurité > Caméra**.
- Sous Windows, vérifiez **Paramètres > Confidentialité et sécurité > Caméra**.
- Sous Linux, vérifiez les permissions du périphérique `/dev/video*`.

### `Can't read ONNX file`

Vérifiez que `face_detection_yunet.onnx` existe dans le même dossier que `main.py` et qu'il s'agit bien du modèle complet, pas d'un pointeur Git LFS.

### `No virtual camera found` ou erreur `pyvirtualcam`

Installez et démarrez une caméra virtuelle compatible avec votre système, puis relancez le programme. Vérifiez aussi que l'application qui utilise la caméra virtuelle n'est pas déjà en conflit avec elle.

### La fenêtre OpenCV ne s'affiche pas

Vérifiez que `opencv-python` est installé et que `opencv-python-headless` n'est pas installé dans `.venv` :

```bash
python -m pip list | grep opencv
```

Sous Windows PowerShell, remplacez `grep` par :

```powershell
python -m pip list | Select-String opencv
```

## Arborescence

```text
AnonymArt/
├── .venv/                       # environnement virtuel local, non versionné
├── face_detection_yunet.onnx    # modèle YuNet
├── main.py                      # programme principal
├── requirements.txt             # dépendances Python
└── README.md
```
