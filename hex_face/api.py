from pathlib import Path
from collections import Counter
from datetime import datetime
import base64, re, numpy as np, cv2, pickle, requests, json
import frappe, face_recognition
from hex_face.utils.settings import get_face_settings
from ultralytics import YOLO  # Added for anti-spoof7
# ==============================
# Configurations (⚠️ keep secrets outside code)
# ==============================

settings = get_face_settings()

API_KEY = settings.get("api_key", "").strip()
API_SECRET = settings.get("api_secret", "").strip()
MODEL = settings["model"]
SITE_URL = settings.get("site_url", "").strip()
REQUEST_ATTENDANCE_METHOD = settings.get(
    "attendance_method",
    "/api/method/hrms.hr.doctype.employee_checkin.employee_checkin.add_log_based_on_employee_field",
).strip()

DEFAULT_TRAINING_DIR = Path(
    settings.get("training_path")
    or "/workspace/development/frappe-bench/apps/hex_face/hex_face/training"
)
DEFAULT_OUTPUT_DIR = Path(
    settings.get("output_path")
    or "/workspace/development/frappe-bench/apps/hex_face/hex_face/output"
)
DEFAULT_VALIDATION_DIR = Path(
    settings.get("validation_path")
    or "/workspace/development/frappe-bench/apps/hex_face/hex_face/validation"
)
DEFAULT_ENCODINGS_PATH = Path(
    settings.get("encodings_path")
    or str(DEFAULT_OUTPUT_DIR / "encodings.pkl")
)
YOLO_MODEL_PATH = settings.get("yolo_model_path") or (
    "/workspace/development/frappe-bench/apps/hex_face/hex_face/Custom-Data-YOLOv8-Person-Detection/ckpts/best.pt"
)
SPOOF_CONFIDENCE_THRESHOLD = float(settings.get("spoof_confidence_threshold") or 0.80)

auth_header = {"Authorization": f"token {API_KEY}:{API_SECRET}"}

# ==============================
# Folder Setup
# ==============================
DEFAULT_TRAINING_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

print(f"Using encodings from: {DEFAULT_ENCODINGS_PATH}")

# ==============================
# Anti-Spoof Model (YOLO)
# ==============================
yolo_model = YOLO(YOLO_MODEL_PATH)

def detect_person(image_path):
    img = cv2.imread(image_path)
    results = yolo_model(img)
    output = []
    for r in results:
        for box in r.boxes:
            output.append({
                "xyxy": box.xyxy.tolist()[0],
                "confidence": float(box.conf[0]),
                "class_id": int(box.cls[0])
            })
    return output


# ==============================
# Helper - Save Snapshot to Validation Folder
# ==============================
def save_to_validation(image_bytes: bytes, employee_name: str):
    today = datetime.now().strftime("%Y-%m-%d")

    folder_path = DEFAULT_VALIDATION_DIR / employee_name / today
    folder_path.mkdir(parents=True, exist_ok=True)

    filename = f"{datetime.now().strftime('%H-%M-%S')}_snapshot.jpg"
    file_path = folder_path / filename

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    return str(file_path)


# ==============================
# Face Encoding
# ==============================
def encode_known_faces(model: str = "hog", encodings_location=DEFAULT_ENCODINGS_PATH) -> None:
    names, encodings = [], []

    for filepath in DEFAULT_TRAINING_DIR.glob("**/*"):
        if filepath.is_file():
            name = filepath.parent.name
            image = face_recognition.load_image_file(filepath)
            face_encs = face_recognition.face_encodings(image, model=model)

            if face_encs:
                for encoding in face_encs:
                    encodings.append(encoding)
                    names.append(name)
            else:
                print(f"No faces found in {filepath}, skipping...")
                return f"No faces found in {filepath}, skipping..."

    print(f"Encoded {len(encodings)} faces from {len(set(names))} people.")

    name_encodings = {"names": names, "encodings": encodings}
    with encodings_location.open(mode="wb") as f:
        pickle.dump(name_encodings, f)
    return f"Encoded {len(encodings)} faces from {len(set(names))} Employee."


# ==============================
# Recognition + Spoof Detection
# ==============================
@frappe.whitelist()
def recognized_faces(image=None, images=None, office_id=None, model: str = "hog"):
    try:
        office_id = (office_id or "").strip()
        if not office_id:
            return {"status": "failed", "reason": "office_id is required"}

        if images:
            if isinstance(images, str):
                try:
                    images = json.loads(images)
                except Exception:
                    images = [images]
        elif image:
            images = [image]
        else:
            return {"status": "failed", "reason": "No image(s) provided"}

        results = []
        for img in images:
            if isinstance(img, list):
                img = img[0]
            if not isinstance(img, str):
                continue

            img = img.strip()
            print("DEBUG IMG START:", img[:40])

            # Decode image
            if "," in img:
                _, img_data = img.split(",", 1)
            else:
                img_data = img
            img_bytes = base64.b64decode(img_data)

            # Save snapshot temporarily for YOLO check
            temp_path = str(DEFAULT_OUTPUT_DIR / "temp_check.jpg")
            with open(temp_path, "wb") as f:
                f.write(img_bytes)

            # 🔍 Anti-Spoof Check
            yolo_results = detect_person(temp_path)
            if not yolo_results:
                save_to_validation(img_bytes, "spoof_detected")
                return {"status": "failed", "reason": "No person detected (spoof)"}

            # Take highest confidence
            max_conf = max(obj["confidence"] for obj in yolo_results)
            print("YOLO Confidence:", max_conf)

            if max_conf < SPOOF_CONFIDENCE_THRESHOLD:
                save_to_validation(img_bytes, "spoof_detected")
                return {"status": "failed", "reason": f"Spoof detected (confidence={max_conf:.2f})"}

            # ✅ Real image → proceed with face recognition
            result = _process_face(img, model)
            results.append(result)

            if result.get("status") == "success":
                save_to_validation(img_bytes, result.get("name"))
            else:
                save_to_validation(img_bytes, "unknown")

        success_results = [r for r in results if r.get("status") == "success"]
        if success_results:
            from collections import Counter
            final_name = Counter([r["name"] for r in success_results]).most_common(1)[0][0]

            if office_id != final_name:
                return {
                    "status": "failed",
                    "reason": "Recognized employee does not match the provided office_id",
                }

            post_attendance_via_method(final_name)
            return {"status": "success", "name": final_name}

        return {"status": "failed", "reason": "No consistent recognition"}

    except Exception as e:
        frappe.log_error(message=str(e), title="Face Recognition Error")
        return {"status": "failed", "reason": str(e)}


def _process_face(image: str, model: str = MODEL):
    if not DEFAULT_ENCODINGS_PATH.exists():
        return {"status": "failed", "reason": "No encodings found. Please train first."}

    with DEFAULT_ENCODINGS_PATH.open(mode="rb") as f:
        name_encodings = pickle.load(f)

    image_data = re.sub("^data:image/.+;base64,", "", image)
    image_bytes = base64.b64decode(image_data)
    nparr = np.frombuffer(image_bytes, np.uint8)
    input_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    input_face_locations = face_recognition.face_locations(input_image, model=model)
    input_face_encodings = face_recognition.face_encodings(input_image, input_face_locations, model=model)

    if not input_face_encodings:
        return {"status": "failed", "reason": "No face detected"}

    for _, unknown_encoding in zip(input_face_locations, input_face_encodings):
        name = _recognize_face(unknown_encoding, name_encodings)
        if not name:
            return {"status": "failed", "reason": "User not recognized"}
        return {"status": "success", "name": name}


def _recognize_face(unknown_encoding, name_encodings):
    matches = face_recognition.compare_faces(name_encodings["encodings"], unknown_encoding)
    votes = Counter(
        name for match, name in zip(matches, name_encodings["names"]) if match
    )
    if votes:
        return votes.most_common(1)[0][0]


# ==============================
# Attendance Posting
# ==============================
@frappe.whitelist()
def post_attendance_via_method(office_id, latitude=None, longitude=None, location_name=None):
    if settings["stop"]:
        return {
            "status": "validation_only",
            "employee": office_id,
            "message": "Auto attendance disabled, only validation done."
        }

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "employee_field_value": office_id,
        "log_type": "IN",
        "employee_latitude": latitude or "",
        "employee_longitude": longitude or "",
        "employee_location_name": location_name or "",
        "timestamp": timestamp,
    }

    if SITE_URL and REQUEST_ATTENDANCE_METHOD:
        url = SITE_URL + REQUEST_ATTENDANCE_METHOD
        r = requests.post(url, json=payload, headers=auth_header, timeout=15)
        return r.status_code == 200
    return False
