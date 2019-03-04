import random
from time import time
from time import sleep

from copy import deepcopy


class Team10():
    
    def __init__(self):
        self.flag = 'x'
        self.opp_flag = 'o'
        self.win_val =1000000000
        self.bonus_move = False
        self.heuristic_value = [0,1,10,100]
        self.pos_weight = ((4,6,4),(6,3,6),(4,6,4))
        self.available_moves = []
        self.start_time = 0
        self.end_time = 23
        self.last_winner = -1
        self.m2 = 1
        self.dict = {}
        self.block_hash = [[[ int(0) for i in range(3) ] for j in range(3)] for k in range(2) ]
        self.hash_table = [[] for i in range(2)]
        self.patterns = []
        self.patterns_init()
        self.hash_init()

    def hash_init(self):
        for i in range(9):
            self.hash_table[0].append(2**(i+1))
            self.hash_table[1].append(3**(i+1))

    def patterns_init(self):
        for i in range(3):
            self.patterns.append(((i,0), (i,1), (i,2)))
            self.patterns.append(((0,i), (1,i), (2,i)))
        self.patterns.append(((0,0),(1,1),(2,2)))
        self.patterns.append(((0,2),(1,1),(2,0)))
    def hash_me(self,move,ply):
        i = move[0]
        j = move[1]
        k = move[2]
        self.block_hash[i][j/3][k/3] += self.hash_table[ply][(j%3)*3 + (k%3)] 
        
    def get_opp(self, flag):
        if flag == 'x': return 'o'
        return 'x'

    def compute_heuristic_block(self, board, move, flag):
        heur_val = 0
        for l in self.patterns:
            ct_self = 0
            ct_opp = 0
            for k in l:
                i = move[1] + k[0]
                j = move[2] + k[1]
                if board.big_boards_status[move[0]][i][j] == flag:
                    ct_self += 1
                elif board.big_boards_status[move[0]][i][j] == self.get_opp(flag):
                    ct_opp += 1
            if not ct_opp or not ct_self:
                heur_val += (self.heuristic_value[ct_self] - self.heuristic_value[ct_opp]*1.5)
        return heur_val

    def compute_heuristic_board(self,board,i,flag):
        heur_val = 0
        for l in self.patterns:
            ct_self = 0
            ct_opp = 0
            for k in l:
                if board.small_boards_status[i][k[0]][k[1]] == flag:
                    ct_self += 1
                elif board.small_boards_status[i][k[0]][k[1]] == self.get_opp(flag):
                    ct_opp += 1
            if not ct_opp or not ct_self:
                heur_val += (self.heuristic_value[ct_self]- self.heuristic_value[ct_opp]*1.5)*100*self.m2

        for j in range(3):
            for k in range(3):
                mult = 1
                if board.small_boards_status[i][j][k] == ('-' or 'd'):
                    mult = 0
                elif board.small_boards_status[i][j][k] == flag:
                    mult = 1
                else:
                    mult = -1   
                heur_val += self.pos_weight[j][k]*150*mult
                  
        return heur_val
    
    def heuristic(self, board, flag):
        fl, status = board.find_terminal_state()
        if status == "WON":
            return self.win_val if fl == flag else -self.win_val
        heur_val = 0
        for i in range(2):
            ct_dash = 0
            for j in range(3):
                for k in range(3):
                    if board.small_boards_status[i][j][k] == '-':
                        ct_dash += 1
                    if self.block_hash[i][j][k] in self.dict:
                        heur_val += self.dict[self.block_hash[i][j][k]]
                    else:
                        var = self.compute_heuristic_block(board,(i,j*3,k*3),flag)  
                        heur_val += var
                        if len(self.dict) > 5000 : self.dict = {}
                        self.dict[self.block_hash[i][j][k]] = var
            
            self.m2 = (9-ct_dash)*(9-ct_dash)*0.3 + 1
            heur_val += self.compute_heuristic_board(board, i, flag)
        return heur_val

    def minimax(self, board, depth, old_move, ply, alpha, beta):
        status = board.find_terminal_state()[1]
        if status == "WON":
            return self.win_val,"NULL" if ply == 1 else -self.win_val,"NULL"
        if status == "DRAW":
            return -self.win_val/400, "NULL"
        if (time() - self.start_time > self.end_time) or depth == -1:
            return self.heuristic(board, self.flag), "NULL"

        valid_moves = board.find_valid_move_cells(old_move)
        best_move = valid_moves[0]
        prune_val = float("-inf") if ply else float("inf")
        temp_winner = self.last_winner
        temp_ply = ply
        for i in valid_moves:
            if board.update(old_move,i,self.flag if ply else self.opp_flag)[1]:
                if self.last_winner == -1:
                    self.last_winner = ply
                    ply ^= 1
                elif self.last_winner == ply:
                    self.last_winner = -1
                elif self.last_winner != ply:
                    self.last_winner = ply
                    ply ^= 1
            else:
                self.last_winner = -1
            self.hash_me(i,ply)    
            val = self.minimax(board, depth-1, i, ply^1, alpha, beta)[0]
            self.hash_me(i,ply)
            self.last_winner = temp_winner
            ply = temp_ply
            if ply:
                if val > prune_val: best_move = i
                prune_val = max(prune_val, val)
                alpha = max(alpha, prune_val)
            else:
                if val < prune_val: best_move = i
                prune_val = min(prune_val, val)
                beta = min(beta, prune_val)
            board.big_boards_status[i[0]][i[1]][i[2]] = '-'
            board.small_boards_status[i[0]][i[1]/3][i[2]/3] = '-'
            if alpha >= beta:
                break
        return prune_val, best_move

    def move(self, board, old_move, flag):
        self.start_time= time()
        self.flag = flag
        self.opp_flag = self.get_opp(flag)
        if board.big_boards_status[old_move[0]][old_move[1]][old_move[2]] == self.opp_flag:
            self.hash_me(old_move,0)
        if board.small_boards_status[old_move[0]][old_move[1]/3][old_move[2]/3] == self.flag:
            self.last_winner = 1
        elif board.small_boards_status[old_move[0]][old_move[1]/3][old_move[2]/3] == self.opp_flag:
            self.last_winner = 0
        else:
            self.last_winner = -1
        if old_move == (-1,-1,-1):
            self.hash_me((0,1,1),1)
            return (0,1,1)
        valid_moves = board.find_valid_move_cells(old_move)
        best_move = valid_moves[0]
        b = deepcopy(board)
        max_depth = 2
        while 1:
            move = self.minimax(b, max_depth,old_move, 1, float("-inf"), float("inf"))[1]
            if (time() - self.start_time) > self.end_time or max_depth > 5:
                break
            best_move = move
            max_depth += 1
        del b
        self.hash_me(best_move,1)
        return best_move
