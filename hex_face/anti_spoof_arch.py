from ultralytics import YOLO 
import cv2 
model = YOLO("/workspace/development/frappe-bench/apps/hex_face/hex_face/Custom-Data-YOLOv8-Person-Detection/ckpts/best.pt")
def detect_person(image_path): 
    img = cv2.imread(image_path) 
    results = model(img) 
    output = [] 
    for r in results: # results is a list of Results objects 
        for box in r.boxes: # r.boxes is a list of boxes 
            output.append({ "xyxy": box.xyxy.tolist()[0], # bounding box coords 
                           "confidence": float(box.conf[0]), 
                           "class_id": int(box.cls[0]) }) 
    return output
import frappe

@frappe.whitelist(allow_guest=True) 
def detect_person_from_image(image_file): 
    try: 
        results = detect_person(image_file) 
        print(results) 
        return {"status": "success", "data": results} 
    except Exception as e: 
        return {"status": "error", "message": str(e)} 
    
detect_person_from_image("/workspace/development/frappe-bench/apps/hex_face/hex_face/validation/HR-EMP-00001/2025-09-11/shuvospoof.jpg")