from vision_module import VisionSystem
import robot_moves
import game_logic
from config import USE_ROBOT, ORIGIN_X, ORIGIN_Y, CELL_SIZE, CAMERA_X, CAMERA_Y, CAMERA_Z, CAMERA_R


# ============================================================================
# COORDINATE TRANSFORMATION - User View to Robot Physical Drawing
# ============================================================================

def user_to_robot_physical(user_index):
    """Convert user cell (terminal 1-9) to physical robot drawing position.
    
    User sees:        Robot draws at:
    0  1  2           0  3  6
    3  4  5    →      1  4  7
    6  7  8           2  5  8
    
    This is transpose: swap row and column.
    """
    row = user_index // 3
    col = user_index % 3
    physical = row + col * 3
    return physical


def get_cell_center(user_index):
    """Get center coordinates for drawing, given user cell index."""
    robot_phys = user_to_robot_physical(user_index)
    row = robot_phys % 3
    col = robot_phys // 3
    cx = ORIGIN_X + col * CELL_SIZE + CELL_SIZE // 2
    cy = ORIGIN_Y + row * CELL_SIZE + CELL_SIZE // 2
    return cx, cy


# ============================================================================
# Display Function
# ============================================================================

def print_board(board, human_symbol, ai_symbol):
    """Print board in HUMAN'S VIEWING PERSPECTIVE (simple 1-9 layout).
    
    Board is stored in user view (0-8), display as:
    1 | 2 | 3
    ---------
    4 | 5 | 6
    ---------
    7 | 8 | 9
    """
    print("\n" + "="*35)
    print("  BOARD (Your View)")
    print("  You: {}, Robot: {}".format(human_symbol, ai_symbol))
    print("="*35)
    
    for row in range(3):
        row_cells = []
        for col in range(3):
            idx = row * 3 + col
            
            if board[idx] != ' ':
                row_cells.append(f" {board[idx]} ")
            else:
                row_cells.append(f" {idx + 1} ")
        
        print("|".join(row_cells))
        if row < 2:
            print("-----------")
    
    print("="*35 + "\n")


# ============================================================================
# Input Functions
# ============================================================================

def get_human_move_manual(board, human_symbol):
    """Get validated human move from keyboard."""
    while True:
        move_str = input(f"Enter cell number (1-9) for {human_symbol}: ").strip()
        
        if not move_str.isdigit():
            print("❌ Enter a number 1-9")
            continue
        
        cell = int(move_str)
        if not (1 <= cell <= 9):
            print("❌ Enter a number 1-9")
            continue
        
        idx = cell - 1
        
        if board[idx] != ' ':
            print(f"❌ Cell {cell} already occupied!")
            continue
        
        return idx


def get_human_move_camera(board, vision, human_symbol=None):
    """Get human move using camera with verification.
    
    If human_symbol is None, will auto-detect from first move.
    Returns: (move_idx, detected_symbol)
    """
    print("\n" + "="*70)
    if human_symbol:
        print(f"📷 CAMERA DETECTION - Draw your {human_symbol}")
    else:
        print(f"📷 CAMERA DETECTION - Draw your symbol (X or O)")
    print("="*70)
    print(f"1. Draw your symbol on ONE empty cell")
    print("2. Press SPACE to capture")
    print("3. Verify detection")
    print()
    
    max_attempts = 3
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n[Attempt {attempt}/{max_attempts}]")
        
        # Capture (returns board in USER VIEW - same as our internal storage)
        detected_board = vision.capture_and_detect(expected_board=board)
        
        if detected_board is None:
            if human_symbol:
                use_manual = input("❌ Cancelled. Use keyboard? (y/n): ").strip().lower()
                if use_manual == 'y':
                    return get_human_move_manual(board, human_symbol), human_symbol
            continue
        
        # Find new moves
        new_moves = []
        detected_symbols = {}
        
        for i in range(9):
            # New move: board was empty, now has symbol
            if board[i] == ' ' and detected_board[i] != ' ':
                new_moves.append(i)
                detected_symbols[i] = detected_board[i]
        
        # Validation
        if len(new_moves) == 0:
            print("❌ No new moves detected!")
            retry = input("   Try again? (y/n): ").strip().lower()
            if retry != 'y':
                if human_symbol:
                    return get_human_move_manual(board, human_symbol), human_symbol
                else:
                    continue
            continue
        
        if len(new_moves) > 1:
            print(f"❌ Multiple moves detected: {[m+1 for m in new_moves]}")
            retry = input("   Try again? (y/n): ").strip().lower()
            if retry != 'y':
                if human_symbol:
                    return get_human_move_manual(board, human_symbol), human_symbol
                else:
                    continue
            continue
        
        # Single new move found
        move_idx = new_moves[0]
        detected_symbol = detected_symbols[move_idx]
        cell_num = move_idx + 1
        
        # If we already know human's symbol, validate it
        if human_symbol and detected_symbol != human_symbol:
            print(f"❌ Wrong symbol! Expected {human_symbol}, got {detected_symbol}")
            retry = input("   Try again? (y/n): ").strip().lower()
            if retry != 'y':
                return get_human_move_manual(board, human_symbol), human_symbol
            continue
        
        # Confirm
        print(f"\n✓ Detected: {detected_symbol} at cell {cell_num}")
        confirm = input("  Correct? (y/n): ").strip().lower()
        
        if confirm == 'y':
            return move_idx, detected_symbol
        else:
            if human_symbol:
                use_manual = input("  Use keyboard? (y/n): ").strip().lower()
                if use_manual == 'y':
                    return get_human_move_manual(board, human_symbol), human_symbol
    
    # Max attempts
    print(f"\n⚠️  Max attempts reached.")
    if human_symbol:
        print("Using keyboard...")
        return get_human_move_manual(board, human_symbol), human_symbol
    else:
        # First move failed, ask user
        print("Could not detect symbol. Please specify:")
        sym = input("Your symbol (X/O): ").strip().upper()
        if sym not in ['X', 'O']:
            sym = 'X'
        return get_human_move_manual(board, sym), sym


# ============================================================================
# Main Game
# ============================================================================

def main():
    print("\n" + "="*70)
    print(" "*20 + "TIC-TAC-TOE WITH DOBOT")
    print("="*70)
    
    # Initialize vision
    vision = VisionSystem()
    if not vision.initialize():
        print("ERROR: Could not initialize camera!")
        return
    
    # Camera alignment
    align = input("\nAlign camera? (y/n): ").strip().lower()
    if align == 'y':
        vision.align_camera()
    else:
        print("✓ Using defaults")
        vision._update_grid_cells()
    
    # Robot setup
    device = None
    if USE_ROBOT:
        device = robot_moves.get_device()
        draw = input("\nDraw grid? (y/n): ").strip().lower()
        if device and draw == 'y':
            print("Drawing grid...")
            robot_moves.draw_grid_on_device(device, ORIGIN_X, ORIGIN_Y, CELL_SIZE)
            print("✓ Done")
    
    # Always move to camera position before game starts
    if device:
        print("Moving to camera position...")
        robot_moves.move_to_camera_position(device, CAMERA_X, CAMERA_Y, CAMERA_Z, CAMERA_R)
    
    # Game setup
    board = [' '] * 9  # Store in USER VIEW (0-8 = cells 1-9)
    
    print("\n" + "="*70)
    print("GAME SETUP")
    print("="*70)
    
    use_camera = input("\nUse camera detection? (y/n): ").strip().lower() == 'y'
    
    # Symbol will be auto-detected from first move
    human_symbol = None
    ai_symbol = None
    
    print("\n" + "="*70)
    print(" "*25 + "GAME START")
    print("="*70)
    print("\n✓ Ready! Draw your first move (X or O)")
    print("  Robot will automatically play the opposite symbol\n")
    
    # Initial board
    if not use_camera:
        # If not using camera, ask for symbol
        human_symbol = input("Your symbol (X/O): ").strip().upper()
        if human_symbol not in ['X', 'O']:
            human_symbol = 'X'
        ai_symbol = 'O' if human_symbol == 'X' else 'X'
        print(f"✓ You: {human_symbol}, Robot: {ai_symbol}")
    
    if human_symbol:
        print_board(board, human_symbol, ai_symbol)
    
    # Game loop
    turn = 'human'  # Human always goes first
    move_num = 0
    
    while True:
        move_num += 1
        print(f"\n{'='*70}")
        print(f"MOVE #{move_num} - {turn.upper()} TURN")
        print('='*70)
        
        if turn == 'human':
            print(f"\n👤 YOUR TURN" + (f" ({human_symbol})" if human_symbol else ""))
            print("-" * 50)
            
            # Show current board state before move
            if human_symbol:
                print_board(board, human_symbol, ai_symbol)
            
            # Move robot to camera position BEFORE detection
            if use_camera and device:
                print("📷 Moving robot to camera position for detection...")
                robot_moves.move_to_camera_position(device, CAMERA_X, CAMERA_Y, CAMERA_Z, CAMERA_R)
            
            if use_camera:
                move_idx, detected_symbol = get_human_move_camera(board, vision, human_symbol)
                
                # First move - auto-detect symbol
                if human_symbol is None:
                    human_symbol = detected_symbol
                    ai_symbol = 'O' if human_symbol == 'X' else 'X'
                    print(f"\n✓ Symbol detected! You: {human_symbol}, Robot: {ai_symbol}")
            else:
                move_idx = get_human_move_manual(board, human_symbol)
            
            board[move_idx] = human_symbol
            print(f"\n✓ You played {human_symbol} at cell {move_idx + 1}")
            
        else:
            print(f"\n🤖 ROBOT TURN ({ai_symbol})")
            print("-" * 50)
            
            # Show current board
            print_board(board, human_symbol, ai_symbol)
            
            print("Thinking...")
            move_idx = game_logic.get_best_move(board, ai_symbol)
            
            if move_idx is None:
                print("No moves!")
                break
            
            board[move_idx] = ai_symbol
            print(f"✓ Robot plays {ai_symbol} at cell {move_idx + 1}")
            
            # Draw on physical board
            if device:
                print("Drawing...")
                cx, cy = get_cell_center(move_idx)
                if ai_symbol == 'X':
                    robot_moves.drawX(device, cx, cy, CELL_SIZE // 2)
                else:
                    robot_moves.drawO(device, cx, cy, CELL_SIZE // 3)
                
                # Return to camera position after drawing
                print("Returning to camera position...")
                robot_moves.move_to_camera_position(device, CAMERA_X, CAMERA_Y, CAMERA_Z, CAMERA_R)
                print("✓ Drawn")
        
        # Show updated board
        print_board(board, human_symbol, ai_symbol)
        
        # Check winner
        winner = game_logic.check_winner(board)
        if winner:
            print("\n" + "="*70)
            print(" "*25 + "GAME OVER")
            print("="*70)
            
            if winner == 'D':
                print("\n🤝 DRAW!")
                if device:
                    dx = ORIGIN_X + 3 * CELL_SIZE + 20
                    dy = ORIGIN_Y + CELL_SIZE
                    robot_moves.drawD(device, dx, dy)
                    print("✓ D symbol drawn")
            else:
                if winner == human_symbol:
                    print(f"\n🎉 YOU WIN! ({human_symbol})")
                else:
                    print(f"\n🤖 ROBOT WINS! ({ai_symbol})")
                
                if device:
                    winning_line = game_logic.get_winning_line(board)
                    if winning_line:
                        print("Drawing strike line...")
                        # Transform winning line to robot coordinates
                        robot_line = tuple(user_to_robot_physical(idx) for idx in winning_line)
                        robot_moves.strike_line(device, ORIGIN_X, ORIGIN_Y, CELL_SIZE, robot_line)
                        print("✓ Strike line drawn")
            
            print("="*70)
            break
        
        # Switch turns
        turn = 'robot' if turn == 'human' else 'human'
    
    # Cleanup
    vision.close()
    if device:
        device.close()
    print("\n✓ Game ended\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
