import os
import shutil
from pathlib import Path
import frappe
from ..api import encode_known_faces

TRAINING_DIR = Path("/workspace/development/frappe-bench/apps/hex_face/hex_face/training")

# def handle_new_employee(doc, method=None):
#     """
#     Run only when a new Employee is created
#     OR when the image field changes.
#     """
#     # 1. Handle new insert
#     if method == "after_insert":
#         if doc.image:
#             sync_employee_images(doc)
#         return

#     # 2. Handle updates (only if image changed)
#     if method == "on_update":
#         old_doc = doc.get_doc_before_save()
#         old_image = old_doc.image if old_doc else None

#         if doc.image and doc.image != old_image:
#             sync_employee_images(doc)


@frappe.whitelist()
def sync_employee_images():
    """
    Sync employee images from Employee doctype into training/<employee_id>/ folders.
    """

    # Ensure training folder exists
    TRAINING_DIR.mkdir(parents=True, exist_ok=True)

    # Fetch employees with images
    employees = frappe.get_all(
        "Employee",
        fields=["name", "employee_name", "image"]
    )

    copied_files = []

    for emp in employees:
        if not emp.image:
            continue  # no image uploaded

        # Image path looks like: /files/emp1.jpg
        image_path = emp.image.lstrip("/")  
        full_image_path = frappe.get_site_path("public", image_path)

        if not os.path.exists(full_image_path):
            frappe.log_error(f"File not found: {full_image_path}")
            continue

        # Create folder per employee (e.g., training/EMP-001/)
        emp_folder = TRAINING_DIR / emp.name
        emp_folder.mkdir(parents=True, exist_ok=True)

        # Copy image into employee folder
        dest_file = emp_folder / os.path.basename(full_image_path)
        shutil.copy(full_image_path, dest_file)

        copied_files.append(str(dest_file))
        knwn_face = encode_known_faces()

    return {"status": "success", "copied": knwn_face}

