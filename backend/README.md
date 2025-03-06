# OCR Backend Service

This is the backend service for the OCR Dashboard application. It provides REST APIs for OCR processing of images and managing scan history.

## Prerequisites

- Python 3.8 or higher
- Tesseract OCR engine
- Virtual environment (recommended)

## Installation

1. Install Tesseract OCR:
   - macOS: `brew install tesseract`
   - Ubuntu: `sudo apt-get install tesseract-ocr`
   - Windows: Download installer from https://github.com/UB-Mannheim/tesseract/wiki

2. Set up Python environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Server

```bash
python run.py
```

The server will start at http://localhost:5000

## Running Tests

```bash
pytest
```

## API Endpoints

- `POST /api/scan` - Perform OCR on an uploaded image
- `GET /api/scans` - Get scan history
- `GET /api/scans/<id>` - Get a specific scan
- `DELETE /api/scans/<id>` - Delete a specific scan
- `GET /api/images/<filename>` - Serve processed images

## Development

The application uses:
- Flask for the web framework
- SQLite for data storage
- Tesseract for OCR processing
- OpenCV for image processing

Images are stored in the `uploads` directory, and the SQLite database is created in the `instance` directory. 