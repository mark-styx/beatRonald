import pandas as pd
import numpy as np
from random import randint

class space:
    def __init__(self,row,column) -> None:
        self.row,self.column = row,column
        self.type = 'primary' if (row%2 == 0 and column%2 == 1) or (row%2 == 1 and column%2 == 0) else 'secondary'
        self.occupied = None

    def display(self):
        if not self.occupied:
            return {
              'primary':'[0]'
            , 'secondary':'[X]'
            }[self.type]
        else: return f'[{self.occupied}]'

    def representation(self):
        if not self.occupied:
            return {
              'primary': 0
            , 'secondary': 'X'
            }[self.type]
        else: return self.occupied

    def occupy(self,by_whom):
        if self.type == 'secondary':
            return 0
        elif self.occupied:
            return 0
        else:
            self.occupied = by_whom
    
    def vacate(self):
        self.occupied = None


class piece:
    def __init__(self,team:int,pident:int) -> None:
        self.team = team
        self.pident = pident
        self.location = None
        self.captured = False
        self.king = False
    
    def move(self,row,column):
        self.location = (row,column)

    def capture(self):
        self.captured = True
    
    def kingme(self):
        if not self.king:
            self.pident += 1
            self.king = True


class board:
    def __init__(self,rows=8,columns=8) -> None:
        self.__rows,self.__columns = rows,columns
        self.spaces = {(r,c):space(r,c) for c in range(columns) for r in range(rows)}

    def show(self):
        representation = ' |  0  1  2  3  4  5  6  7 \n'
        for r in range(self.__rows):
            if r != 0:
                representation += '\n'
            representation += f'{r}| '
            for c in range(self.__columns):
                representation += self.spaces[(r,c)].display()
        return representation

    def array_rep(self):
        representation = []
        for r in range(self.__rows):
            for c in range(self.__columns):
                representation.append(self.spaces[(r,c)].representation())
        return representation

    def coordinate_representation(self):
        representation = []
        for r in range(self.__rows):
            for c in range(self.__columns):
                if self.spaces[(r,c)].type == 'primary':
                    representation.append(
                        (r,c,self.spaces[(r,c)].representation())
                        )
        return representation

    def occupiable_spaces(self):
        return [space for space in self.spaces.values() if space.type == 'primary']


class game:
    def __init__(self) -> None:
        self.board = board()
        self.special_case = None
        self.finished = False

    def create_game(self,team1,team2)->tuple:
        self.t1,self.t2 = team1,team2
        self.t1.orientation,self.t2.orientation = ('L->R','L<-R')
        self.initiative = self.t1
        self.rest = self.t2
        self.set_board()

    def set_board(self):
        for p,s in zip(self.t1.pieces,self.board.occupiable_spaces()):
            s.occupy(p.pident)
            p.move(s.row,s.column)
        for p,s in zip(self.t2.pieces,self.board.occupiable_spaces()[::-1]):
            s.occupy(p.pident)
            p.move(s.row,s.column)

    def observation(self):
        return tuple(self.board.coordinate_representation())

    def game_state_eval(self):
        if not self.random_move(self.initiative):
            self.finished = True
            self.initiative.score -= 10
            self.rest.score += 10
        if self.t1.consecutive_invalid_moves >= 1000:
            self.t2.score += 10
            self.t1.score -= 10
            self.finished = True
        if self.t2.consecutive_invalid_moves >= 1000:
            self.t1.score += 10
            self.t2.score -= 10
            self.finished = True
        if not any(self.t1.field):
            self.t2.score += 10
            self.t1.score -= 10
            self.finished = True
        elif not any(self.t2.field):
            self.t1.score += 10
            self.t2.score -= 10
            self.finished = True

    def _opposition(self,team):
        return {
              self.t1:self.t2
            , self.t2:self.t1
        }[team]

    def update(self,team,mvFrom:tuple,mvTo:tuple):
        opponent = self._opposition(team)
        self.potential_captures = self.evaluate_capture_opportunities(team)
        try:
            mvPiece = team.field[mvFrom]
            valid,reward = self.move_evaluation(team,team.orientation,mvPiece,mvFrom,mvTo)
            if not valid:
                #team.field[mvFrom].capture();print(f'{mvFrom} captured')
                #self.board.spaces[mvFrom].vacate()
                pass
            elif valid:
                self.board.spaces[mvFrom].vacate()
                if mvTo[1] in [0,7]:
                    mvPiece.kingme()
                self.board.spaces[mvTo].occupy(team.field[mvFrom].pident)
            if reward == 2:
                captured = self.potential_captures.get(mvFrom).get(mvTo)
                opponent.field[captured].capture();print(f'{captured} captured')
                self.board.spaces[captured].vacate()
                opponent.score -= 1
            if reward == -2:
                missed = list(self.potential_captures.keys())[0]
                team.field[missed].capture();print(f'{missed} captured')
                self.board.spaces[missed].vacate()
        except:
            valid,reward = 0,-2
        team.score += reward
        if valid:
            team.consecutive_invalid_moves = 0
            self.initiative = self._opposition(team)
            self.rest = team
        elif not valid:
            team.consecutive_invalid_moves += 1
        self.game_state_eval()
        return valid

    def move_evaluation(self,team,orientation,mvPiece:piece,mvFrom:tuple,mvTo:tuple,debug=True):
        
        # direction
        direction = 'L->R' if mvFrom[1] < mvTo[1] else 'L<-R'
        if not mvPiece.king and orientation != direction:
            if debug:print(f'invalid move for {team.identifier}: {mvFrom} to {mvTo} | wrong direction')
            return 0,-1

        # occupied already
        elif mvTo in self.occupied_space():
            if debug:print(f'invalid move for {team.identifier}: {mvFrom} to {mvTo} | occupied space')
            return 0,-1

        # adjacency
        elif mvTo in self.find_adjacent(mvFrom):
            if any(self.potential_captures):
                if debug:print(f'{team.identifier}: {mvFrom} to {mvTo} | missed capture')
                return 1,0 # missed capture opp
            else:
                if debug:print(f'{team.identifier}: {mvFrom} to {mvTo}')
                return 1,1 # not occupied, proper direction, is adjacent, no capture opps
        
        # jump
        elif (mvFrom in self.potential_captures) and mvTo in self.potential_captures.get(mvFrom,[]):
                if debug:print(f'{team.identifier} jump: {mvFrom} to {mvTo}')
                return 1,2

        else: return 0,-1

    def random_move(self,team):
        # start with captures
        captures = self.evaluate_capture_opportunities(team)
        if any(captures):
            k = list(captures.keys())
            key = k[randint(0,len(k)-1)]
            k2 = list(captures[key].keys())
            key2 = k2[randint(0,len(k2)-1)]
            return {'mvFrom':key,'mvTo':key2}
        # move on to benign moves
        possible_moves = []
        open_spaces = self.unnoccupied_space()
        for loc,piece in team.field.items():
            for space in open_spaces:
                valid,_ = self.move_evaluation(team,team.orientation,piece,loc,space,debug=False)
                if valid:possible_moves.append({'mvFrom':loc,'mvTo':space})
        if not any(possible_moves): return
        return possible_moves[randint(0,len(possible_moves)-1)]

    def evaluate_capture_opportunities(self,team):
        opponent = self.t2 if team is self.t1 else self.t1
        self.potential_captures = {}
        for loc,piece in team.field.items():
            # adjacent
            a1 = [x for x in self.find_adjacent(loc) if x not in team.field]
            # correct moveable orientation
            a1 = self.orientation_filter(loc,a1,team.orientation,piece.king)
            # immediately adjacent opponents
            a1ops = [x for x in a1 if x in opponent.field]
            # capture_ops = {x:([y for y in self.orientation_filter(loc,self.find_adjacent(x),team.orientation,piece.king) if y not in self.occupied_space()]) for x in a1ops}
            capture_ops = {y:x for x in a1ops for y in self.orientation_filter(loc,self.find_adjacent(x),team.orientation,piece.king) if y not in self.occupied_space()}
            if capture_ops:
                self.potential_captures[loc] = capture_ops
        keys_to_remove = []
        for mvf in self.potential_captures:
            for mvt in self.potential_captures[mvf]:
                if abs(mvf[0] - mvt[0]) != 2 or abs(mvf[1] - mvt[1]) !=2:
                    keys_to_remove.append((mvf,mvt))
        for key in keys_to_remove:
            self.potential_captures[key[0]].__delitem__(key[1])
            if not any(self.potential_captures[key[0]]):
                self.potential_captures.__delitem__(key[0])
        return self.potential_captures

    def orientation_filter(self,start,locations,direction,king=False):
        if king == True:
            pass
        elif direction == 'L->R':
            locations = [x for x in locations if x[1] > start[1]]
        else:
            locations = [x for x in locations if x[1] < start[1]]
        return locations

    def find_adjacent(self,location:tuple):
        r,c = location
        return [
            (x.row,x.column) for x in self.board.occupiable_spaces() if (
                abs(r-x.row)<2 and abs(c-x.column)<2 and (x.row,x.column) != location
                )
            ]

    def occupied_space(self):
        return [(space.row,space.column) for space in self.board.occupiable_spaces() if space.occupied]

    def unnoccupied_space(self):
        return [(space.row,space.column) for space in self.board.occupiable_spaces() if not space.occupied]

    def opponent_capture(self):
        pass


class team:

    def __init__(self,identifier:int,field:int=12) -> None:
        self.identifier = identifier
        self.pident = {'base':self.identifier+1,'evolved':self.identifier+2}
        self.range = self.identifier+2
        self.pieces = [piece(self.identifier,self.pident['base']) for i in range(field)]
        self.score = 0
        self.consecutive_invalid_moves = 0

    def update_field(self):
        self.field = {x.location:x for x in self.pieces if x.captured == False}

    def move(self,mvFrom:tuple,mvTo:tuple):
        self.update_field()
        # need to write something to penalize moves that don't exist
        valid = self.game.update(self,mvFrom,mvTo)
        if valid:
            piece = self.field[mvFrom]
            piece.move(*mvTo)
        self.update_field()

    def join_game(self,game:game):
        self.game = game
        self.update_field()

def setup():
    team1.move((1,2),(2,3))
    team1.move((2,3),(1,4))
    print(G.board.show())
    print(G.evaluate_capture_opportunities(team2))

def random_play_step():
    team1.move(**G.random_move(team1))
    team2.move(**G.random_move(team2))
    print(G.board.show())
    print('\n\n')

if __name__ == '__main__':
    G = game()
    team1 = team(0)
    team2 = team(2)
    G.create_game(team1,team2)
    team1.join_game(G)
    team2.join_game(G)
    print(G.board.show())
    setup()