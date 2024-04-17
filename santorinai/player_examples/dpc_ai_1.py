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

    def get_enemy_pawns(self, board, our_pawn):
        pawns = []
        for pawn in board.pawns:
            if pawn.player_number != our_pawn.player_number:
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
        dic_ind_eval_var = {}  # Dictionary of individual evaluation variables
        start = 0

        # Select available moves and builds
        for pawn in board.get_player_pawns(self.player_number):
            dic_plays[pawn.number] = board.get_possible_movement_and_building_positions(pawn)

            # Generate pay ids and map them to pawn and move/build coordinates
            for id, (move, build) in enumerate(dic_plays[pawn.number], start):
                dic_play_ids[id] = [pawn.number, move, build]

                # Copy board and play move
                board_2 = copy.deepcopy(board)
                board_2.play_move(pawn.number, move, build)

                # Compute evaluation variables
                dic_ind_eval_var["sum_height"] = self.get_pawns_added_heights(board_2)
                dic_play_eval[id] = dic_ind_eval_var

            start = id + 1

        # Generate plays evaluation matrix
        x=1


        return None, None


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