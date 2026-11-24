"""
Enhanced Vision Module for Tic-Tac-Toe Detection
Uses template matching for X and HoughCircles for O
Handles 90° CLOCKWISE rotation between camera view and physical board
"""

import cv2
import numpy as np
from config import CAMERA_INDEX

# ============================================================================
# CAMERA VIEW TRANSFORMATION - 90° CLOCKWISE ROTATION
# ============================================================================

def camera_to_physical(camera_index):
    """Convert camera-detected cell index to physical board index.
    
    Camera sees board rotated 90° CLOCKWISE from human's perspective:
    
    Human (Physical):      Camera View:
    0  1  2                6  3  0
    3  4  5        →       7  4  1
    6  7  8                8  5  2
    
    Formula: 90° clockwise rotation
    - camera_row = physical_col
    - camera_col = 2 - physical_row
    
    Inverse (camera to physical):
    - physical_row = 2 - camera_col
    - physical_col = camera_row
    
    Args:
        camera_index: Cell index as seen by camera (0-8)
    
    Returns:
        physical_index: Actual physical board position (0-8)
    """
    camera_row = camera_index // 3
    camera_col = camera_index % 3
    
    physical_row = 2 - camera_col
    physical_col = camera_row
    
    physical_index = physical_row * 3 + physical_col
    
    return physical_index

def physical_to_camera(physical_index):
    """Convert physical board index to camera view index.
    
    This is the forward transformation (inverse of camera_to_physical).
    """
    physical_row = physical_index // 3
    physical_col = physical_index % 3
    
    camera_row = physical_col
    camera_col = 2 - physical_row
    
    camera_index = camera_row * 3 + camera_col
    
    return camera_index

# ============================================================================
# Vision System Class
# ============================================================================

class VisionSystem:
    """Vision system with improved X/O detection and camera alignment."""
    
    def __init__(self):
        self.cap = None
        self.x_template = None
        self.grid_cells = []
        self.camera_aligned = False
        
        # Camera frame size (will be set during initialization)
        self.frame_width = 640
        self.frame_height = 480
        
        # Grid settings (will be dynamically adjusted to fit frame)
        self.grid_origin = [50, 50]  # Top-left corner [x, y]
        self.cell_size_px = 120  # Cell size in pixels
        self.margin = 10  # Margin inside each cell
        
    def initialize(self):
        """Initialize camera and create X template."""
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self.cap.isOpened():
            print("ERROR: Cannot open camera!")
            return False
        
        # Get actual camera frame size
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"✓ Camera initialized ({self.frame_width}x{self.frame_height})")
        
        # Calculate initial grid position to fit in frame
        self._calculate_initial_grid_position()
        
        # Create X template for matching
        self.x_template = self._create_x_template()
        
        print("✓ X template created")
        print("✓ Camera-to-physical transformation enabled (90° clockwise rotation)")
        return True
    
    def _calculate_initial_grid_position(self):
        """Calculate initial grid position to center it in the frame."""
        # Maximum cell size that fits in frame (with some margin)
        max_cell_size = min(
            (self.frame_width - 100) // 3,  # 3 cells wide + margin
            (self.frame_height - 100) // 3  # 3 cells tall + margin
        )
        
        # Use smaller cell size for safety
        self.cell_size_px = min(max_cell_size, 150)
        
        # Center the grid in the frame
        grid_width = 3 * self.cell_size_px
        grid_height = 3 * self.cell_size_px
        
        self.grid_origin[0] = (self.frame_width - grid_width) // 2
        self.grid_origin[1] = (self.frame_height - grid_height) // 2
        
        print(f"✓ Initial grid: origin ({self.grid_origin[0]}, {self.grid_origin[1]}), cell size {self.cell_size_px}px")
    
    def _create_x_template(self):
        """Create a simple X template for template matching."""
        template = np.zeros((50, 50), dtype=np.uint8)
        cv2.line(template, (10, 10), (40, 40), 255, 3)
        cv2.line(template, (40, 10), (10, 40), 255, 3)
        return template
    
    def _validate_grid_bounds(self, origin_x, origin_y, cell_size):
        """Ensure grid stays within camera frame bounds."""
        grid_width = 3 * cell_size
        grid_height = 3 * cell_size
        
        # Check if grid fits in frame
        if origin_x < 0:
            origin_x = 0
        if origin_y < 0:
            origin_y = 0
        if origin_x + grid_width > self.frame_width:
            origin_x = self.frame_width - grid_width
        if origin_y + grid_height > self.frame_height:
            origin_y = self.frame_height - grid_height
        
        # Minimum cell size
        if cell_size < 50:
            cell_size = 50
        
        # Maximum cell size (to fit in frame)
        max_size = min(
            (self.frame_width - origin_x) // 3,
            (self.frame_height - origin_y) // 3
        )
        if cell_size > max_size:
            cell_size = max_size
        
        return origin_x, origin_y, cell_size
    
    def align_camera(self):
        """Interactive camera alignment - saves grid position."""
        print("\n" + "="*70)
        print("CAMERA ALIGNMENT - Robot's View (90° Clockwise)")
        print("="*70)
        print("\n⚠️  IMPORTANT: Camera is from robot's perspective!")
        print("   Grid numbers shown are CAMERA VIEW (rotated 90° clockwise from human)")
        print("   Detection will automatically convert to physical coordinates")
        print("\nInstructions:")
        print("1. Position camera to see the grid (robot's opposite view)")
        print("2. Adjust the GREEN overlay to match your grid:")
        print("   - Arrow keys: Move grid (UP/DOWN/LEFT/RIGHT)")
        print("   - +/=: Make cells bigger")
        print("   - -/_: Make cells smaller")
        print("   - C: Center grid in frame")
        print("   - SPACE: Save and continue")
        print("   - Q: Skip alignment (use defaults)")
        print()
        
        grid_x, grid_y = self.grid_origin
        cell_size = self.cell_size_px
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            display = frame.copy()
            
            # Draw frame boundary
            cv2.rectangle(display, (5, 5), (self.frame_width - 5, self.frame_height - 5),
                         (255, 255, 0), 2)  # Yellow border
            
            # Validate and constrain grid
            grid_x, grid_y, cell_size = self._validate_grid_bounds(grid_x, grid_y, cell_size)
            
            # Draw 3x3 grid overlay (CAMERA VIEW - will be transformed)
            for row in range(3):
                for col in range(3):
                    x = grid_x + col * cell_size
                    y = grid_y + row * cell_size
                    
                    # Cell rectangle
                    cv2.rectangle(display, (x, y), 
                                (x + cell_size, y + cell_size),
                                (0, 255, 0), 2)
                    
                    # Camera cell number (will be converted to physical)
                    camera_num = row * 3 + col + 1
                    physical_num = camera_to_physical(camera_num - 1) + 1
                    
                    # Show both camera and physical numbers
                    text = f"C{camera_num}"
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    text_x = x + (cell_size - text_size[0]) // 2
                    text_y = y + (cell_size + text_size[1]) // 2 - 10
                    cv2.putText(display, text, (text_x, text_y),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # Physical number (smaller, below)
                    text2 = f"(P{physical_num})"
                    text_size2 = cv2.getTextSize(text2, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
                    text_x2 = x + (cell_size - text_size2[0]) // 2
                    text_y2 = y + (cell_size + text_size2[1]) // 2 + 15
                    cv2.putText(display, text2, (text_x2, text_y2),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
            
            # Instructions overlay
            cv2.rectangle(display, (0, 0), (self.frame_width, 90), (0, 0, 0), -1)
            cv2.rectangle(display, (0, 0), (self.frame_width, 90), (255, 255, 255), 2)
            
            cv2.putText(display, "C=Camera View  P=Physical Board  (Auto-converted)",
                       (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(display, "Arrows=Move  +/-=Size  C=Center  SPACE=Save  Q=Skip",
                       (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(display, f"Origin: ({grid_x:3d}, {grid_y:3d})  Cell: {cell_size:3d}px",
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            cv2.imshow("Camera Alignment - Robot View", display)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\n⚠️  Skipped alignment, using centered defaults")
                break
            elif key == ord(' '):
                self.grid_origin = [grid_x, grid_y]
                self.cell_size_px = cell_size
                self.camera_aligned = True
                print(f"\n✓ Camera aligned! Grid at ({grid_x}, {grid_y}), cell size {cell_size}px")
                break
            elif key == ord('c'):
                # Center the grid
                grid_width = 3 * cell_size
                grid_height = 3 * cell_size
                grid_x = (self.frame_width - grid_width) // 2
                grid_y = (self.frame_height - grid_height) // 2
                print(f"  Centered: ({grid_x}, {grid_y})")
            elif key == 82 or key == ord('w'):  # Up arrow or W
                grid_y = max(0, grid_y - 10)
            elif key == 84 or key == ord('s'):  # Down arrow or S
                grid_y += 10
            elif key == 81 or key == ord('a'):  # Left arrow or A
                grid_x = max(0, grid_x - 10)
            elif key == 83 or key == ord('d'):  # Right arrow or D
                grid_x += 10
            elif key == ord('+') or key == ord('='):
                cell_size += 10
            elif key == ord('-') or key == ord('_'):
                cell_size = max(30, cell_size - 10)
        
        cv2.destroyAllWindows()
        
        # Calculate grid cells
        self._update_grid_cells()
        return True
    
    def _update_grid_cells(self):
        """Update grid cell coordinates based on current settings."""
        self.grid_cells = []
        for row in range(3):
            for col in range(3):
                x = self.grid_origin[0] + col * self.cell_size_px
                y = self.grid_origin[1] + row * self.cell_size_px
                self.grid_cells.append((x, y, self.cell_size_px, self.cell_size_px))
    
    def capture_and_detect(self, expected_board=None):
        """Capture current frame and detect X/O symbols."""
        print("\n[CAMERA] Press SPACE to capture board state...")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            display = frame.copy()
            
            # Draw grid overlay with camera/physical numbers
            for i, (x, y, w, h) in enumerate(self.grid_cells):
                cv2.rectangle(display, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                physical_num = camera_to_physical(i) + 1
                text = f"C{i+1}(P{physical_num})"
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                text_x = x + (w - text_size[0]) // 2
                text_y = y + (h + text_size[1]) // 2
                cv2.putText(display, text, (text_x, text_y),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Instructions
            cv2.rectangle(display, (0, 0), (self.frame_width, 60), (0, 0, 0), -1)
            cv2.putText(display, "Press SPACE to detect, Q to skip",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            cv2.imshow("Capture Board State", display)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                cv2.destroyAllWindows()
                return None
            elif key == ord(' '):
                board = self._detect_board_state(frame)
                cv2.destroyAllWindows()
                self._show_detection_result(frame, board)
                return board
    
    def _detect_board_state(self, frame):
        """Detect X and O symbols and convert to physical coordinates."""
        camera_board = []
        
        print("\nDetecting symbols (camera view)...")
        for i, (x, y, w, h) in enumerate(self.grid_cells):
            pad = self.margin
            y1 = max(0, y + pad)
            y2 = min(frame.shape[0], y + h - pad)
            x1 = max(0, x + pad)
            x2 = min(frame.shape[1], x + w - pad)
            
            if y2 <= y1 or x2 <= x1:
                camera_board.append(' ')
                continue
            
            cell_img = frame[y1:y2, x1:x2]
            symbol = self._detect_symbol(cell_img)
            camera_board.append(symbol)
            
            status = symbol if symbol else 'empty'
            print(f"  Camera cell {i+1}: {status}")
        
        # Convert from camera view to physical board
        print("\n🔄 Converting camera view → physical board...")
        physical_board = [' '] * 9
        for camera_idx in range(9):
            physical_idx = camera_to_physical(camera_idx)
            physical_board[physical_idx] = camera_board[camera_idx]
            
            if camera_board[camera_idx] != ' ':
                print(f"   Camera C{camera_idx+1} → Physical P{physical_idx+1}: {camera_board[camera_idx]}")
        
        return physical_board
    
    def _detect_symbol(self, cell):
        """Detect X or O in a cell image."""
        if cell.size == 0 or cell.shape[0] < 30 or cell.shape[1] < 30:
            return ' '
        
        is_o, o_conf = self._detect_o_hough(cell)
        is_x, x_conf = self._detect_x_template(cell)
        
        if is_o and is_x:
            return 'O' if o_conf > x_conf else 'X'
        elif is_o:
            return 'O'
        elif is_x:
            return 'X'
        else:
            return ' '
    
    def _detect_o_hough(self, cell):
        """Detect O using HoughCircles."""
        if cell.size == 0 or cell.shape[0] < 30 or cell.shape[1] < 30:
            return False, 0
        
        gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY) if len(cell.shape) == 3 else cell
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        
        h, w = gray.shape
        min_r = int(0.15 * min(h, w))
        max_r = int(0.45 * min(h, w))
        
        try:
            circles = cv2.HoughCircles(
                gray, cv2.HOUGH_GRADIENT, dp=1.2,
                minDist=min(h, w) // 2, param1=50, param2=30,
                minRadius=min_r, maxRadius=max_r
            )
            
            if circles is not None and len(circles[0]) > 0:
                return True, 0.8
        except:
            pass
        
        return False, 0
    
    def _detect_x_template(self, cell):
        """Detect X using template matching."""
        if cell.size == 0 or cell.shape[0] < 30 or cell.shape[1] < 30:
            return False, 0
        
        gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY) if len(cell.shape) == 3 else cell
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        filled = np.count_nonzero(binary) / binary.size
        if filled < 0.05:
            return False, 0
        
        h, w = gray.shape
        template_size = min(h, w) // 2
        x_temp = cv2.resize(self.x_template, (template_size, template_size))
        
        try:
            x_match = cv2.matchTemplate(binary, x_temp, cv2.TM_CCOEFF_NORMED)
            x_score = np.max(x_match)
            
            if x_score > 0.3:
                return True, x_score
        except:
            pass
        
        return False, 0
    
    def _show_detection_result(self, frame, board):
        """Show detection result in PHYSICAL coordinates."""
        result = frame.copy()
        for camera_idx, (x, y, w, h) in enumerate(self.grid_cells):
            physical_idx = camera_to_physical(camera_idx)
            symbol = board[physical_idx]
            
            if symbol == 'X':
                color = (0, 0, 255)
            elif symbol == 'O':
                color = (255, 0, 0)
            else:
                color = (0, 255, 0)
            
            cv2.rectangle(result, (x, y), (x+w, y+h), color, 4)
            text = symbol if symbol != ' ' else '.'
            textsize = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 2.0, 4)[0]
            textx = x + (w - textsize[0]) // 2
            texty = y + (h + textsize[1]) // 2
            cv2.putText(result, text, (textx, texty), cv2.FONT_HERSHEY_SIMPLEX, 2.0, color, 4)
        
        cv2.imshow("Detection Result (Physical Coordinates)", result)
        print("Detection complete! Press any key")
        cv2.waitKey(0)
        cv2.destroyWindow("Detection Result (Physical Coordinates)")
    
    def detect_board_silent(self, expected_board=None):
        """
        Silent detection without displaying window (for continuous monitoring).
        Returns detected board state in PHYSICAL coordinates or None.
        """
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # Camera board (as seen by camera)
        camera_board = [' '] * 9
        
        # Extract and detect each cell
        for i, (x, y, w, h) in enumerate(self.grid_cells):
            pad = self.margin
            y1 = max(0, y + pad)
            y2 = min(frame.shape[0], y + h - pad)
            x1 = max(0, x + pad)
            x2 = min(frame.shape[1], x + w - pad)
            
            if y2 <= y1 or x2 <= x1:
                camera_board[i] = ' '
                continue
            
            cell_img = frame[y1:y2, x1:x2]
            symbol = self._detect_symbol(cell_img)  # ← UNDERSCORE!
            camera_board[i] = symbol
        
        # Convert camera view to physical coordinates
        physical_board = [' '] * 9
        for camera_idx in range(9):
            physical_idx = camera_to_physical(camera_idx)
            physical_board[physical_idx] = camera_board[camera_idx]
        
        return physical_board
    
    def close(self):
        """Release camera and close windows."""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

    def detect_board_from_frame(self, frame):
        """
        Detect board state from a given frame (for live feed processing).
        Returns detected board state in PHYSICAL coordinates or None.
        """
        # Camera board (as seen by camera)
        camera_board = [' '] * 9
        
        # Extract and detect each cell
        for i, (x, y, w, h) in enumerate(self.grid_cells):
            pad = self.margin
            y1 = max(0, y + pad)
            y2 = min(frame.shape[0], y + h - pad)
            x1 = max(0, x + pad)
            x2 = min(frame.shape[1], x + w - pad)
            
            if y2 <= y1 or x2 <= x1:
                camera_board[i] = ' '
                continue
            
            cell_img = frame[y1:y2, x1:x2]
            symbol = self._detect_symbol(cell_img)
            camera_board[i] = symbol
        
        # Convert camera view to physical coordinates
        physical_board = [' '] * 9
        for camera_idx in range(9):
            physical_idx = camera_to_physical(camera_idx)
            physical_board[physical_idx] = camera_board[camera_idx]
        
        return physical_board
