"""
Draw Grid Script - Tests grid drawing with real Dobot or simulator
"""

from config import USE_ROBOT, ORIGIN_X, ORIGIN_Y, CELL_SIZE
from robot_moves import get_device, draw_grid_on_device


def draw_grid_entry():
    """Draw tic-tac-toe grid on paper."""
    print("\n" + "="*60)
    print("GRID DRAWING TEST")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  USE_ROBOT: {USE_ROBOT}")
    print(f"  Grid Origin: ({ORIGIN_X}, {ORIGIN_Y})")
    print(f"  Cell Size: {CELL_SIZE}mm")
    print(f"  Grid Span: {CELL_SIZE * 3}mm × {CELL_SIZE * 3}mm")
    print()
    
    # Get device (real Dobot or simulator)
    print("Initializing device...")
    device = get_device()
    
    if device is None:
        print("❌ Failed to initialize device!")
        return
    
    print("✓ Device ready")
    print("\nDrawing grid...")
    print("  - 2 vertical lines")
    print("  - 2 horizontal lines")
    print("  - Pen will lift between lines")
    print()
    
    # Draw the grid
    draw_grid_on_device(device, ORIGIN_X, ORIGIN_Y, CELL_SIZE)
    
    print("\n✓ Grid drawing complete!")
    print("="*60)
    
    # Close device
    if hasattr(device, 'close'):
        device.close()
        print("✓ Device closed")


if __name__ == "__main__":
    try:
        draw_grid_entry()
    except KeyboardInterrupt:
        print("\n\n⚠️  Drawing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
