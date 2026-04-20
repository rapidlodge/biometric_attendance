# Copyright (c) 2025, Hex Flow and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FaceAttendanceSettings(Document):
	def validate(self):
		self.site_url = (self.site_url or "").strip()
		self.attendance_method = (
			self.attendance_method
			or "/api/method/hrms.hr.doctype.employee_checkin.employee_checkin.add_log_based_on_employee_field"
		).strip()
		self.training_path = (
			self.training_path
			or "/workspace/development/frappe-bench/apps/hex_face/hex_face/training"
		).strip()
		self.output_path = (
			self.output_path
			or "/workspace/development/frappe-bench/apps/hex_face/hex_face/output"
		).strip()
		self.validation_path = (
			self.validation_path
			or "/workspace/development/frappe-bench/apps/hex_face/hex_face/validation"
		).strip()
		self.encodings_path = (
			self.encodings_path
			or f"{self.output_path}/encodings.pkl"
		).strip()
		self.yolo_model_path = (
			self.yolo_model_path
			or "/workspace/development/frappe-bench/apps/hex_face/hex_face/Custom-Data-YOLOv8-Person-Detection/ckpts/best.pt"
		).strip()
		self.spoof_confidence_threshold = float(self.spoof_confidence_threshold or 0.8)

		if self.spoof_confidence_threshold <= 0 or self.spoof_confidence_threshold > 1:
			frappe.throw("Spoof Confidence Threshold must be greater than 0 and at most 1.")
