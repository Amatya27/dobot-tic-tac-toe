# Configuration settings
USE_ROBOT = False  # Set to False for testing at home without Dobot
CAMERA_INDEX = 0

# ============================================================================
# GRID DRAWING POSITION
# ============================================================================
ORIGIN_X = 234.2  # X coordinate of top-left corner (mm from robot base)
ORIGIN_Y = -63.4   # Y coordinate of top-left corner
CELL_SIZE = 35  # Size of each cell in mm
                # Larger cells = easier to draw and detect symbols
                # With 35mm: X will be 17.5mm, O diameter will be 23mm

# ============================================================================
# Z-AXIS HEIGHTS (CRITICAL FOR PEN LIFTING)
# ============================================================================
DRAW_Z = 4.4      # Z height when pen touches paper (NEGATIVE = down) -37.3
DRAW_TRAVEL_Z = 15     # Z height when pen is lifted (POSITIVE = up in air)
                       # 
                       # Adjust in lab if needed:
                       # - Pen drags? Increase DRAW_TRAVEL_Z (try 30, 40, 50)
                       # - Pen doesn't touch? Decrease DRAW_Z (try -40, -42)

# ============================================================================
# CAMERA OBSERVATION POSITION
# ============================================================================
CAMERA_X = 229.8   # Camera X position (best view) - UPDATED
CAMERA_Y = -15.2   # Camera Y position - UPDATED
CAMERA_Z = 38.3    # Camera Z height above paper - UPDATED
CAMERA_R = -1.4    # Camera rotation angle - UPDATED

# ============================================================================
# ROBOT SPEED SETTINGS
# ============================================================================
DRAW_SPEED = 250      # Speed for drawing (mm/s) - FASTER!
TRAVEL_SPEED = 300    # Speed for moving without drawing (mm/s)
