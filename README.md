# AgriSmart AI - Farmer Welfare Portal

AgriSmart AI is a complete Flask + SQLite web application inspired by Indian government agriculture service portals. It supports farmer registration, OCR document verification, status tracking, farmer self-service dashboards, admin approval workflows, analytics charts, multilingual UI, and a basic AI help bot.

## Folder Structure

```text
AgriSmart AI/
|-- app.py
|-- agrismart.db               # Created automatically on first run
|-- requirements.txt
|-- schema.sql
|-- README.md
|-- static/
|   |-- css/
|   |   `-- style.css
|   |-- js/
|   |   `-- app.js
|   `-- uploads/              # Uploaded images are saved here
`-- templates/
    |-- base.html
    |-- home.html
    |-- register.html
    |-- track_status.html
    |-- admin_login.html
    |-- admin_dashboard.html
    `-- farmer_dashboard.html
```

## Features

- Government-style responsive homepage with green and blue theme
- Farmer registration with validation and unique Farmer ID
- Aadhaar OCR verification using `pytesseract`
- Status tracking by phone or Aadhaar
- Secure admin session login
- Farmer dashboard for subsidy, insurance, and complaints
- Admin approvals for farmers, subsidy, insurance, and complaints
- Analytics charts with Chart.js
- Rule-based FAQ chatbot
- English and Tamil language toggle

## Run Instructions in VS Code

1. Open the project folder in VS Code.
2. Open the integrated terminal in VS Code.
3. Create a virtual environment:

```powershell
python -m venv venv
```

4. Activate the environment:

```powershell
.\venv\Scripts\activate
```

5. Install the required packages:

```powershell
pip install -r requirements.txt
```

6. Install the Tesseract OCR engine on Windows if it is not already installed.
   Recommended default path:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

7. If needed, add the Tesseract install path to your system PATH, or set it inside `app.py` using:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

8. Start the Flask app:

```powershell
python app.py
```

9. Open the browser and visit:

```text
http://127.0.0.1:5000
```

## Default Admin Login

- Username: `admin`
- Password: `admin123`

## Notes

- The SQLite database file `agrismart.db` is created automatically on first run.
- Uploaded Aadhaar and land images are saved in `static/uploads/`.
- Farmer dashboard access is enabled only after admin approval.
- OCR status becomes `Verified` only when both name and Aadhaar number match extracted Aadhaar text.
