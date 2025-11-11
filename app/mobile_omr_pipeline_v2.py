"""
Mobile OMR Pipeline V2 - Resolution-Adaptive Corner Detection

Improvements:
- Handles different image resolutions (mobile photos vs scanned images)
- Adaptive area thresholds based on image size
- Better corner mark detection for real-world conditions
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# Fix for DFLoss missing in newer ultralytics versions
# Create a dummy DFLoss class to allow loading older trained models
try:
    from ultralytics.utils import loss
    if not hasattr(loss, 'DFLoss'):
        # Create dummy DFLoss class for backward compatibility
        class DFLoss:
            def __init__(self, *args, **kwargs):
                pass
        # Register it in the loss module
        loss.DFLoss = DFLoss
except Exception as e:
    print(f"Warning: Could not patch DFLoss: {e}")

from ultralytics import YOLO


class MobileOMRPipelineV2:
    """Complete OMR processing pipeline with adaptive corner detection"""

    def __init__(self, model_path):
        """Initialize pipeline"""
        print("="*70)
        print("MOBILE OMR DETECTION PIPELINE V2")
        print("="*70)
        print(f"Loading model: {model_path}")

        self.model = YOLO(model_path)
        print("Model loaded successfully!")
        print()

        # Template specifications
        self.target_width = 2480
        self.target_height = 3508

        # Grid layout
        self.num_questions = 100
        self.num_columns = 4
        self.questions_per_column = 25
        self.questions_start_y = 726  # Actual measured from aligned images
        self.question_spacing_y = 103  # Actual measured spacing
        self.column_width = 585  # Actual measured column width
        self.first_column_x = 49  # Actual measured first column position

        # YOLO classes
        self.filled_classes = [1, 3, 5, 7]

    def detect_corner_marks(self, image):
        """Adaptive corner detection for different resolutions"""
        print("STEP 1: DETECTING CORNER MARKS (ADAPTIVE)")
        print("-"*70)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        print(f"Image size: {w}x{h}")

        # Calculate expected corner mark size based on image resolution
        # Full resolution (2480x3508): corner marks are 100x100 = 10,000 px
        # Scale factor relative to full resolution
        scale_x = w / self.target_width
        scale_y = h / self.target_height
        scale = (scale_x + scale_y) / 2

        print(f"Scale factor: {scale:.2f}x")

        # Expected corner mark size
        expected_size = 100 * scale  # In pixels
        expected_area = expected_size ** 2

        # Adaptive area thresholds (allow 30% - 300% of expected)
        min_area = expected_area * 0.3
        max_area = expected_area * 3.0

        print(f"Expected corner size: {expected_size:.1f}x{expected_size:.1f} px")
        print(f"Search area range: {min_area:.0f} - {max_area:.0f} px")

        # Try multiple threshold methods
        methods = [
            ('adaptive', lambda g: cv2.adaptiveThreshold(
                g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 21, 10
            )),
            ('otsu', lambda g: cv2.threshold(
                g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )[1]),
            ('simple_100', lambda g: cv2.threshold(
                g, 100, 255, cv2.THRESH_BINARY_INV
            )[1])
        ]

        all_candidates = []

        for method_name, threshold_func in methods:
            binary = threshold_func(gray)
            contours, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            for contour in contours:
                area = cv2.contourArea(contour)

                if min_area < area < max_area:
                    x, y, bw, bh = cv2.boundingRect(contour)
                    aspect_ratio = float(bw) / bh if bh > 0 else 0

                    # Should be square-ish
                    if 0.5 < aspect_ratio < 2.0:
                        M = cv2.moments(contour)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])

                            # Distance from center (corners are far from center)
                            center_x, center_y = w // 2, h // 2
                            dist_from_center = np.sqrt(
                                (cx - center_x)**2 + (cy - center_y)**2
                            )

                            # Must be in outer regions (not center)
                            if dist_from_center > min(w, h) * 0.2:
                                all_candidates.append({
                                    'center': (cx, cy),
                                    'area': area,
                                    'dist_from_center': dist_from_center,
                                    'method': method_name
                                })

        print(f"Found {len(all_candidates)} corner candidates (before deduplication)")

        # Deduplicate nearby candidates (same corner detected by multiple methods)
        unique_candidates = []
        merge_threshold = expected_size  # Candidates within this distance are same corner

        for candidate in all_candidates:
            cx, cy = candidate['center']

            # Check if this is a duplicate of an existing unique candidate
            is_duplicate = False
            for unique in unique_candidates:
                ux, uy = unique['center']
                distance = np.sqrt((cx - ux)**2 + (cy - uy)**2)

                if distance < merge_threshold:
                    # Duplicate - keep the one with larger area
                    if candidate['area'] > unique['area']:
                        unique_candidates.remove(unique)
                        unique_candidates.append(candidate)
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_candidates.append(candidate)

        print(f"After deduplication: {len(unique_candidates)} unique corners")

        if len(unique_candidates) < 4:
            print(f"ERROR: Only found {len(unique_candidates)} unique corner marks (need 4)")
            return None

        # Sort by distance from center, take top 4
        unique_candidates.sort(key=lambda c: c['dist_from_center'], reverse=True)
        top_4 = unique_candidates[:4]

        print(f"Selected top 4 candidates:")
        for c in top_4:
            print(f"  Center: {c['center']}, Area: {c['area']:.0f} px, Method: {c['method']}")

        # Extract corner positions
        corners_list = [c['center'] for c in top_4]

        # Sort corners: top-left, top-right, bottom-left, bottom-right
        corners_list = sorted(corners_list, key=lambda p: p[1])  # Sort by y
        top_corners = sorted(corners_list[:2], key=lambda p: p[0])  # Top 2, sort by x
        bottom_corners = sorted(corners_list[2:], key=lambda p: p[0])  # Bottom 2, sort by x

        corners = {
            'top_left': top_corners[0],
            'top_right': top_corners[1],
            'bottom_left': bottom_corners[0],
            'bottom_right': bottom_corners[1]
        }

        print()
        print("Corner marks identified:")
        print(f"  Top-left:     {corners['top_left']}")
        print(f"  Top-right:    {corners['top_right']}")
        print(f"  Bottom-left:  {corners['bottom_left']}")
        print(f"  Bottom-right: {corners['bottom_right']}")
        print()

        return corners

    def align_image(self, image, corners):
        """Apply perspective transform to straighten image"""
        print("STEP 2: ALIGNING IMAGE")
        print("-"*70)

        # Source points (detected corners)
        src_points = np.float32([
            corners['top_left'],
            corners['top_right'],
            corners['bottom_left'],
            corners['bottom_right']
        ])

        # Destination points (perfect rectangle)
        dst_points = np.float32([
            [0, 0],
            [self.target_width, 0],
            [0, self.target_height],
            [self.target_width, self.target_height]
        ])

        # Calculate and apply perspective transform
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        aligned = cv2.warpPerspective(
            image, matrix, (self.target_width, self.target_height)
        )

        print(f"Image aligned to {self.target_width}x{self.target_height}")
        print()

        return aligned

    def detect_bubbles(self, image):
        """Run YOLO detection"""
        print("STEP 3: DETECTING BUBBLES")
        print("-"*70)

        results = self.model.predict(
            image,
            conf=0.25,
            iou=0.45,
            imgsz=1280,
            max_det=500,
            device='cuda' if self.model.device.type == 'cuda' else 'cpu',
            verbose=False
        )

        num_detections = len(results[0].boxes)
        print(f"Detected {num_detections} bubbles")
        print(f"Detection rate: {(num_detections/400)*100:.1f}%")
        print()

        return results[0]

    def map_bubble_to_question(self, center_x, center_y):
        """Map bubble position to question number"""
        col = int((center_x - self.first_column_x) / self.column_width)
        col = max(0, min(3, col))

        row = int((center_y - self.questions_start_y) / self.question_spacing_y)
        row = max(0, min(24, row))

        question_num = col * self.questions_per_column + row + 1

        return question_num if 1 <= question_num <= 100 else None

    def extract_answers(self, yolo_results):
        """Extract answers from YOLO detections"""
        print("STEP 4: EXTRACTING ANSWERS")
        print("-"*70)

        boxes = yolo_results.boxes

        # Filter filled bubbles
        filled_bubbles = []

        for box in boxes:
            cls_id = int(box.cls[0])

            if cls_id in self.filled_classes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                conf = float(box.conf[0])

                option = ['A', 'B', 'C', 'D'][cls_id // 2]

                filled_bubbles.append({
                    'center': (cx, cy),
                    'option': option,
                    'confidence': conf,
                    'class_id': cls_id
                })

        print(f"Filled bubbles: {len(filled_bubbles)}")

        # Map to questions
        question_bubbles = {}

        for bubble in filled_bubbles:
            cx, cy = bubble['center']
            question_num = self.map_bubble_to_question(cx, cy)

            if question_num:
                if question_num not in question_bubbles:
                    question_bubbles[question_num] = []
                question_bubbles[question_num].append(bubble)

        # Extract final answers
        answers = {}
        multiple_fills = []

        for q_num, bubbles in question_bubbles.items():
            if len(bubbles) == 1:
                answers[q_num] = bubbles[0]['option']
            else:
                best = max(bubbles, key=lambda b: b['confidence'])
                answers[q_num] = best['option']
                multiple_fills.append({
                    'question': q_num,
                    'options': [b['option'] for b in bubbles]
                })

        print(f"Answered: {len(answers)}/{self.num_questions}")
        print(f"Multiple fills: {len(multiple_fills)}")
        print()

        return {
            'answers': answers,
            'answered': len(answers),
            'unanswered': self.num_questions - len(answers),
            'multiple_fills': multiple_fills
        }

    def process(self, image_path, save_debug=True):
        """Complete processing pipeline"""
        print("="*70)
        print(f"PROCESSING: {image_path}")
        print("="*70)
        print()

        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            return {'error': 'Could not load image'}

        h, w = image.shape[:2]
        print(f"Image loaded: {w}x{h}")
        print()

        # Create output directory
        output_dir = Path('mobile_omr_results')
        output_dir.mkdir(exist_ok=True)

        base_name = Path(image_path).stem

        # Step 1: Detect corners
        corners = self.detect_corner_marks(image)
        if corners is None:
            return {'error': 'Corner detection failed'}

        if save_debug:
            corner_viz = image.copy()
            for name, (x, y) in corners.items():
                cv2.circle(corner_viz, (x, y), 10, (0, 255, 0), -1)
            cv2.imwrite(str(output_dir / f"{base_name}_1_corners.jpg"), corner_viz)

        # Step 2: Align
        aligned = self.align_image(image, corners)

        if save_debug:
            cv2.imwrite(str(output_dir / f"{base_name}_2_aligned.jpg"), aligned)

        # Step 3: Detect bubbles
        yolo_results = self.detect_bubbles(aligned)

        if save_debug:
            detection_viz = aligned.copy()
            for box in yolo_results.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cls_id = int(box.cls[0])
                color = (0, 255, 0) if cls_id in self.filled_classes else (0, 0, 255)
                cv2.rectangle(detection_viz, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            cv2.imwrite(str(output_dir / f"{base_name}_3_detections.jpg"), detection_viz)

        # Step 4: Extract answers
        extraction_result = self.extract_answers(yolo_results)

        results = {
            'image_path': str(image_path),
            'detection_count': len(yolo_results.boxes),
            'extraction': extraction_result,
            'output_dir': str(output_dir)
        }

        return results

    def print_results(self, results):
        """Print formatted results"""
        print()
        print("="*70)
        print("FINAL RESULTS")
        print("="*70)
        print()

        if 'error' in results:
            print(f"ERROR: {results['error']}")
            return

        extraction = results['extraction']
        answers = extraction['answers']

        # Print answers
        for col in range(4):
            q_start = col * 25 + 1
            q_end = q_start + 25

            print(f"Column {col + 1} (Q{q_start}-Q{q_end-1}):")
            for q in range(q_start, q_end):
                if q in answers:
                    print(f"  Q{q:3d}: {answers[q]}")
                else:
                    print(f"  Q{q:3d}: [NOT FILLED]")
            print()

        print("="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Detection: {results['detection_count']}/400 bubbles")
        print(f"Answered: {extraction['answered']}/{self.num_questions} questions")

        if extraction['multiple_fills']:
            print(f"Multiple fills: {len(extraction['multiple_fills'])}")

        print()
        print(f"Debug images saved to: {results['output_dir']}")


def main():
    """Command-line interface"""
    if len(sys.argv) < 3:
        print("Usage: python mobile_omr_pipeline_v2.py <model_path> <image_path>")
        return

    model_path = sys.argv[1]
    image_path = sys.argv[2]

    # Initialize pipeline
    pipeline = MobileOMRPipelineV2(model_path)

    # Process image
    results = pipeline.process(image_path, save_debug=True)

    # Print results
    pipeline.print_results(results)


if __name__ == "__main__":
    main()
