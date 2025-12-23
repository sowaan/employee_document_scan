# Copyright (c) 2025, Fariz Khanzada and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import os
import urllib.parse
import re
import json

class ScannedDocuments(Document):
    # def before_save(self):
    #     # Automatically run OCR before save
    #     extract_ocr_from_scanned_document(self)
    pass

def preprocess_with_pil(image):
    """Improve image quality for OCR using PIL only"""
    image = image.convert("L")
    image = ImageEnhance.Contrast(image).enhance(2.5)
    image = ImageEnhance.Sharpness(image).enhance(2.0)
    image = image.filter(ImageFilter.MedianFilter(size=3))
    image = image.point(lambda x: 0 if x < 140 else 255, "1")
    return image

def extract_uae_id_fields(text):
    data = {}

    # Emirates ID number
    m = re.search(r'\b784-\d{4}-\d{7}-\d\b', text)
    if m:
        data["id_number"] = m.group()

    # Name
    m = re.search(r'Name[:\s]+([A-Za-z ]{5,})', text)
    if m:
        data["name"] = m.group(1).strip()

    # Date of Birth
    m = re.search(r'(Date|Bate|Dafe)\s*of\s*Birth.*?(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
    if m:
        data["date_of_birth"] = m.group(2)

    # Nationality
    m = re.search(r'Nationality[:\s]+([A-Za-z]+)', text)
    if m:
        data["nationality"] = m.group(1)

    # Extract all dates
    all_dates = re.findall(r'\b\d{2}/\d{2}/\d{4}\b', text)
    if "date_of_birth" in data and data["date_of_birth"] in all_dates:
        all_dates.remove(data["date_of_birth"])

    def to_date(d): return frappe.utils.getdate(d)
    all_dates = sorted(set(all_dates), key=to_date)

    if len(all_dates) >= 2:
        data["issuing_date"] = all_dates[0]
        data["expiry_date"] = all_dates[-1]

    # Gender
    if re.search(r'\bM\b|\bMale\b|Maly', text, re.IGNORECASE):
        data["sex"] = "M"
    elif re.search(r'\bF\b|\bFemale\b|Femaie', text, re.IGNORECASE):
        data["sex"] = "F"

    return data

@frappe.whitelist()
def extract_ocr_from_scanned_document(doc):
    """
    Reads front_image of Scanned Documents,
    runs OCR, extracts fields, and saves in extracted_data
    """
    if not doc.front_image:
        frappe.msgprint("No front image attached.")
        return

    try:
        file_doc = frappe.get_doc("File", {"file_url": doc.front_image})
    except frappe.DoesNotExistError:
        frappe.msgprint("Front image file not found.")
        return

    site_path = frappe.get_site_path()
    file_path = os.path.join(site_path, "public", file_doc.file_url.lstrip("/"))
    file_path = urllib.parse.unquote(file_path)

    if not os.path.exists(file_path):
        frappe.msgprint(f"Front image not found on server: {file_path}")
        return

    # OCR
    image = Image.open(file_path)
    image = preprocess_with_pil(image)
    tesseract_config = "--oem 3 --psm 6 -l eng+ara"
    ocr_text = pytesseract.image_to_string(image, config=tesseract_config)

    # Extract fields
    data = extract_uae_id_fields(ocr_text)

    # Save extracted data as JSON
    doc.extracted_data = json.dumps(data, indent=4)
