from flask import Flask, render_template, redirect, url_for, session
from random import choices
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# ❌/⭕
p1_symbol = '❌'
p2_symbol = '⭕'
no_symbol = ''

def create_board():
    return [[no_symbol]*3 for i in range(3)]

def check_winner(board):
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] != no_symbol:
            return row[0]
    
    # Check columns
    for j in range(3):
        if board[0][j] == board[1][j] == board[2][j] != no_symbol:
            return board[0][j]
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != no_symbol:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != no_symbol:
        return board[0][2]
    
    return None

def check_draw(board):
    for row in board:
        if no_symbol in row:
            return False
    return True

def find_prob(board, unmarked_indexes):
    winning_index = [
        [(0,0), (0,1), (0,2)], [(1,0), (1,1), (1,2)], [(2,0), (2,1), (2,2)],
        [(0,0), (1,0), (2,0)], [(0,1), (1,1), (2,1)], [(0,2), (1,2), (2,2)],
        [(0,0), (1,1), (2,2)], [(0,2), (1,1), (2,0)]
    ]
    myboard_w = [[0]*3 for i in range(3)]
    
    for index in winning_index:
        freq = [board[i][j] for (i,j) in index].count(p1_symbol)
        freq2 = [board[i][j] for (i,j) in index].count(p2_symbol)
        
        if freq2 == 2:
            for (i,j) in index:
                myboard_w[i][j] += 1000000
        if freq == 2:
            for (i,j) in index:
                myboard_w[i][j] += 1000
        elif freq == 1 and freq2 == 0:
            for (i,j) in index:
                myboard_w[i][j] += 50
        elif freq == 0 and freq2 == 0:
            for (i,j) in index:
                myboard_w[i][j] += 1
    
    weights_unmarked = [myboard_w[i][j] for (i,j) in unmarked_indexes]
    total = sum(weights_unmarked)
    if total == 0:
        prob = [1/len(weights_unmarked)] * len(weights_unmarked)
    else:
        prob = [w/total for w in weights_unmarked]
    return prob

def ai_mark(board):
    unmarked_indexes = [(i,j) for i in range(len(board)) for j in range(len(board[i])) if board[i][j] == no_symbol]
    if unmarked_indexes != []:
        p = find_prob(board, unmarked_indexes)
        (i,j) = choices(unmarked_indexes, weights=p, k=1)[0]
        board[i][j] = p2_symbol

@app.route('/')
def home():
    session.clear()
    return render_template('menu.html')

@app.route('/start/<mode>')
def start_game(mode):
    session['mode'] = mode
    session['board'] = create_board()
    session['current_turn'] = 'p1'
    session['game_over'] = False
    session['winner'] = None
    
    if mode == 'friend':
        return render_template('names.html')
    else:
        session['p1_name'] = 'You'
        session['p2_name'] = 'AI'
        return redirect(url_for('game'))

@app.route('/set_names/<p1>/<p2>')
def set_names(p1, p2):
    session['p1_name'] = p1 if p1 else 'Player 1'
    session['p2_name'] = p2 if p2 else 'Player 2'
    return redirect(url_for('game'))

@app.route('/game')
def game():
    board = session.get('board', create_board())
    mode = session.get('mode', 'ai')
    game_over = session.get('game_over', False)
    winner = session.get('winner', None)
    current_turn = session.get('current_turn', 'p1')
    p1_name = session.get('p1_name', 'Player 1')
    p2_name = session.get('p2_name', 'Player 2')
    
    winner_name = None
    if winner == p1_symbol:
        winner_name = p1_name
    elif winner == p2_symbol:
        winner_name = p2_name
    elif winner == 'draw':
        winner_name = 'Draw'
    
    return render_template('index.html', 
                         board=board, 
                         mode=mode,
                         game_over=game_over,
                         winner=winner_name,
                         current_turn=current_turn,
                         p1_name=p1_name,
                         p2_name=p2_name,
                         p1_symbol=p1_symbol,
                         p2_symbol=p2_symbol)

@app.route('/mark/<int:i>/<int:j>')
def mark(i, j):
    board = session.get('board', create_board())
    mode = session.get('mode', 'ai')
    current_turn = session.get('current_turn', 'p1')
    game_over = session.get('game_over', False)
    
    if game_over:
        return redirect(url_for('game'))
    
    if board[i][j] == no_symbol:
        if mode == 'ai':
            if current_turn == 'p1':
                board[i][j] = p1_symbol
                winner = check_winner(board)
                
                if winner:
                    session['game_over'] = True
                    session['winner'] = winner
                elif check_draw(board):
                    session['game_over'] = True
                    session['winner'] = 'draw'
                else:
                    ai_mark(board)
                    winner = check_winner(board)
                    if winner:
                        session['game_over'] = True
                        session['winner'] = winner
                    elif check_draw(board):
                        session['game_over'] = True
                        session['winner'] = 'draw'
        else:
            if current_turn == 'p1':
                board[i][j] = p1_symbol
                session['current_turn'] = 'p2'
            else:
                board[i][j] = p2_symbol
                session['current_turn'] = 'p1'
            
            winner = check_winner(board)
            if winner:
                session['game_over'] = True
                session['winner'] = winner
            elif check_draw(board):
                session['game_over'] = True
                session['winner'] = 'draw'
        
        session['board'] = board
    
    return redirect(url_for('game'))

@app.route('/reset')
def reset():
    mode = session.get('mode', 'ai')
    p1_name = session.get('p1_name', 'Player 1')
    p2_name = session.get('p2_name', 'Player 2')
    
    session['board'] = create_board()
    session['current_turn'] = 'p1'
    session['game_over'] = False
    session['winner'] = None
    session['p1_name'] = p1_name
    session['p2_name'] = p2_name
    session['mode'] = mode
    
    return redirect(url_for('game'))

if __name__ == '__main__':
    app.run(debug=True)