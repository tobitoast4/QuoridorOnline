import sys

from quoridor.game import Game
from quoridor.wall import Wall
from errors import QuoridorOnlineGameError
import copy
import threading


class MoveSimulator:
    def __init__(self, game: Game):
        self.game = game
        self.game_copies = dict()
        self.running_threads = []

    def start_generate_moves(self, depth=1):
        self._generate_moves(dictionary=self.game_copies, depth=depth)
        for my_thread in self.running_threads:
            my_thread.join()
        print("x")

    def _generate_moves(self, dictionary, depth):
        depth -= 1
        # calculate all horizontal walls
        for row_start in range(self.game.game_board.amount_fields-1):
            row_start += 0.5  # for the horizontal case, row_start and row_end is the same
            for col_start in range(self.game.game_board.amount_fields-1):
                new_game = copy.deepcopy(self.game)
                try:  # if trying to place a wall does not throw an error, we know its a legal move
                    # for the horizontal case, col_end is equal to col_start+1
                    Wall(None, col_start, row_start, col_start+1, row_start, new_game.game_board)
                    dictionary[new_game] = {}
                    if depth > 0:
                        new_thread = threading.Thread(
                            target=self._generate_moves,
                            args=(dictionary[new_game], depth)
                        )
                        self.running_threads.append(new_thread)
                        new_thread.start()
                except QuoridorOnlineGameError as e:
                    pass
        # calculate all vertical walls
        for col_start in range(self.game.game_board.amount_fields-1):
            col_start += 0.5  # for the horizontal case, row_start and row_end is the same
            for row_start in range(self.game.game_board.amount_fields-1):
                new_game = copy.deepcopy(self.game)
                try:  # if trying to place a wall does not throw an error, we know its a legal move
                    # for the horizontal case, col_end is equal to col_start+1
                    Wall(None, col_start, row_start, col_start, row_start+1, new_game.game_board)
                    dictionary[new_game] = {}
                    if depth > 0:
                        new_thread = threading.Thread(
                            target=self._generate_moves,
                            args=(dictionary[new_game], depth)
                        )
                        self.running_threads.append(new_thread)
                        new_thread.start()
                except QuoridorOnlineGameError as e:
                    pass
        print("done")

    def get_best_game(self):
        self._generate_moves2(self.game_copies)
        best_game_score = -sys.maxsize
        best_game = None
        for game in self.game_copies:
            if self.game_copies[game] > best_game_score:
                best_game_score = self.game_copies[game]
                best_game = game
        best_game.game_board.print_fields()
        return best_game

    def _generate_moves2(self, dictionary):
        # calculate all horizontal walls
        for row_start in range(self.game.game_board.amount_fields-1):
            row_start += 0.5  # for the horizontal case, row_start and row_end is the same
            for col_start in range(self.game.game_board.amount_fields-1):
                new_game = copy.deepcopy(self.game)
                try:  # if trying to place a wall does not throw an error, we know its a legal move
                    # for the horizontal case, col_end is equal to col_start+1
                    new_game.place_wall(self.game.get_current_player().user.id, col_start, row_start, col_start+1, row_start)
                    dictionary[new_game] = new_game.get_game_score()
                except QuoridorOnlineGameError as e:
                    pass
        # calculate all vertical walls
        for col_start in range(self.game.game_board.amount_fields-1):
            col_start += 0.5  # for the horizontal case, row_start and row_end is the same
            for row_start in range(self.game.game_board.amount_fields-1):
                new_game = copy.deepcopy(self.game)
                try:  # if trying to place a wall does not throw an error, we know its a legal move
                    # for the horizontal case, col_end is equal to col_start+1
                    new_game.place_wall(self.game.get_current_player().user.id, col_start, row_start, col_start, row_start+1)
                    dictionary[new_game] = new_game.get_game_score()
                except QuoridorOnlineGameError as e:
                    pass
        print("done")
