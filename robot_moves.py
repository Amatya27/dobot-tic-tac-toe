from serial.tools import list_ports
import pydobot
import math

# Import ALL configuration values
from config import DRAW_Z, DRAW_TRAVEL_Z, USE_ROBOT
from config import ORIGIN_X, ORIGIN_Y, CELL_SIZE
from config import CAMERA_X, CAMERA_Y, CAMERA_Z, CAMERA_R
from config import DRAW_SPEED, TRAVEL_SPEED


class DobotSimulator:
    """Simulator for testing without robot."""
    
    def __init__(self):
        print("[SIMULATOR] Dobot simulator initialized")
    
    def move_to(self, x, y, z, r=0):
        """Simulate movement - must match real Dobot signature."""
        if z >= 0:
            print(f"[SIM] move_to({x:.1f}, {y:.1f}, Z={z:.1f}, R={r:.1f}) | PEN UP")
        else:
            print(f"[SIM] move_to({x:.1f}, {y:.1f}, Z={z:.1f}, R={r:.1f}) | PEN DOWN")
    
    def speed(self, velocity, acceleration=100):
        """Simulate speed setting."""
        print(f"[SIM] speed set to {velocity} mm/s")
    
    def close(self):
        print("[SIMULATOR] Device closed")


def get_device():
    """Get Dobot device or simulator."""
    ports = list_ports.comports()
    if not ports:
        print("SIMULATION: No Dobot found, using simulator")
        return DobotSimulator()
    
    port = ports[0].device
    device = pydobot.Dobot(port=port)
    
    # Set default speeds
    device.speed(TRAVEL_SPEED, 100)
    print(f"✓ Dobot connected, speed set to {TRAVEL_SPEED} mm/s")
    
    return device


def line(device, start, end, draw_z=DRAW_Z, travel_z=DRAW_TRAVEL_Z):
    """
    Draw a line with proper pen lifting.
    
    Sequence:
    1. Lift to safe height ABOVE target
    2. Move to start horizontally
    3. Lower to drawing height
    4. Draw line
    5. Lift back up
    """
    x1, y1 = start
    x2, y2 = end
    
    # Use EXTRA high travel height for safety
    SAFE_Z = max(travel_z, 30)  # At least 30mm above paper
    
    # Set travel speed
    device.speed(TRAVEL_SPEED, 100)
    
    # Move to start position with pen VERY high
    device.move_to(x1, y1, SAFE_Z, 0)
    
    # Set drawing speed
    device.speed(DRAW_SPEED, 100)
    
    # Lower pen to drawing height
    device.move_to(x1, y1, draw_z, 0)
    
    # Draw the line
    device.move_to(x2, y2, draw_z, 0)
    
    # Lift pen back to safe height
    device.move_to(x2, y2, SAFE_Z, 0)
    
    # Reset to travel speed
    device.speed(TRAVEL_SPEED, 100)



def move_to_camera_position(device, x=CAMERA_X, y=CAMERA_Y, z=CAMERA_Z, r=CAMERA_R):
    """Move robot to camera observation position with rotation."""
    device.speed(TRAVEL_SPEED, 100)
    device.move_to(x, y, z, r)
    print(f"✓ Robot moved to camera position ({x}, {y}, {z}, R={r})")


def drawX(device, cx, cy, size):
    """Draw X symbol centered at (cx, cy) with given size."""
    device.speed(DRAW_SPEED, 100)
    line(device, (cx - size, cy - size), (cx + size, cy + size))
    line(device, (cx - size, cy + size), (cx + size, cy - size))
    device.speed(TRAVEL_SPEED, 100)


def drawO(device, cx, cy, radius=20):
    """Draw O symbol (circle approximation with 12 segments)."""
    device.speed(DRAW_SPEED, 100)
    
    for i in range(12):
        angle1 = 2 * math.pi * i / 12
        angle2 = 2 * math.pi * (i + 1) / 12
        
        x1 = cx + radius * math.cos(angle1)
        y1 = cy + radius * math.sin(angle1)
        x2 = cx + radius * math.cos(angle2)
        y2 = cy + radius * math.sin(angle2)
        
        line(device, (x1, y1), (x2, y2))
    
    device.speed(TRAVEL_SPEED, 100)


def drawD(device, cx, cy):
    """Draw 'D' for Draw outside grid."""
    device.speed(DRAW_SPEED, 100)
    line(device, (cx, cy), (cx, cy + 40))
    line(device, (cx, cy), (cx + 15, cy))
    line(device, (cx + 15, cy), (cx + 20, cy + 10))
    line(device, (cx + 20, cy + 10), (cx + 20, cy + 30))
    line(device, (cx + 20, cy + 30), (cx + 15, cy + 40))
    line(device, (cx + 15, cy + 40), (cx, cy + 40))
    device.speed(TRAVEL_SPEED, 100)


def drawE(device, cx, cy):
    """Draw error symbol E outside grid."""
    device.speed(DRAW_SPEED, 100)
    line(device, (cx, cy), (cx + 20, cy))
    line(device, (cx, cy), (cx, cy + 40))
    line(device, (cx, cy + 20), (cx + 15, cy + 20))
    line(device, (cx, cy + 40), (cx + 20, cy + 40))
    device.speed(TRAVEL_SPEED, 100)


def strike_line(device, origin_x, origin_y, cell_size, winning_line):
    """Strike through winning line (row, col, or diagonal)."""
    def get_row_col(idx):
        return idx // 3, idx % 3
    
    a, b, c = winning_line
    r1, c1 = get_row_col(a)
    r3, c3 = get_row_col(c)
    
    x1 = origin_x + (c1 + 0.5) * cell_size
    y1 = origin_y + (r1 + 0.5) * cell_size
    x2 = origin_x + (c3 + 0.5) * cell_size
    y2 = origin_y + (r3 + 0.5) * cell_size
    
    device.speed(DRAW_SPEED, 100)
    line(device, (x1, y1), (x2, y2))
    device.speed(TRAVEL_SPEED, 100)


def draw_grid_on_device(device, origin_x, origin_y, cell_size):
    """Draw a 3x3 tic-tac-toe grid."""
    device.speed(DRAW_SPEED, 100)
    
    # Vertical lines
    for i in range(1, 3):
        x = origin_x + i * cell_size
        line(device, (x, origin_y), (x, origin_y + 3 * cell_size))
    
    # Horizontal lines
    for i in range(1, 3):
        y = origin_y + i * cell_size
        line(device, (origin_x, y), (origin_x + 3 * cell_size, y))
    
    device.speed(TRAVEL_SPEED, 100)
