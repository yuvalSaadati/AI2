# ===============================================================================
# Imports
# ===============================================================================
from collections import defaultdict
import abstract
import players.simple_player
from utils import INFINITY
from checkers.consts import EM, PAWN_COLOR, KING_COLOR, OPPONENT_COLOR

# ===============================================================================
# Globals
# ===============================================================================
PAWN_WEIGHT = 1
KING_WEIGHT = 1.5
LAST_ROW_PAWN = 0.8
CENTER_BOARD_PAWN = 0.5
MIDDLE_ROW_PAWN = 0.1
VULNERABLE_PAWN = -0.6
PROTECTED_PAWN = 0.6


# ===============================================================================
# Player
# ===============================================================================

class Player(players.simple_player.Player):
    """
    Calculate the utility for the player based on the state of the board
    2 arrays one for the player one for the rival.
    each array contains what we take into consideration for the heuristic
    -number of pawns
    -number of kings
    -number of pawns on the last row in the player side
    -number of pawns in the center of the board
    -number of protected pawns
    -number of vulnerable pawns
    return value: the sum of the player array after subtraction of the rival array
    """
    def utility(self, state):
        my_hur = [None] * 7
        op_hur = [None] * 7
        my_hur[0], op_hur[0] = self.pawns_utility(state)
        my_hur[1], op_hur[1] = self.kings_utility(state)
        my_hur[2], op_hur[2] = self.last_row(state)
        my_hur[3], op_hur[3] = self.center_board(state)
        my_hur[4], op_hur[4] = self.middle_rows_not_center(state)
        my_hur[5], op_hur[5] = self.protected_player(state)
        my_hur[6], op_hur[6] = self.vulnerable_player(state)

        if not my_hur:
            # I have no tools left
            return -INFINITY
        elif not op_hur:
            # The opponent has no tools left
            return INFINITY
        else:
            for i in range(len(my_hur)):
                my_hur[i] -= op_hur[i]
            heuristic = sum(my_hur)
            return heuristic

    """
    Calculate the number of pawns the player and rival have on the board
    and returns both
    """

    def pawns_utility(self, state):
        piece_counts = defaultdict(lambda: 0)
        for loc_val in state.board.values():
            if loc_val != EM:
                piece_counts[loc_val] += 1

        opponent_color = OPPONENT_COLOR[self.color]

        my_u = PAWN_WEIGHT * piece_counts[PAWN_COLOR[self.color]]
        op_u = PAWN_WEIGHT * piece_counts[PAWN_COLOR[opponent_color]]
        return my_u, op_u

    """
        Calculate the number of kings the player and rival have on the board
        and returns both
    """
    def kings_utility(self, state):
        piece_counts = defaultdict(lambda: 0)
        for loc_val in state.board.values():
            if loc_val != EM:
                piece_counts[loc_val] += 1

        opponent_color = OPPONENT_COLOR[self.color]

        my_u = KING_WEIGHT * piece_counts[KING_COLOR[self.color]]
        op_u = KING_WEIGHT * piece_counts[KING_COLOR[opponent_color]]
        return my_u, op_u

    """
        Calculate the number of pieces the player and the rival have on the last row of the board
        for red player its the 0 row and for black player its the 7 row
        and returns both
    """
    def last_row(self, state):
        piece_counts = defaultdict(lambda: 0)
        for key, value in state.board.items():
            if value != EM and key[0] == 7 and (value == 'b' or value == 'B'):
                piece_counts[value] += 1
            elif value != EM and key[0] == 0 and (value == 'r' or value == 'R'):
                piece_counts[value] += 1

        opponent_color = OPPONENT_COLOR[self.color]

        my_u = LAST_ROW_PAWN * (piece_counts[KING_COLOR[self.color]] + piece_counts[PAWN_COLOR[self.color]])
        op_u = LAST_ROW_PAWN * (piece_counts[KING_COLOR[opponent_color]] + piece_counts[PAWN_COLOR[opponent_color]])
        return my_u, op_u

    """
        Calculate the number of pieces the player and the rival have on the center of the board
        the center is the 3,4 rows and the 2,3,4,5 columns
        and returns both
    """
    def center_board(self, state):
        piece_counts = defaultdict(lambda: 0)
        for key, value in state.board.items():
            if value != EM and (key[0] == 3 or key[0] == 4) and (2 <= key[1] <= 5):
                piece_counts[value] += 1

        opponent_color = OPPONENT_COLOR[self.color]

        my_u = CENTER_BOARD_PAWN * (piece_counts[KING_COLOR[self.color]] + piece_counts[PAWN_COLOR[self.color]])
        op_u = CENTER_BOARD_PAWN * (piece_counts[KING_COLOR[opponent_color]] + piece_counts[PAWN_COLOR[opponent_color]])
        return my_u, op_u

    """
        Calculate the number of pieces the player and the rival have on the middle but not in the center
        the middle is the 3,4 rows and the 0,1,6,7 columns
        and returns both
    """
    def middle_rows_not_center(self, state):
        piece_counts = defaultdict(lambda: 0)
        for key, value in state.board.items():
            if value != EM and (key[0] == 3 or key[0] == 4) and (2 > key[1] or key[1] > 5):
                piece_counts[value] += 1

        opponent_color = OPPONENT_COLOR[self.color]

        my_u = MIDDLE_ROW_PAWN * (piece_counts[KING_COLOR[self.color]] + piece_counts[PAWN_COLOR[self.color]])
        op_u = MIDDLE_ROW_PAWN * (piece_counts[KING_COLOR[opponent_color]] + piece_counts[PAWN_COLOR[opponent_color]])
        return my_u, op_u
    """
        Calculate the number of protected pieces the player and the rival have on the board
        protected pawn is a pawn that can't be jumped over on the next turn
        it calculate it for the black and red player
        and returns both
    """
    def protected_player(self, state):
        piece_counts = defaultdict(lambda: 0)
        piece_counts = self.protected_player_black(state, piece_counts)
        piece_counts = self.protected_player_red(state, piece_counts)
        opponent_color = OPPONENT_COLOR[self.color]
        my_u = PROTECTED_PAWN * (piece_counts[KING_COLOR[self.color]] + piece_counts[PAWN_COLOR[self.color]])
        op_u = PROTECTED_PAWN * (piece_counts[KING_COLOR[opponent_color]] + piece_counts[PAWN_COLOR[opponent_color]])
        return my_u, op_u
    """
        Calculate the number of protected pieces the black player has
        and returns it
    """
    def protected_player_black(self, state, piece_counts):
        for key, value in state.board.items():
            if value != EM and key[0] < 7:
                if key[1] == 0 or key[1] == 7:
                    piece_counts[value] += 1
                elif (value == 'b' or value == 'B') and state.board[(key[0] + 1, key[1] - 1)] != EM and \
                        (state.board[(key[0] + 1, key[1] - 1)] != 'R'
                         and (state.board[(key[0] + 1, key[1] + 1)] != EM
                              and state.board[(key[0] + 1, key[1] + 1)] != 'R')):
                    piece_counts[value] += 1
        return piece_counts

    """
        Calculate the number of protected pieces the red player has
        and returns it
    """
    def protected_player_red(self, state, piece_counts):
        for key, value in state.board.items():
            if value != EM and key[0] > 0:
                if key[1] == 0 or key[1] == 7:
                    piece_counts[value] += 1
                elif (value == 'r' or value == 'R') and state.board[(key[0] - 1, key[1] - 1)] != EM and \
                        (state.board[(key[0] - 1, key[1] - 1)] != 'B'
                         and (state.board[(key[0] - 1, key[1] + 1)] != EM
                              and state.board[(key[0] - 1, key[1] + 1)] != 'B')):
                    piece_counts[value] += 1
        return piece_counts
    """
    Count the amount of pieces in board that are vulnerable.
    Vulnerable player is a player that can't save himself and the rival will jump on him in his next move. 
    :return: the number of pieces vulnerable on the board for the player and for the rival
    """
    def vulnerable_player(self, state):
        piece_counts = defaultdict(lambda: 0)
        piece_counts = self.vulnerable_black_pawn(state, piece_counts)
        piece_counts = self.vulnerable_red_pawn(state, piece_counts)
        opponent_color = OPPONENT_COLOR[self.color]
        my_u = VULNERABLE_PAWN * (piece_counts[KING_COLOR[self.color]] + piece_counts[PAWN_COLOR[self.color]])
        op_u = VULNERABLE_PAWN * (piece_counts[KING_COLOR[opponent_color]] + piece_counts[PAWN_COLOR[opponent_color]])
        return my_u, op_u

    """
        Count the amount black in board that are vulnerable.
        Vulnerable player is a player that can't save himself and the rival will jump on him in his next move. 
        :return: the number of black pieces vulnerable on the board
        """
    def vulnerable_black_pawn(self, state, piece_counts):
        for key, value in state.board.items():
            if value != EM and 0 < key[0] < 7 and 0 < key[1] < 7:
                if (value == 'b' or value == 'B') and (state.board[(key[0] + 1, key[1] - 1)] == EM and
                                                       (state.board[(key[0] - 1, key[1] + 1)] == 'r' or
                                                        state.board[(key[0] - 1, key[1] + 1)] == 'R')) \
                        and (state.board[(key[0] + 1, key[1] + 1)] == EM and
                             (state.board[(key[0] - 1, key[1] - 1)] == 'r' or
                              state.board[(key[0] - 1, key[1] - 1)] == 'R')):
                    piece_counts[value] += 1
                if (value == 'b' or value == 'B') and (state.board[(key[0] - 1, key[1] + 1)] == EM and
                                                       (state.board[(key[0] + 1, key[1] - 1)] == 'R')) \
                        and (state.board[(key[0] - 1, key[1] - 1)] == EM and
                             (state.board[(key[0] + 1, key[1] + 1)] == 'R')):
                    piece_counts[value] += 1
        return piece_counts

    """
        Count the amount red in board that are vulnerable.
        Vulnerable player is a player that can't save himself and the rival will jump on him in his next move. 
        :return: the number of red pieces vulnerable on the board
    """
    def vulnerable_red_pawn(self, state, piece_counts):
        for key, value in state.board.items():
            if value != EM and 0 < key[0] < 7 and 0 < key[1] < 7:
                if (value == 'r' or value == 'R') and (state.board[(key[0] - 1, key[1] + 1)] == EM and
                                                       (state.board[(key[0] + 1, key[1] - 1)] == 'b' or
                                                        state.board[(key[0] + 1, key[1] - 1)] == 'B')) \
                        and (state.board[(key[0] - 1, key[1] - 1)] == EM and
                             (state.board[(key[0] + 1, key[1] + 1)] == 'b' or
                              state.board[(key[0] + 1, key[1] + 1)] == 'B')):
                    piece_counts[value] += 1
                if (value == 'r' or value == 'R') and (state.board[(key[0] + 1, key[1] - 1)] == EM and
                                                       (state.board[(key[0] - 1, key[1] + 1)] == 'B')) \
                        and (state.board[(key[0] + 1, key[1] + 1)] == EM and
                             (state.board[(key[0] - 1, key[1] - 1)] == 'B')):
                    piece_counts[value] += 1
        return piece_counts

    def __repr__(self):
        return '{} {}'.format(abstract.AbstractPlayer.__repr__(self), 'better_h player')
