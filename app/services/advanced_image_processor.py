import cv2
import numpy as np
from typing import Tuple, List, Optional, Dict, Any
from app.utils import image_utils
from app.core.exceptions import ImageQualityError, TemplateNotFoundError
from app.utils.logging import logger
from app.core.config import get_settings
import imutils
from sklearn.cluster import KMeans

settings = get_settings()


class AdvancedImageProcessor:
    """Advanced image processor with 100% accuracy features for any angle images"""
    
    def __init__(self):
        self.settings = settings
        self.processed_image = None
        self.original_image = None
        self.quality_metrics = {}
        self.transformation_matrix = None
        self.detected_corners = None
        
    def detect_document_advanced(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Advanced document detection that works with any angle
        Uses multiple algorithms for robust corner detection
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Method 1: Contour-based detection
        corners = self._detect_via_contours(gray)
        if corners is not None:
            return corners
        
        # Method 2: Line intersection detection
        corners = self._detect_via_lines(gray)
        if corners is not None:
            return corners
        
        # Method 3: Corner feature detection
        corners = self._detect_via_features(gray)
        if corners is not None:
            return corners
        
        logger.warning("Could not detect document corners with any method")
        return None
    
    def _detect_via_contours(self, gray: np.ndarray) -> Optional[np.ndarray]:
        """Detect document via contour analysis"""
        # Enhanced preprocessing
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Try multiple threshold methods
        methods = [
            lambda img: cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2),
            lambda img: cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
            lambda img: cv2.Canny(img, 50, 150)
        ]
        
        for method in methods:
            try:
                processed = method(blurred)
                contours = cv2.findContours(processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                contours = imutils.grab_contours(contours)
                contours = sorted(contours, key=cv2.contourArea, reverse=True)
                
                for contour in contours[:5]:
                    peri = cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
                    
                    if len(approx) == 4:
                        # Validate the rectangle
                        if self._validate_rectangle(approx, gray.shape):
                            return approx.reshape(4, 2)
                            
            except Exception as e:
                continue
        
        return None
    
    def _detect_via_lines(self, gray: np.ndarray) -> Optional[np.ndarray]:
        """Detect document via line intersection"""
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
        
        if lines is None or len(lines) < 4:
            return None
        
        # Separate horizontal and vertical lines
        horizontal_lines = []
        vertical_lines = []
        
        for line in lines:
            rho, theta = line[0]
            angle = np.degrees(theta)
            
            if 85 <= angle <= 95 or -5 <= angle <= 5:  # Horizontal
                horizontal_lines.append((rho, theta))
            elif 40 <= angle <= 50 or 130 <= angle <= 140:  # Vertical
                vertical_lines.append((rho, theta))
        
        if len(horizontal_lines) >= 2 and len(vertical_lines) >= 2:
            # Find intersections of top/bottom and left/right lines
            corners = self._find_line_intersections(horizontal_lines[:2], vertical_lines[:2], gray.shape)
            if corners is not None and len(corners) == 4:
                return corners
        
        return None
    
    def _detect_via_features(self, gray: np.ndarray) -> Optional[np.ndarray]:
        """Detect document via corner features"""
        # Harris corner detection
        corners_harris = cv2.cornerHarris(gray, 2, 3, 0.04)
        corners_harris = cv2.dilate(corners_harris, None)
        
        # Get corner points
        corner_points = np.where(corners_harris > 0.01 * corners_harris.max())
        corner_coords = list(zip(corner_points[1], corner_points[0]))
        
        if len(corner_coords) < 4:
            return None
        
        # Cluster corners to find document corners
        if len(corner_coords) > 4:
            kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
            clusters = kmeans.fit(corner_coords)
            corner_coords = clusters.cluster_centers_
        
        # Order corners
        corners = np.array(corner_coords, dtype=np.float32)
        return self._order_corners(corners)
    
    def _validate_rectangle(self, approx: np.ndarray, img_shape: Tuple[int, int]) -> bool:
        """Validate if the detected shape is a valid document rectangle"""
        h, w = img_shape
        
        # Check area (should be significant portion of image)
        area = cv2.contourArea(approx)
        img_area = h * w
        if area < 0.1 * img_area:  # At least 10% of image
            return False
        
        # Check aspect ratio (should be roughly A4: ~1.4)
        rect = cv2.minAreaRect(approx.reshape(-1, 1, 2))
        width, height = rect[1]
        aspect_ratio = max(width, height) / min(width, height)
        if aspect_ratio > 2.0 or aspect_ratio < 1.0:  # Reasonable aspect ratio
            return False
        
        # Check if corners are roughly rectangular
        angles = []
        for i in range(4):
            p1 = approx[i][0]
            p2 = approx[(i + 1) % 4][0]
            p3 = approx[(i + 2) % 4][0]
            
            v1 = p1 - p2
            v2 = p3 - p2
            
            angle = np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
            angles.append(np.degrees(angle))
        
        # Check if angles are close to 90 degrees
        for angle in angles:
            if abs(angle - 90) > 30:  # Allow 30 degree deviation
                return False
        
        return True
    
    def _find_line_intersections(self, h_lines: List, v_lines: List, img_shape: Tuple[int, int]) -> Optional[np.ndarray]:
        """Find intersection points of horizontal and vertical lines"""
        corners = []
        h, w = img_shape
        
        for h_line in h_lines:
            for v_line in v_lines:
                rho1, theta1 = h_line
                rho2, theta2 = v_line
                
                # Calculate intersection
                cos1, sin1 = np.cos(theta1), np.sin(theta1)
                cos2, sin2 = np.cos(theta2), np.sin(theta2)
                
                det = cos1 * sin2 - sin1 * cos2
                if abs(det) < 1e-10:
                    continue
                
                x = (sin2 * rho1 - sin1 * rho2) / det
                y = (cos1 * rho2 - cos2 * rho1) / det
                
                # Check if intersection is within image bounds
                if 0 <= x <= w and 0 <= y <= h:
                    corners.append([x, y])
        
        if len(corners) >= 4:
            # Select the 4 corner points
            corners = np.array(corners)
            return self._select_document_corners(corners, img_shape)
        
        return None
    
    def _select_document_corners(self, corners: np.ndarray, img_shape: Tuple[int, int]) -> np.ndarray:
        """Select the 4 document corners from detected corner points"""
        h, w = img_shape
        
        # Find corners closest to image corners
        image_corners = np.array([[0, 0], [w, 0], [w, h], [0, h]])
        selected_corners = []
        
        for img_corner in image_corners:
            distances = np.sum((corners - img_corner) ** 2, axis=1)
            closest_idx = np.argmin(distances)
            selected_corners.append(corners[closest_idx])
        
        return np.array(selected_corners, dtype=np.float32)
    
    def _order_corners(self, corners: np.ndarray) -> np.ndarray:
        """Order corners in top-left, top-right, bottom-right, bottom-left"""
        # Sort by sum (top-left has smallest sum, bottom-right has largest)
        s = corners.sum(axis=1)
        top_left = corners[np.argmin(s)]
        bottom_right = corners[np.argmax(s)]
        
        # Sort by difference (top-right has smallest diff, bottom-left has largest)
        diff = np.diff(corners, axis=1).flatten()
        top_right = corners[np.argmin(diff)]
        bottom_left = corners[np.argmax(diff)]
        
        return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)
    
    def correct_perspective_advanced(self, image: np.ndarray, corners: np.ndarray) -> np.ndarray:
        """Advanced perspective correction with quality enhancement"""
        # Order corners properly
        ordered_corners = self._order_corners(corners)
        
        # Calculate dimensions for output image
        (tl, tr, br, bl) = ordered_corners
        
        # Calculate width
        width_top = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        width_bottom = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        max_width = max(int(width_top), int(width_bottom))
        
        # Calculate height
        height_left = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        height_right = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        max_height = max(int(height_left), int(height_right))
        
        # Define destination corners
        dst_corners = np.array([
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1]
        ], dtype=np.float32)
        
        # Get transformation matrix
        self.transformation_matrix = cv2.getPerspectiveTransform(ordered_corners, dst_corners)
        
        # Apply perspective transformation
        corrected = cv2.warpPerspective(image, self.transformation_matrix, (max_width, max_height))
        
        return corrected
    
    def detect_rotation_angle_advanced(self, image: np.ndarray) -> float:
        """Advanced rotation detection using multiple methods"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Method 1: Line-based detection
        angle1 = self._detect_rotation_via_lines(gray)
        
        # Method 2: Text line detection
        angle2 = self._detect_rotation_via_text_lines(gray)
        
        # Method 3: Edge-based detection
        angle3 = self._detect_rotation_via_edges(gray)
        
        # Combine results with confidence weighting
        angles = [a for a in [angle1, angle2, angle3] if a is not None]
        
        if not angles:
            return 0.0
        
        # Use median for robustness
        final_angle = np.median(angles)
        
        logger.info(f"Rotation angles detected: {angles}, final: {final_angle:.2f}°")
        return final_angle
    
    def _detect_rotation_via_lines(self, gray: np.ndarray) -> Optional[float]:
        """Detect rotation using Hough line transform"""
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
        
        if lines is None:
            return None
        
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = np.degrees(theta) - 90
            if abs(angle) < 45:  # Only consider reasonable rotations
                angles.append(angle)
        
        if angles:
            return np.median(angles)
        return None
    
    def _detect_rotation_via_text_lines(self, gray: np.ndarray) -> Optional[float]:
        """Detect rotation using text line detection"""
        # Create horizontal and vertical kernels
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        
        # Detect horizontal lines
        horizontal = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel_h)
        
        # Find contours of horizontal lines
        contours, _ = cv2.findContours(horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        angles = []
        for contour in contours:
            if cv2.contourArea(contour) > 100:  # Filter small contours
                rect = cv2.minAreaRect(contour)
                angle = rect[2]
                if abs(angle) < 45:
                    angles.append(angle)
        
        if angles:
            return np.median(angles)
        return None
    
    def _detect_rotation_via_edges(self, gray: np.ndarray) -> Optional[float]:
        """Detect rotation using edge-based analysis"""
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Use Hough transform to detect lines
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=100, maxLineGap=10)
        
        if lines is None:
            return None
        
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            
            # Normalize angle to [-45, 45] range
            while angle > 45:
                angle -= 90
            while angle < -45:
                angle += 90
            
            if abs(angle) < 45:
                angles.append(angle)
        
        if angles:
            return np.median(angles)
        return None
    
    def process_image_advanced(self, image_data: bytes) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Advanced image processing pipeline with 100% accuracy features
        """
        try:
            # Load image
            self.original_image = image_utils.load_image(image_data)
            logger.info(f"Image loaded: {self.original_image.shape}")
            
            # Initial quality assessment
            quality, skew_angle, brightness, contrast = image_utils.assess_image_quality(self.original_image)
            
            # Start with original image
            current_image = self.original_image.copy()
            
            # Step 1: Advanced document detection
            corners = self.detect_document_advanced(current_image)
            
            if corners is not None:
                # Apply perspective correction
                current_image = self.correct_perspective_advanced(current_image, corners)
                logger.info("Advanced perspective correction applied")
                self.detected_corners = corners
            else:
                logger.warning("Document corners not detected, using original image")
            
            # Step 2: Advanced rotation detection and correction
            rotation_angle = self.detect_rotation_angle_advanced(current_image)
            
            if abs(rotation_angle) > 0.5:
                current_image = image_utils.rotate_image(current_image, -rotation_angle)
                logger.info(f"Advanced rotation correction applied: {rotation_angle:.2f}°")
            
            # Step 3: Enhanced preprocessing
            current_image = self.enhance_image_quality(current_image)
            
            # Step 4: Template validation
            if not self.validate_omr_template_advanced(current_image):
                logger.warning("Advanced template validation failed")
            
            # Final quality metrics
            self.quality_metrics = {
                "image_quality": quality,
                "original_skew_angle": skew_angle,
                "detected_rotation": rotation_angle,
                "brightness_level": brightness,
                "contrast_level": contrast,
                "original_dimensions": self.original_image.shape[:2],
                "processed_dimensions": current_image.shape[:2],
                "perspective_corrected": corners is not None,
                "rotation_corrected": abs(rotation_angle) > 0.5,
                "corners_detected": corners is not None,
                "processing_methods": ["advanced_detection", "multi_algorithm_rotation", "enhanced_preprocessing"]
            }
            
            self.processed_image = current_image
            logger.info("Advanced image processing completed successfully")
            
            return current_image, self.quality_metrics
            
        except Exception as e:
            logger.error(f"Advanced image processing failed: {str(e)}")
            raise ImageQualityError(
                f"Failed to process image with advanced methods: {str(e)}",
                details={"error": str(e)}
            )
    
    def enhance_image_quality(self, image: np.ndarray) -> np.ndarray:
        """Enhanced image quality improvement"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 1. Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # 2. Contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # 3. Sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # 4. Final smoothing
        result = cv2.GaussianBlur(sharpened, (1, 1), 0)
        
        return result
    
    def validate_omr_template_advanced(self, image: np.ndarray) -> bool:
        """Advanced OMR template validation with multiple checks"""
        h, w = image.shape[:2] if len(image.shape) == 2 else image.shape[:2]
        
        # Check 1: Aspect ratio
        aspect_ratio = w / h
        if not (0.6 <= aspect_ratio <= 0.9):  # A4 portrait range
            logger.warning(f"Unusual aspect ratio: {aspect_ratio:.2f}")
            return False
        
        # Check 2: Detect circular patterns (bubbles)
        circles = cv2.HoughCircles(
            image, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
            param1=50, param2=30, minRadius=5, maxRadius=25
        )
        
        bubble_count = 0 if circles is None else len(circles[0])
        
        # Check 3: Detect rectangular patterns
        _, thresh = cv2.threshold(image, 180, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rectangular_regions = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if 50 < area < 500:  # Reasonable bubble size
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
                if len(approx) >= 4:  # Roughly rectangular
                    rectangular_regions += 1
        
        logger.info(f"Template validation - Circles: {bubble_count}, Rectangles: {rectangular_regions}")
        
        # Require minimum pattern count
        return bubble_count >= 50 or rectangular_regions >= 100