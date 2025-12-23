# Employee Document Scan - Full Documentation

This document contains the full setup, architecture, and usage guide for the **Employee Document Scan** app and local image watcher.

---

## Overview

The Employee Document Scan app allows scanning and attaching employee ID documents to ERPNext.  

**Features:**
- Local image watcher to capture scanned ID images
- Automatic creation of **Scanned Documents**
- **Scan & Attach ID** workflow on Employee form
- MRZ data parsing and auto-population of Employee fields

**Note:** This solution is designed for **local workstation scanners** and integrates seamlessly with Frappe / ERPNext. It is **not intended for production server use**.

---

## Features

- Watches a scanner output folder for overwritten images (e.g., `ImageVis.png`)  
- Captures first and second scans as **Document Image 1** and **Document Image 2**  
- Uploads both images to ERPNext via REST API  
- Creates a **Scanned Documents** record  
- Employee form can load the latest scanned document and attach it to fields:
  - `custom_passport_front_image`
  - `custom_passport_back_image`
  - `custom_nationality`
- MRZ parsing populates employee fields automatically:
  - First Name
  - Last Name
  - Date of Birth
  - Passport Number
  - Nationality
  - Place of Issue

---

## Architecture

### Components

1. **Scanner Software**  
   - Produces image files (e.g., `ImageVis.png`) for each ID scan

2. **Local Image Watcher (`local_image_watcher.py`)**  
   - Monitors the scanner output folder for file changes  
   - Captures front and back images sequentially  
   - Uploads images via ERPNext REST API

3. **ERPNext / Frappe**  
   - Receives uploaded images and creates **Scanned Documents**  
   - Employee form can attach scanned documents to employee records

### SetUp
- Install Python on local Windows machine on which the scanner is connected.
- Copy the `local_image_watcher` folder from the app and paste it onto the local Windows machine where the scanner is connected.  
- Run the `run_proxy.bat` file **before starting the document scanning**.  
- Also, start the **Output Wedge TRYSYS** from the Gemalto Thales SDK located in the `Bin` folder.
