import sys

from web.quoridor.game import Game
from web.quoridor.wall import Wall, is_wall_within_board
from web.errors import QuoridorOnlineGameError
import copy
from collections import deque
import threading


class MoveSimulator:
    def __init__(self, game: Game, depth, wall_range):
        self.depth = depth
        self.wall_range = wall_range
        self.game = game
        self.ai_player = game.get_current_player()
        self.game_copies = dict()
        self.running_threads = []
        self.moves = []

    def start_generate_moves(self):
        score = self._generate_moves(self.game, dictionary=self.game_copies, depth=self.depth, 
                             alpha=float("-inf"), beta=float("inf"),)
        # for my_thread in self.running_threads:
        #     my_thread.join()
        print("x")
        games = [m for m in self.moves if m[1] == score]
        return games[0]

    def get_ai_player(self, game):
        for p in game.game_board.players:
            if str(p.gameplayer.id) == str(self.ai_player.gameplayer.id): 
                return p
            
    def get_not_ai_players(self, game):
        """Get other players that didnt surrender yet"""
        players = []
        for p in game.game_board.players:
            if str(p.gameplayer.id) != str(self.ai_player.gameplayer.id): 
                if not p.gameplayer.has_surrendered:
                    players.append(p)
        return players

    def calculate_game_score(self, game: Game):
        """Calculates the score of the game for the current player. The higher the score, 
        the better the position of the current player. 
        
            score = (10 * (sum_enemy_distance - own_distance) + 2 * (amount_own_walls - sum_amount_enemy_walls))
        """
        others_walls = 0
        others_distance = 0
        current_player = self.get_ai_player(game)
        for player in self.get_not_ai_players(game):
            if not player.gameplayer.has_surrendered and player != current_player:
                distance = game.shortest_distance(player)
                assert distance >= 0, "Distance should be non-negative"
                others_distance += distance
                others_walls += player.amount_walls_left
        score = (
            10 * (others_distance - game.shortest_distance(current_player))
            + 2 * (current_player.amount_walls_left - others_walls)
        )
        return score
    
    def _generate_moves(self, game, dictionary, depth, alpha, beta):
        current_turn_player = game.get_current_player()  # its this players turn != self.ai_player
        if current_turn_player == self.ai_player:  # minimaxing
            maximizing = True
            best_score = float("-inf")
            func = max
        else:
            maximizing = False
            best_score = float("inf")
            func = min

        if depth <= 0:
            score = self.calculate_game_score(game)
            dictionary["score"] = score
            return score
        
        # Player movement moves
        for option in current_turn_player.getMoveOptions():
            key = str(f"KI-M-({option.col_num}, {option.row_num})")
            new_game = copy.deepcopy(game)
            new_game.move_player(current_turn_player.gameplayer.game_user.id, 
                                 None, option.col_num, option.row_num)
            dictionary[key] = {}
            score = self._generate_moves(new_game, dictionary[key], depth-1, alpha, beta)
            if depth == self.depth:
                print(f"{key} - {score}")
                self.moves.append((new_game, score))
            best_score = func(best_score, score)
            if maximizing:
                alpha = max(alpha, best_score)
            else:
                beta = min(beta, best_score)
            if alpha >= beta:
                break

        # Walls placement moves
        walls = self.get_walls_in_range(game.get_other_players()[0].field, self.wall_range)  # TODO: all walls for all players
        for wall in walls:
            key = f"KI-W-{str(wall)}"
            new_game = copy.deepcopy(game)
            col_start, row_start, col_end, row_end = wall
            try:  # if trying to place a wall does not throw an error, we know its a legal move
                new_game.place_wall(current_turn_player.gameplayer.game_user.id, 
                                    col_start, row_start, col_end, row_end)
                dictionary[key] = {}
                score = self._generate_moves(new_game, dictionary[key], depth-1, alpha, beta)
                if depth == self.depth:
                    print(f"{key} - {score}")
                    self.moves.append((new_game, score))
                best_score = func(best_score, score)
                if maximizing:
                    alpha = max(alpha, best_score)
                else:
                    beta = min(beta, best_score)
                if alpha >= beta:
                    break
            except QuoridorOnlineGameError as e:
                pass  # wall can not be placed
        return best_score
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


    def get_walls_in_range(self, field, distance):
        def get_walls_at_field(field):
            col = field.col_num
            row = field.row_num
            walls = []

            candidate_walls = [
                # horizontal
                (col, row + 0.5, col + 1, row + 0.5),
                (col - 1, row + 0.5, col, row + 0.5),
                (col, row - 0.5, col + 1, row - 0.5),
                (col - 1, row - 0.5, col, row - 0.5),
                # vertical
                (col + 0.5, row, col + 0.5, row + 1),
                (col + 0.5, row - 1, col + 0.5, row),
                (col - 0.5, row, col - 0.5, row + 1),
                (col - 0.5, row - 1, col - 0.5, row),
            ]

            for wall_coords in candidate_walls:
                if is_wall_within_board(*wall_coords, self.game.game_board.amount_fields):
                    walls.append(wall_coords)
            return walls

        # get all fields in range of the given manhatten distance
        fields_in_range = {field}
        for _ in range(distance):
            new_fields_in_range = list(fields_in_range)
            for field in fields_in_range:
                new_fields_in_range += field.neighbour_fields
            fields_in_range = set(new_fields_in_range)
        walls = []
        for field in fields_in_range:
            walls += get_walls_at_field(field)
        return walls
