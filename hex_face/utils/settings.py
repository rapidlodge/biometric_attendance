import frappe
# from pathlib import Path
import frappe

def get_face_settings():
    doc = frappe.get_doc("Face Attendance Settings", "Face Attendance Settings")

    return {
        "api_key": frappe.utils.password.get_decrypted_password(
            "Face Attendance Settings", doc.name, "api_key"
        ).strip(),
        "api_secret": frappe.utils.password.get_decrypted_password(
            "Face Attendance Settings", doc.name, "api_secret"
        ).strip(),
        "model": doc.model,
        "stop": doc.stop,
        "site_url": (doc.site_url or "").strip(),
        "attendance_method": (doc.attendance_method or "").strip(),
        "training_path": (doc.training_path or "").strip(),
        "output_path": (doc.output_path or "").strip(),
        "validation_path": (doc.validation_path or "").strip(),
        "encodings_path": (doc.encodings_path or "").strip(),
        "yolo_model_path": (doc.yolo_model_path or "").strip(),
        "spoof_confidence_threshold": float(doc.spoof_confidence_threshold or 0.80),
    }
