from collections import defaultdict

import abstract
import players.simple_player
from utils import MiniMaxWithAlphaBetaPruning, INFINITY, run_with_limited_time, ExceededTimeError
import time
from checkers.consts import EM, PAWN_COLOR, KING_COLOR, OPPONENT_COLOR, MAX_TURNS_NO_JUMP

PAWN_WEIGHT = 1
KING_WEIGHT = 1.5
LAST_ROW_PAWN = 0.8
CENTER_BOARD_PAWN = 0.5
MIDDLE_ROW_PAWN = 0.1
VULNERABLE_PAWN = -0.6
PROTECTED_PAWN = 0.6


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

    """
              Choose the best next move for the player and set the time to
              choose the next best move according to different criteria.

              Arguments:
              game_state: current game state which include board state, palyer color and number of turns since last jump.
              possible_moves: empty dictionary.

              :return: the best next move
       """

    def get_move(self, game_state, possible_moves):
        self.clock = time.process_time()
        self.time_for_current_move = self.time_for_state(game_state)
        if len(possible_moves) == 1:
            if self.turns_remaining_in_round == 1:
                self.turns_remaining_in_round = self.k
                self.time_remaining_in_round = self.time_per_k_turns
            else:
                self.turns_remaining_in_round -= 1
                self.time_remaining_in_round -= (time.process_time() - self.clock)
            return possible_moves[0]

        current_depth = 1
        prev_alpha = -INFINITY

        # Choosing an arbitrary move in case Minimax does not return an answer:
        best_move = possible_moves[0]

        # Initialize Minimax algorithm, still not running anything
        minimax = MiniMaxWithAlphaBetaPruning(self.utility, self.color, self.no_more_time,
                                              self.selective_deepening_criterion)

        # We will return the move that yields the most jumps and we will not
        # perform a minmax search, thus saving search time.
        max_jump = 0
        jump_move = None
        for move in possible_moves:
            if len(move.jumped_locs) > max_jump:
                jump_move = move
                max_jump = len(move.jumped_locs)
        if max_jump > 0:
            best_move = jump_move
            if self.turns_remaining_in_round == 1:
                self.turns_remaining_in_round = self.k
                self.time_remaining_in_round = self.time_per_k_turns
            else:
                self.turns_remaining_in_round -= 1
                self.time_remaining_in_round -= (time.process_time() - self.clock)
            return best_move

        # Iterative deepening until the time runs out.
        while True:
            print('going to depth: {}, remaining time: {}, prev_alpha: {}, best_move: {}'.format(
                current_depth,
                self.time_for_current_move - (time.process_time() - self.clock),
                prev_alpha,
                best_move))

            try:
                (alpha, move), run_time = run_with_limited_time(
                    minimax.search, (game_state, current_depth, -INFINITY, INFINITY, True), {},
                    self.time_for_current_move - (time.process_time() - self.clock))
            except (ExceededTimeError, MemoryError):
                print('no more time, achieved depth {}'.format(current_depth))
                break

            if self.no_more_time():
                print('no more time')
                break

            prev_alpha = alpha
            best_move = move

            if alpha == INFINITY:
                print('the move: {} will guarantee victory.'.format(best_move))
                break

            if alpha == -INFINITY:
                print('all is lost')
                break

            current_depth += 1

        if self.turns_remaining_in_round == 1:
            self.turns_remaining_in_round = self.k
            self.time_remaining_in_round = self.time_per_k_turns
        else:
            self.turns_remaining_in_round -= 1
            self.time_remaining_in_round -= (time.process_time() - self.clock)
        return best_move

    """
            Calculating the time for choosing the next move.
            The motivation behind the method is to invest in critical situations where player
            can be attacked and in situations where the player can attack the opponent.

            Arguments:
            game_state: current game state which include board state, palyer color and number of turns since last jump.

            :return: time to choose the next move.
    """

    def time_for_state(self, game_state):
        if self.turns_remaining_in_round == 1:
            return self.time_remaining_in_round
        avg_time_for_turn = self.time_remaining_in_round / self.turns_remaining_in_round - 0.05
        center = self.center_pieces(game_state, piece_counts=defaultdict(lambda: 0))
        if self.color == 'r':
            rescued_red = self.can_be_rescued_red(game_state, piece_counts=defaultdict(lambda: 0))
            rescued_pieces = sum(rescued_red.values())
            if rescued_pieces >= 1:
                """
                A situation in the board where there is at least one red player that will be attacked
                and the he has escape route.
                In this situation a maximum time is given which is 180% of the average time for action.
                """
                return 1.8 * avg_time_for_turn
            vulnerable_red = self.vulnerable_red_pawn(game_state, piece_counts=defaultdict(lambda: 0))
            vulnerable_pieces = sum(vulnerable_red.values())
            if vulnerable_pieces >= 1:
                """
                A situation where in the next turn the black opponent will jump over red player
                and in such a situation extra time is given in order to maximize future actions.
                The time given is 150% of the average time for action.
                """
                return 1.5 * avg_time_for_turn
            if center['r'] + center['R'] >= 2:
                """
                A situation in which there are at least two red player in the center of the board.
                Control of the center of the board is an advantage of maneuvering and attacking
                so more time is given in such a situation.
                The time given is 130% of the average time for action. 
                """
                return 1.3 * avg_time_for_turn
        else:
            rescued_black = self.can_be_rescued_black(game_state, piece_counts=defaultdict(lambda: 0))
            rescued_pieces = sum(rescued_black.values())
            if rescued_pieces >= 1:
                """
                A situation in the board where there is at least one black player that will be attacked
                and the he has escape route.
                In this situation a maximum time is given which is 180% of the average time for action.
                """
                return 1.8 * avg_time_for_turn
            vulnerable_black = self.vulnerable_black_pawn(game_state, piece_counts=defaultdict(lambda: 0))
            vulnerable_pieces = sum(vulnerable_black.values())
            if vulnerable_pieces > 1:
                """
                A situation where in the next turn the red opponent will jump over black player
                and in such a situation extra time is given in order to maximize future actions.
                The time given is 150% of the average time for action.
                """
                return 1.5 * avg_time_for_turn
            if center['b'] + center['B'] >= 2:
                """
                A situation in which there are at least two black player in the center of the board.
                Control of the center of the board is an advantage of maneuvering and attacking
                so more time is given in such a situation.
                The time given is 130% of the average time for action.
                """
                return 1.3 * avg_time_for_turn

        return self.time_remaining_in_round / self.turns_remaining_in_round - 0.05

    """
            Count the amount of pawn and kings in board center.
            Board center is between lines 3 and 4 and between columns 2 and 5.

            Arguments:
            state: current game state which include board state, palyer color and number of turns since last jump.
            piece_counts: empty dictionary.
            :return: dictionary where the key is the player type and the value is the amount of them in board center.
    """

    def center_pieces(self, state, piece_counts):
        for key, value in state.board.items():
            if value != EM and (key[0] == 3 or key[0] == 4) and (2 <= key[1] <= 5):
                piece_counts[value] += 1
        return piece_counts

    """
           Count the amount of black pawn and kings in board that can be rescued.
           Can be rescued is a state where the black player cam make a move to be rescued
           from the red opponent that may jump on him in his turn.

           Arguments:
           state: current game state which include board state, palyer color and number of turns since last jump.
           piece_counts: empty dictionary.
           :return: dictionary where the key is the player type and the value is the amount of them that can be rescued.
           """

    def can_be_rescued_black(self, state, piece_counts):
        for key, value in state.board.items():
            if value != EM and 0 < key[0] < 7 and 0 < key[1] < 7:
                if (value == 'b' or value == 'B') and (bool(state.board[(key[0] + 1, key[1] - 1)] == EM and
                                                            (state.board[(key[0] - 1, key[1] + 1)] == 'r' or
                                                             state.board[(key[0] - 1, key[1] + 1)] == 'R'))
                                                       ^ bool(state.board[(key[0] + 1, key[1] + 1)] == EM and
                                                              (state.board[(key[0] - 1, key[1] - 1)] == 'r' or
                                                               state.board[(key[0] - 1, key[1] - 1)] == 'R'))):
                    piece_counts[value] += 1
                if (value == 'b' or value == 'B') and (bool(state.board[(key[0] - 1, key[1] + 1)] == EM and
                                                            (state.board[(key[0] + 1, key[1] - 1)] == 'R'))
                                                       ^ (bool(state.board[(key[0] - 1, key[1] - 1)] == EM and
                                                               (state.board[(key[0] + 1, key[1] + 1)] == 'R')))):
                    piece_counts[value] += 1
        return piece_counts

    """
            Count the amount of red pawn and kings in board that can be rescued.
            Can be rescued is a state where the red player cam make a move to be rescued
            from the black opponent that may jump on him in his turn.

            Arguments:
            state: current game state which include board state, palyer color and number of turns since last jump.
            piece_counts: empty dictionary.
            :return: dictionary where the key is the player type and the value is the amount of them that can be rescued.
    """

    def can_be_rescued_red(self, state, piece_counts):
        for key, value in state.board.items():
            if value != EM and 0 < key[0] < 7 and 0 < key[1] < 7:
                if (value == 'r' or value == 'R') and (bool(state.board[(key[0] - 1, key[1] + 1)] == EM and
                                                            (state.board[(key[0] + 1, key[1] - 1)] == 'b' or
                                                             state.board[(key[0] + 1, key[1] - 1)] == 'B'))
                                                       ^ (bool(state.board[(key[0] - 1, key[1] - 1)] == EM and
                                                               (state.board[(key[0] + 1, key[1] + 1)] == 'b' or
                                                                state.board[(key[0] + 1, key[1] + 1)] == 'B')))):
                    piece_counts[value] += 1
                if (value == 'r' or value == 'R') and (bool(state.board[(key[0] + 1, key[1] - 1)] == EM and
                                                            (state.board[(key[0] - 1, key[1] + 1)] == 'B'))
                                                       ^ (bool(state.board[(key[0] + 1, key[1] + 1)] == EM and
                                                               (state.board[(key[0] - 1, key[1] - 1)] == 'B')))):
                    piece_counts[value] += 1
        return piece_counts

    """
            Count the amount of black pawn and kings in board that are vulnerable.
            Vulnerable palyer is a palyer that can't save himself and the red opponent will jump on him in his next move. 

            Arguments:
            state: current game state which include board state, palyer color and number of turns since last jump.
            piece_counts: empty dictionary.
            :return: dictionary where the key is the player type and the value is the amount of them that are vulnerable.
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
            Count the amount of red pawn and kings in board that are vulnerable.
            Vulnerable palyer is a palyer that can't save himself and the black opponent will jump on him in his next move. 

            Arguments:
            state: current game state which include board state, palyer color and number of turns since last jump.
            piece_counts: empty dictionary.
            :return: dictionary where the key is the player type and the value is the amount of them that are vulnerable.
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
        return '{} {}'.format(abstract.AbstractPlayer.__repr__(self), 'improved_better_h player')



