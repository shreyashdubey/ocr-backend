import os
import logging
from google.cloud import vision
import pytesseract
from PIL import Image
import cv2
import numpy as np
from typing import Tuple, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        self.enable_premium = os.getenv('ENABLE_PREMIUM_OCR', 'false').lower() == 'true'
        if self.enable_premium:
            try:
                self.vision_client = vision.ImageAnnotatorClient()
                logger.info("Google Cloud Vision client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Google Cloud Vision: {e}")
                self.enable_premium = False

    def process_image_with_tesseract(self, image_path: str) -> Tuple[str, float]:
        """Process image with Tesseract OCR"""
        try:
            # Read and preprocess image
            img = cv2.imread(image_path)
            if img is None:
                # Try with PIL if OpenCV fails
                pil_image = Image.open(image_path)
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                # Save as JPEG for OpenCV
                pil_image.save(image_path, 'JPEG')
                img = cv2.imread(image_path)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

            # Perform OCR
            text = pytesseract.image_to_string(gray)
            confidence_data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            confidence_scores = [float(conf) for conf in confidence_data['conf'] if conf != '-1']
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

            return text.strip(), avg_confidence

        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            raise

    def process_image_with_google_vision(self, image_path: str) -> Tuple[str, float]:
        """Process image with Google Cloud Vision API"""
        try:
            # Read image file
            with open(image_path, 'rb') as image_file:
                content = image_file.read()

            image = vision.Image(content=content)
            
            # Perform OCR
            response = self.vision_client.text_detection(image=image)
            texts = response.text_annotations

            if not texts:
                return "", 0.0

            # First element contains all text
            full_text = texts[0].description

            # Calculate confidence (average of word confidences)
            confidence = 0.0
            if len(texts) > 1:  # Skip first element as it's the full text
                word_confidences = [word.confidence for word in texts[1:] if word.confidence]
                confidence = sum(word_confidences) * 100 / len(word_confidences) if word_confidences else 0.0

            if response.error.message:
                raise Exception(response.error.message)

            return full_text.strip(), confidence

        except Exception as e:
            logger.error(f"Google Cloud Vision error: {e}")
            raise

    def process_image(self, image_path: str, use_premium: bool = False) -> Tuple[str, float]:
        """Process image with either Tesseract or Google Cloud Vision based on premium status"""
        if use_premium and self.enable_premium:
            logger.info("Using Google Cloud Vision for OCR")
            return self.process_image_with_google_vision(image_path)
        else:
            logger.info("Using Tesseract for OCR")
            return self.process_image_with_tesseract(image_path)

# Create a singleton instance
ocr_service = OCRService() 