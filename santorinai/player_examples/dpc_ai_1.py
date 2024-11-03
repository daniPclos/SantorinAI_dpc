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

    def get_winning_moves(self, board: Board, pawn):
        available_positions = board.get_possible_movement_positions(pawn)
        winning_moves = []
        for pos in available_positions:
            if board.board[pos[0]][pos[1]] == 3:
                winning_moves.append(pos)

        return winning_moves

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

    def play_move(self, board):
        dic_plays = {}  # Dictionary to store move/build plays
        dic_play_ids = {}  # Dictionary to map play id's to plays (pawn, move, build)
        dic_play_eval = {}  # Dictionary to store plays evaluation variables
        start = 0
        id = -1  # -1 for edge case where first pawn has no plays id=-1 sets start=0 for second pawn, avoiding key error

        # Select available moves and builds
        for pawn in board.get_player_pawns(self.player_number):
            dic_plays[pawn.number] = board.get_possible_movement_and_building_positions(pawn)

            # Generate play ids and map them to pawn and move/build coordinates
            for id, (move, build) in enumerate(dic_plays[pawn.number], start):
                dic_play_ids[id] = [pawn.number, move, build]

                # Copy board and play move
                board_2 = copy.deepcopy(board)
                status, reason = board_2.play_move(pawn.order, move, build)
                board_2.player_turn = board.player_turn  # Correct turn increase in play_move

                # Compute evaluation variables
                dic_ind_eval_var = {}  # Dictionary of individual evaluation variables
                dic_ind_eval_var["sum_height"] = self.get_pawns_added_heights(board_2)
                dic_ind_eval_var["max_dist_rivals"] = self.get_max_distance_to_rivals(board_2)
                dic_ind_eval_var["max_dist_height_rivals"] = self.get_rivals_distance_height(board_2)
                dic_play_eval[id] = dic_ind_eval_var

            start = id + 1

        # Generate plays evaluation matrix
        a_weights = np.ones(len(dic_ind_eval_var))
        df_eval = pd.DataFrame(dic_play_eval)
        ar_eval_comb = df_eval.mul(a_weights, axis=0).sum(axis=0).values
        opt_play = np.argsort(ar_eval_comb)[::-1][0]
        l_opt_play = dic_play_ids[opt_play]

        pawn_order = board.pawns[l_opt_play[0] - 1].order
        return pawn_order, l_opt_play[1], l_opt_play[2]


    def get_pawns_added_heights(self, board: Board):
        """
        Method that returns the sum of the heights of own player pawns
        Args:
            board:

        Returns:

        """
        sum_heights = 0
        for pawn in board.get_player_pawns(self.player_number):
            sum_heights += board.board[pawn.pos[0]][pawn.pos[1]]
        return sum_heights

    def get_max_distance_to_rivals(self, board:Board):
        """
        Method that computes the maximum, minimum distance to adjacent enemy pawns.
        Args:
            board:

        Returns:

        """
        a_board = np.array(board.board)
        a_own_pawns = self.get_own_pawns_array(board)
        a_riv_pawns = self.get_rival_pawns_array(board)

        # Calculate distances between own pawn and others
        pawn_1 = max(max(abs(a_riv_pawns[1:3, 0] - a_own_pawns[1:3, 0])),  # x, y distance to rival 1
                     max(abs(a_riv_pawns[1:3, 1] - a_own_pawns[1:3, 0])))  # x, y distance to rival 2

        pawn_2 = max(max(abs(a_riv_pawns[1:3, 0] - a_own_pawns[1:3, 1])),  # x, y distance to rival 1
                     max(abs(a_riv_pawns[1:3, 1] - a_own_pawns[1:3, 1])))  # x, y distance to rival 2

        # Subtract maximum distance so higher values correspond to lower distances
        max_dist = 4 - min(pawn_1, pawn_2)
        return int(max_dist)

    def get_rivals_distance_height(self, board:Board):
        """
        Method that computes the weighted distance/height from rival pawns.
        Args:
            board:

        Returns:

        """
        a_board = np.array(board.board)
        a_own_pawns = self.get_own_pawns_array(board)
        a_riv_pawns = self.get_rival_pawns_array(board)

        # Calculate distances between own pawn and others
        pawn_1 = min(max(abs(a_riv_pawns[1:3, 0] - a_own_pawns[1:3, 0])
                         * a_riv_pawns[3,0]),  # x, y distance to rival 1
                     max(abs(a_riv_pawns[1:3, 0] - a_own_pawns[1:3, 1])

                         * a_riv_pawns[3,0]))  # x, y distance to rival 2

        pawn_2 = min(max(abs(a_riv_pawns[1:3, 1] - a_own_pawns[1:3, 0])
                         * a_riv_pawns[3,1]),  # x, y distance to rival 1
                     max(abs(a_riv_pawns[1:3, 1] - a_own_pawns[1:3, 1])
                         * a_riv_pawns[3,1]))  # x, y distance to rival 2

        # Subtract maximum distance so higher values correspond to lower distances
        max_dist = 10 - min(pawn_1, pawn_2)
        return int(max_dist)

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

