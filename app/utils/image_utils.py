import cv2
import numpy as np
from typing import Tuple, Optional, List
import imutils
from app.utils.logging import logger


def load_image(image_data: bytes) -> np.ndarray:
    """Load image from bytes data"""
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Failed to decode image")
    return image


def resize_image(image: np.ndarray, width: int = 1000) -> np.ndarray:
    """Resize image maintaining aspect ratio"""
    height = int(image.shape[0] * width / image.shape[1])
    return cv2.resize(image, (width, height))


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert image to grayscale"""
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def apply_threshold(image: np.ndarray, threshold_value: int = 180) -> np.ndarray:
    """Apply binary threshold to image"""
    _, thresh = cv2.threshold(image, threshold_value, 255, cv2.THRESH_BINARY_INV)
    return thresh


def apply_adaptive_threshold(image: np.ndarray) -> np.ndarray:
    """Apply adaptive threshold for better bubble detection"""
    return cv2.adaptiveThreshold(
        image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2
    )


def remove_noise(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """Remove noise using morphological operations"""
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
    return image


def detect_edges(image: np.ndarray, low_threshold: int = 50, high_threshold: int = 150) -> np.ndarray:
    """Detect edges using Canny edge detector"""
    return cv2.Canny(image, low_threshold, high_threshold)


def find_contours(image: np.ndarray) -> List:
    """Find contours in the image"""
    contours = cv2.findContours(image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    return sorted(contours, key=cv2.contourArea, reverse=True)


def detect_skew_angle(image: np.ndarray) -> float:
    """Detect skew angle of the image using Hough Line Transform"""
    edges = detect_edges(image)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    
    if lines is None:
        return 0.0
    
    angles = []
    for rho, theta in lines[:, 0]:
        angle = np.degrees(theta) - 90
        if -45 <= angle <= 45:
            angles.append(angle)
    
    if angles:
        return np.median(angles)
    return 0.0


def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """Rotate image by given angle"""
    if abs(angle) < 0.5:  # Skip rotation for very small angles
        return image
    
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    # Calculate new dimensions
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    
    # Adjust rotation matrix for translation
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]
    
    return cv2.warpAffine(image, M, (new_w, new_h), borderValue=(255, 255, 255))


def find_document_corners(image: np.ndarray) -> Optional[np.ndarray]:
    """Find the four corners of the OMR sheet"""
    gray = convert_to_grayscale(image)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = detect_edges(blurred)
    
    contours = find_contours(edged)
    
    for contour in contours[:5]:  # Check top 5 largest contours
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        
        if len(approx) == 4:
            return approx.reshape(4, 2)
    
    return None


def order_points(pts: np.ndarray) -> np.ndarray:
    """Order points in top-left, top-right, bottom-right, bottom-left order"""
    rect = np.zeros((4, 2), dtype="float32")
    
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect


def four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Apply perspective transform to get top-down view"""
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_width = max(int(width_a), int(width_b))
    
    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_height = max(int(height_a), int(height_b))
    
    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype="float32")
    
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (max_width, max_height))
    
    return warped


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """Enhance image contrast using CLAHE"""
    if len(image.shape) == 3:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    else:
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        return clahe.apply(image)


def assess_image_quality(image: np.ndarray) -> Tuple[str, float, str, str]:
    """Assess image quality based on various metrics"""
    gray = convert_to_grayscale(image) if len(image.shape) == 3 else image
    
    # Check resolution
    height, width = gray.shape
    if width < 800 or height < 600:
        resolution = "low"
    elif width < 1200 or height < 900:
        resolution = "adequate"
    else:
        resolution = "high"
    
    # Check brightness
    mean_brightness = np.mean(gray)
    if mean_brightness < 100:
        brightness = "dark"
    elif mean_brightness > 200:
        brightness = "bright"
    else:
        brightness = "normal"
    
    # Check contrast
    std_dev = np.std(gray)
    if std_dev < 30:
        contrast = "low"
    elif std_dev > 80:
        contrast = "high"
    else:
        contrast = "normal"
    
    # Overall quality assessment
    quality_score = 0
    if resolution in ["adequate", "high"]:
        quality_score += 1
    if brightness == "normal":
        quality_score += 1
    if contrast == "normal":
        quality_score += 1
    
    if quality_score == 3:
        quality = "excellent"
    elif quality_score == 2:
        quality = "good"
    elif quality_score == 1:
        quality = "adequate"
    else:
        quality = "poor"
    
    # Calculate skew angle
    skew_angle = detect_skew_angle(gray)
    
    return quality, skew_angle, brightness, contrast


def detect_reference_marks(image: np.ndarray) -> List[Tuple[int, int]]:
    """Detect reference marks (corner markers) on the OMR sheet"""
    gray = convert_to_grayscale(image) if len(image.shape) == 3 else image
    
    # Look for dark circular marks in corners
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=100,
        param1=50,
        param2=30,
        minRadius=5,
        maxRadius=20
    )
    
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        
        # Filter circles in corner regions
        h, w = gray.shape
        corner_marks = []
        corner_regions = [
            (0, w//4, 0, h//4),  # Top-left
            (3*w//4, w, 0, h//4),  # Top-right
            (0, w//4, 3*h//4, h),  # Bottom-left
            (3*w//4, w, 3*h//4, h)  # Bottom-right
        ]
        
        for (x, y, r) in circles:
            for (x1, x2, y1, y2) in corner_regions:
                if x1 <= x <= x2 and y1 <= y <= y2:
                    corner_marks.append((x, y))
                    break
        
        return corner_marks
    
    return []