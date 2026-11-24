import math

class Board:
    def __init__(self):
        self.cells = [' '] * 9
    
    def copy(self):
        b = Board()
        b.cells = self.cells.copy()
        return b
    
    def place(self, index, symbol):
        if not (0 <= index < 9):
            return False
        if self.cells[index] != ' ':
            return False
        self.cells[index] = symbol
        return True
    
    def available_moves(self):
        return [i for i, v in enumerate(self.cells) if v == ' ']
    
    def winner(self):
        lines = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for a, b, c in lines:
            if self.cells[a] != ' ' and self.cells[a] == self.cells[b] == self.cells[c]:
                return self.cells[a], (a, b, c)
        if ' ' not in self.cells:
            return 'D', None
        return None, None


def minimax(board, depth, maximizing, robot_symbol, human_symbol, alpha=-math.inf, beta=math.inf):
    win, _ = board.winner()
    if win == robot_symbol:
        return 10 - depth, None
    if win == human_symbol:
        return depth - 10, None
    if win == 'D':
        return 0, None
    
    if maximizing:
        best = -math.inf
        move = None
        for m in board.available_moves():
            b = board.copy()
            b.place(m, robot_symbol)
            val, _ = minimax(b, depth + 1, False, robot_symbol, human_symbol, alpha, beta)
            if val > best:
                best = val
                move = m
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return best, move
    else:
        best = math.inf
        move = None
        for m in board.available_moves():
            b = board.copy()
            b.place(m, human_symbol)
            val, _ = minimax(b, depth + 1, True, robot_symbol, human_symbol, alpha, beta)
            if val < best:
                best = val
                move = m
            beta = min(beta, val)
            if beta <= alpha:
                break
        return best, move


def get_best_move(cells, robot_symbol):
    """Get best move for robot using minimax."""
    board = Board()
    board.cells = cells.copy()
    
    human_symbol = 'O' if robot_symbol == 'X' else 'X'
    _, move = minimax(board, 0, True, robot_symbol, human_symbol)
    
    return move


def check_winner(cells):
    """Check for winner or draw."""
    board = Board()
    board.cells = cells.copy()
    
    winner, _ = board.winner()
    return winner


def get_winning_line(cells):
    """Get the winning line (tuple of 3 indices) if there is a winner."""
    board = Board()
    board.cells = cells.copy()
    
    _, line = board.winner()
    return line
