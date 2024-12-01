import copy

import numpy as np
import pandas as pd
from santorinai.player import Player
from santorinai.board import Board
from santorinai.pawn import Pawn
from random import choice



class PlayerDPC1(Player):
    """

    :log_level: 0: no output, 1: Move choices
    """

    def __init__(self, player_number, log_level=0) -> None:
        super().__init__(player_number, log_level)

    def name(self):
        return "DaniPclos1!"

    def get_ally_pawn(self, board: Board, our_pawn: Pawn) -> Pawn | None:
        for pawn in board.pawns:
            if (
                    pawn.number != our_pawn.number
                    and pawn.player_number == our_pawn.player_number
            ):
                return pawn

    def get_rival_pawns(self, board, player_nb):
        pawns = []
        for pawn in board.pawns:
            if pawn.player_number != player_nb:
                pawns.append(pawn)
        return pawns

    def place_pawn(self, board: Board, pawn):
        ally_pawn = self.get_ally_pawn(board, pawn)

        available_positions = board.get_possible_movement_positions(pawn)
        if (
                ally_pawn is None
                or ally_pawn.pos[0] is None
                or ally_pawn.pos[1] is not None
        ):
            # First pawn to place
            return choice(available_positions)

        # Place second pawn next to the first one if possible
        for pos in available_positions:
            if board.is_position_adjacent(pos, ally_pawn.pos):
                return pos

        return choice(available_positions)

    def play_move(self, board, n_layers=2, n_branches=2):
        """
        Method that plays the best move from analyzing the n_branches
        best moves for n_layers-deep chain of moves, where each layer
        corresponds to rival+own move (OBS if n_layers=1 then no
        additional rival moves investigated)
        """
        # Initialize plays analysis placeholders
        l_ar_eval = [0. for _ in range(n_branches**(2 * n_layers - 1))]
        n_eval = len(l_ar_eval)
        ar_eval_tot = np.tile(l_ar_eval, (2 * n_layers - 1, 1))

        # Evaluate potential moves and select the n_branches most promising candidates
        l_opt_plays, ar_eval = self.play_move_iter(board, n_branches)

        # Integrate evaluation of outer plays
        ar_eval_exp = np.repeat(ar_eval, n_branches**2)

        # Generate initial plays evaluation dictionary that needs to be updated at the end of each turn n
        l_l_plays = [l_opt_plays]

        # Evaluate branches for
        for n in range(n_layers - 1):
            # Iterate through branches from previous turn
            for idx1, branch in enumerate(l_l_plays):
                # Get opponents play for each own play from the previous turn
                for play in branch:
                    board_2 = copy.deepcopy(board)
                    board_2.play_move(play["order"], play["move"], play["build"])
                    l_opt_plays_2, ar_eval_2 = self.play_move_iter(board_2, n_branches)

                    # Get own plays for each oppoenent play
                    for play_2 in l_opt_plays_2:
                        board_3 = copy.deepcopy(board_2)
                        board_3.play_move(play["order"], play_2["move"], play_2["build"])
                        l_opt_plays_3, ar_eval_3 = self.play_move_iter(board_3, n_branches)


        dic_opt_play = l_opt_plays[0]
        return dic_opt_play["order"], dic_opt_play["move"], dic_opt_play["build"]

    def play_move_iter(self, board, n_branches=2):
        """
        Method that returns the n_branches best plays. Method that is called
        iteratively to implement the MinMax search algorithm.
        """
        dic_play_ids = {}  # Dictionary to map play id's to plays (pawn, move, build)
        dic_play_eval = {}  # Dictionary to store plays evaluation variables
        start = 0
        id = -1  # -1 for edge case where first pawn has no plays id=-1 sets start=0 for second pawn, avoiding key error

        # Select available moves and builds
        for pawn in board.get_player_pawns(self.player_number):
            l_plays = board.get_possible_movement_and_building_positions(pawn)

            # Generate movement sets
            dic_moves_done = {}
            dic_builds_done = {}

            # Analyze movements
            for id, (move, build) in enumerate(l_plays):
                # Move analysis. If already analyzed, extract result
                if not f"{move}" in dic_moves_done.keys():
                    dic_param_move = {}  # Dictionary of moves evaluations
                    dic_param_move["sum_height"] = self.get_pawns_added_heights(board, pawn.number, move)
                    dic_param_move["max_dist_rivals"] = self.get_max_distance_to_rivals(board, pawn.number, move)
                    dic_param_move["max_dist_height_rivals"] = self.get_rivals_distance_height(board, pawn.number, move)
                    dic_param_move["victory_move"] = self.get_victory_move(board, move)
                    dic_moves_done[f"{move}"] = dic_param_move
                else:
                    dic_param_move = dic_moves_done[f"{move}"]

                # Build analysis
                if not f"{build}" in dic_builds_done.keys():
                    dic_param_build = {}
                    dic_param_build["avoid_rival_victory"] = self.get_avoid_rival_victory(board, build)
                    dic_param_build["avoid_giving_victory"] = self.avoid_giving_victory(board, build)
                    dic_builds_done[f"{build}"] = dic_param_build
                else:
                    dic_param_build = dic_builds_done[f"{build}"]

                dic_param_play = dic_param_move | dic_param_build
                dic_play_eval[id + start] = dic_param_play
                dic_play_ids[id + start] = {"order": pawn.order,
                                            "move": move,
                                            "build": build}
            start += id + 1

        # Generate plays evaluation matrix
        a_weights = np.ones(len(dic_param_play))
        df_eval = pd.DataFrame(dic_play_eval)
        try:
            ar_eval_comb = df_eval.mul(a_weights, axis=0).sum(axis=0).values
        except ValueError:
            pass

        ar_eval_comb_opt = np.sort(ar_eval_comb)[::-1][:n_branches]
        l_opt_plays = np.argsort(ar_eval_comb)[::-1][:n_branches].tolist()
        l_opt_plays = [dic_play_ids[play] for play in l_opt_plays]

        return l_opt_plays, ar_eval_comb_opt

    def get_pawns_added_heights(self, board: Board, pawn_number, move):
        """
        Method that returns the sum of the heights squared of own player pawns. Squared
        so higher heights score better e.g. 0,2 vs 1,1.
        Args:
            board:

        Returns:

        """
        sum_heights = 0
        for pawn_old in board.get_player_pawns(self.player_number):
            if pawn_old.number == pawn_number:
                sum_heights += board.board[move[0]][move[1]]**2
            else:
                sum_heights += board.board[pawn_old.pos[0]][pawn_old.pos[1]]**2
        return sum_heights

    def get_max_distance_to_rivals(self, board:Board, pawn_number, move):
        """
        Method that computes the maximum, minimum distance to adjacent enemy pawns.
        Args:
            board:

        Returns:

        """
        a_own_pawns = self.get_own_pawns_array(board)
        a_riv_pawns = self.get_rival_pawns_array(board)

        # Update position of own moving pawn
        if a_own_pawns[0,0] == pawn_number:
            a_own_pawns[1,0] = move[0]
            a_own_pawns[2,0] = move[1]
        elif a_own_pawns[0,1] == pawn_number:
            a_own_pawns[1,1] = move[0]
            a_own_pawns[2,1] = move[1]

        # Calculate distances between own pawn and others
        rival_pawn_1 = min(max(abs(a_riv_pawns[1:3, 0] - a_own_pawns[1:3, 0])),  # x, y distance to rival 1
                     max(abs(a_riv_pawns[1:3, 0] - a_own_pawns[1:3, 1])))

        rival_pawn_2 = min(max(abs(a_riv_pawns[1:3, 1] - a_own_pawns[1:3, 0])),  # x, y distance to rival 1
                     max(abs(a_riv_pawns[1:3, 1] - a_own_pawns[1:3, 1])))

        # Subtract maximum distance so higher values correspond to lower distances
        max_dist = 4 - max(rival_pawn_1, rival_pawn_2)
        return int(max_dist)

    def get_rivals_distance_height(self, board:Board, pawn_number, move):
        """
        Method that computes the weighted distance/height from rival pawns.
        Args:
            board:

        Returns:

        """
        a_board = np.array(board.board)
        a_own_pawns = self.get_own_pawns_array(board)
        a_riv_pawns = self.get_rival_pawns_array(board)

        # Update position of own moving pawn
        if a_own_pawns[0,0] == pawn_number:
            a_own_pawns[1,0] = move[0]
            a_own_pawns[2,0] = move[1]
        elif a_own_pawns[0,1] == pawn_number:
            a_own_pawns[1,1] = move[0]
            a_own_pawns[2,1] = move[1]

        # Calculate distances between own pawn and others
        rival_pawn_1 = min(max(abs(a_riv_pawns[1:3, 0] - a_own_pawns[1:3, 0])
                         * a_riv_pawns[3,0]),  # x, y distance to rival 1
                     max(abs(a_riv_pawns[1:3, 0] - a_own_pawns[1:3, 1])

                         * a_riv_pawns[3,0]))  # x, y distance to rival 2

        rival_pawn_2 = min(max(abs(a_riv_pawns[1:3, 1] - a_own_pawns[1:3, 0])
                         * a_riv_pawns[3,1]),  # x, y distance to rival 1
                     max(abs(a_riv_pawns[1:3, 1] - a_own_pawns[1:3, 1])
                         * a_riv_pawns[3,1]))  # x, y distance to rival 2

        # Subtract maximum distance so higher values correspond to lower distances
        max_dist = 10 - max(rival_pawn_1, rival_pawn_2)
        return int(max_dist)

    def get_avoid_rival_victory(self, board:Board, build):
        """
        That gives many points if avoiding rival's victory.
        Args:
            board:

        Returns:

        """
        a_riv_pawns = self.get_rival_pawns_array(board)
        height = board.board[build[0]][build[1]] + 1
        a_build = np.array(build)

        # Calculate distances between own pawn and others
        distance_rival_1 = max(abs(a_riv_pawns[1:3, 0] - a_build))  # x, y distance to rival 1
        height_riv_1 = a_riv_pawns[3,0]

        distance_rival_2 = max(abs(a_riv_pawns[1:3, 1] - a_build)) # x, y distance to rival 2
        height_riv_2 = a_riv_pawns[3, 1]

        # If both building cupule and having a rival at winning position, give high score
        if (height==4 and ((distance_rival_1==1 and height_riv_1==2) or (distance_rival_2==1 and height_riv_2==2))):
            return 100
        else:
            return 0

    def avoid_giving_victory(self, board:Board, build):
        """
        Avoid building on a rival's victory position.
        Args:
            board:

        Returns:

        """
        a_riv_pawns = self.get_rival_pawns_array(board)
        height = board.board[build[0]][build[1]] + 1
        a_build = np.array(build)

        # Calculate distances between own pawn and others
        distance_rival_1 = max(abs(a_riv_pawns[1:3, 0] - a_build))  # x, y distance to rival 1
        height_riv_1 = a_riv_pawns[3,0]

        distance_rival_2 = max(abs(a_riv_pawns[1:3, 1] - a_build)) # x, y distance to rival 2
        height_riv_2 = a_riv_pawns[3, 1]

        # If both building cupule and having a rival at winning position, give high score
        if (height==3 and ((distance_rival_1==1 and height_riv_1==2) or (distance_rival_2==1 and height_riv_2==2))):
            return -100
        else:
            return 0
    def get_victory_move(self, board:Board, move):
        """
        Gives the most points if it's a victory move.
        Args:
            board:

        Returns:

        """

        height = board.board[move[0]][move[1]]

        # If winning move give highest score
        if height==3:
            return 1000
        else:
            return 0

    def get_own_pawns_array(self, board:Board):
        """
        Generate array with positions and height for own pawns
        Args:
            board:

        Returns:

        """
        l_pawn_nb = []
        l_pos_x = []
        l_pos_y = []
        l_heights = []

        for pawn in board.get_player_pawns(self.player_number):
            l_pawn_nb.append(pawn.number)
            l_pos_x.append(pawn.pos[0])
            l_pos_y.append(pawn.pos[1])
            l_heights.append(board.board[pawn.pos[0]][pawn.pos[1]])
        a_own_pawns = np.array([l_pawn_nb, l_pos_x, l_pos_y, l_heights])
        return a_own_pawns

    def get_rival_pawns_array(self, board:Board):
        """
        Generate array with positions and height for rival pawns
        Args:
            board:

        Returns:

        """
        l_pawn_nb = []
        l_pos_x = []
        l_pos_y = []
        l_heights = []

        for pawn in self.get_rival_pawns(board, self.player_number):
            l_pawn_nb.append(pawn.number)
            l_pos_x.append(pawn.pos[0])
            l_pos_y.append(pawn.pos[1])
            l_heights.append(board.board[pawn.pos[0]][pawn.pos[1]])
        a_rival_pawns = np.array([l_pawn_nb, l_pos_x, l_pos_y, l_heights])
        return a_rival_pawns
