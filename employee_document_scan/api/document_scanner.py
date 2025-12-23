import frappe
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import os
import urllib.parse
import re


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

    # Date of Birth (always labeled near DOB)
    m = re.search(
        r'(Date|Bate|Dafe)\s*of\s*Birth.*?(\d{2}/\d{2}/\d{4})',
        text,
        re.IGNORECASE
    )
    if m:
        data["date_of_birth"] = m.group(2)

    # Nationality
    m = re.search(r'Nationality[:\s]+([A-Za-z]+)', text)
    if m:
        data["nationality"] = m.group(1)

    # ---- DATE EXTRACTION (KEY PART) ----
    all_dates = re.findall(r'\b\d{2}/\d{2}/\d{4}\b', text)

    # Remove DOB from list
    if "date_of_birth" in data and data["date_of_birth"] in all_dates:
        all_dates.remove(data["date_of_birth"])

    # Sort dates chronologically
    def to_date(d):
        return frappe.utils.getdate(d)

    all_dates = sorted(set(all_dates), key=to_date)

    # Assign issuing & expiry dates
    if len(all_dates) >= 2:
        data["issuing_date"] = all_dates[0]
        data["expiry_date"] = all_dates[-1]

    # Sex / Gender
    if re.search(r'\bM\b|\bMale\b|Maly', text, re.IGNORECASE):
        data["sex"] = "M"
    elif re.search(r'\bF\b|\bFemale\b|Femaie', text, re.IGNORECASE):
        data["sex"] = "F"

    return data




def read_passport_image(doc, method=None):
    """
    ERPNext hook:
    Reads attached Emirates ID image,
    extracts fields, and fills Employee record.
    """

    if not doc.custom_passport_front_image:
        frappe.msgprint("No ID image attached.")
        return

    # Fetch file document
    try:
        file_doc = frappe.get_doc(
            "File",
            {"file_url": doc.custom_passport_front_image}
        )
    except frappe.DoesNotExistError:
        frappe.msgprint("File not found.")
        return

    # Build file path
    site_path = frappe.get_site_path()
    file_path = os.path.join(
        site_path,
        "public",
        file_doc.file_url.lstrip("/")
    )
    file_path = urllib.parse.unquote(file_path)

    if not os.path.exists(file_path):
        frappe.msgprint("Image not found on server.")
        return

    # OCR
    image = Image.open(file_path)
    image = preprocess_with_pil(image)

    tesseract_config = "--oem 3 --psm 6 -l eng+ara"
    ocr_text = pytesseract.image_to_string(image, config=tesseract_config)

    # Extract data
    data = extract_uae_id_fields(ocr_text)

    # Show extracted data
    frappe.msgprint(
        "Extracted Data:\n" +
        "\n".join(f"{k}: {v}" for k, v in data.items())
    )

    # ==============================
    # OPTIONAL: SAVE INTO EMPLOYEE
    # ==============================
    if data.get("id_number"):
        doc.custom_emirates_id_number = data["id_number"]

    if data.get("name"):
        doc.employee_name = data["name"]

    if data.get("date_of_birth"):
        doc.date_of_birth = frappe.utils.getdate(
            data["date_of_birth"]
        )

    if data.get("nationality"):
        doc.nationality = data["nationality"]

    if data.get("issuing_date"):
        doc.custom_id_issue_date = frappe.utils.getdate(
            data["issuing_date"]
        )

    if data.get("expiry_date"):
        doc.custom_id_expiry_date = frappe.utils.getdate(
            data["expiry_date"]
        )

    if data.get("sex"):
        doc.gender = "Male" if data["sex"] == "M" else "Female"

    # doc.save(ignore_permissions=True)
