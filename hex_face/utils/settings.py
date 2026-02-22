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
    }
