import sys

from conf import settings
from web.quoridor.game import Game, STATE_PLACING_PLAYERS, STATE_PLAYER_DID_WIN
from web.quoridor.wall import Wall, is_wall_within_board
from web.errors import QuoridorOnlineGameError
from collections import deque
import copy, asyncio
import threading, random, time


class MoveSimulator:
    def __init__(self, lobby, game: Game, depth, wall_range):
        self.depth = depth
        self.wall_range = wall_range
        self.ai_player = game.get_current_player()
        if self.ai_player.amount_walls_left <= 0:
            self.depth = 1  # just follow the direct path to the win option fields, no need to calculate walls placement
        self.moves_before_wall = random.randint(3, 6)  # this many moves will be performed before placing a wall
        self.lobby = lobby
        self.game = game
        self.game_copies = dict()
        self.running_threads = []
        self.moves = []
        self.impossible_walls = []  # TODO: Only add in depth=self.depth (problem we need BFS for that...)
                                    # Currently walls that are possible are added here :((
                                    # This is especially a problem when self.depth is high, e.g. self.depth>=4

    def play(self):
        """Wrapper function for play_ai_player() that ensures that at least 0.5 
           seconds pass when executing play_ai_player(). 
        """
        start = time.monotonic()
        game = self.play_ai_player()  # actual method
        elapsed = time.monotonic() - start
        min_delay = random.uniform(0.5, 2.5)  # artificial delay to make the AI player look more human-like (and not too fast)
        if not settings.DEBUG and elapsed < min_delay:
            time.sleep(min_delay)
        return game

    def play_ai_player(self):
        if self.game.state == STATE_PLAYER_DID_WIN:
            return
        if self.game.state == STATE_PLACING_PLAYERS:
            move_options = self.ai_player.start_option_fields
            start_field = random.choice(move_options)
            self.game.move_player(self.ai_player.gameplayer.game_user.id, self.lobby, 
                                  start_field.col_num, start_field.row_num)
            return self.game
        else:
            print("")
            score = self._generate_moves(self.game, dictionary=self.game_copies, depth=self.depth, 
                                alpha=float("-inf"), beta=float("inf"),)
            games = [m for m in self.moves if m[1] == score]
            return random.choice(games)[0]

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

    def calculate_game_score(self, game: Game, depth):
        """Calculates the score of the game for the AI player. The higher the score, 
        the better the position of the AI player. 
        
            score = (10 * (sum_enemy_distance - own_distance) + 2 * (amount_own_walls - sum_amount_enemy_walls))
        """
        others_walls = 0
        others_distance = 0
        ai_player = self.get_ai_player(game)

        # calculate las field  # TODO: improve this, this is a hacky solution
        rounds = game.game_data["game"]
        last_real_round = rounds[len(rounds)-(self.depth-depth)-1]
        last_real_round_players = last_real_round["game_board"]["players"]
        last_field = [p["field"] for p in last_real_round_players if p["user"]["id"] == str(ai_player.gameplayer.id)][0]

        ai_player_walls = [w for w in game.game_board.walls if w.player_id == \
            str(ai_player.gameplayer.game_user.id)]
        ai_player_horizontal_walls = [w for w in ai_player_walls if w.is_horizontal()]
        wall_anchors = {a for w in game.game_board.walls for a in w.get_wall_anchors()}
        if ai_player.field in ai_player.win_option_fields:
            return float("inf")  # best score possible
        for player in self.get_not_ai_players(game):
            if player.field in player.win_option_fields:
                return float("-inf")  # worst score possible
            if not player.gameplayer.has_surrendered and player != ai_player:
                distance = game.shortest_distance(player)
                assert distance >= 0, "Distance should be non-negative"
                others_distance += distance
                others_walls += player.amount_walls_left
        score = (
            6 * (others_distance - game.shortest_distance(ai_player))
            + 4 * (ai_player.amount_walls_left - others_walls)
            + len(ai_player_horizontal_walls) 
            - 2 * len(wall_anchors)  # reward for placing walls in a way that they can be extended 
        )                        # (the less anchors the less lonely walls -> the better)
        if ai_player.field.col_num == last_field["col_num"] and ai_player.field.row_num == last_field["row_num"]:
            score -= 50  # Ai player should not return to same field
        return score
    
    def _generate_moves(self, game, dictionary, depth, alpha, beta):
        current_turn_player = game.get_current_player()  # its this players turn != self.ai_player
        if current_turn_player == self.ai_player:  # minimaxing
            kzl = "AI"
            maximizing = True
            best_score = float("-inf")
            func = max
        else:
            kzl = "G"
            maximizing = False
            best_score = float("inf")
            func = min

        score = self.calculate_game_score(game, depth)
        if depth <= 0 or score == float("inf") or score == float("-inf"):
            # if the score is +/- infinity, it means that the game is over and we can return the score directly
            dictionary["score"] = score
            return score
        
        if game.turn <= self.moves_before_wall or len(game.game_board.walls) >= 1:
            # Player movement moves
            for option in current_turn_player.getMoveOptions():
                key = str(f"{kzl}-M-({option.col_num}, {option.row_num})")
                new_game = copy.deepcopy(game)
                new_game.move_player(current_turn_player.gameplayer.game_user.id,   # only at the top level depth, the winner 
                                    self.lobby, option.col_num, option.row_num, depth==self.depth)  # should be set
                dictionary[key] = {}
                score = self._generate_moves(new_game, dictionary[key], depth-1, alpha, beta)
                if depth == self.depth:
                    print(f"{key}: {score}")
                    self.moves.append((new_game, score))
                best_score = func(best_score, score)
                if maximizing:
                    alpha = max(alpha, best_score)
                else:
                    beta = min(beta, best_score)
                if alpha >= beta:
                    break
        
        if game.turn > self.moves_before_wall or len(game.game_board.walls) >= 1 and current_turn_player.amount_walls_left <= 0:
            # Walls placement moves
            walls = self.get_walls_on_paths(game, game.get_other_players())
            # walls2 = self.get_walls_in_range(game.get_other_players()[0].field, self.wall_range)
            # walls = list(set(walls1) & set(walls2))
            for wall in walls:
                if wall in self.impossible_walls:
                    continue
                key = f"{kzl}-W-{str(wall)}"
                new_game = copy.deepcopy(game)
                col_start, row_start, col_end, row_end = wall
                try:  # if trying to place a wall does not throw an error, we know its a legal move
                    new_game.place_wall(current_turn_player.gameplayer.game_user.id, 
                                        col_start, row_start, col_end, row_end)
                    dictionary[key] = {}
                    score = self._generate_moves(new_game, dictionary[key], depth-1, alpha, beta)
                    if depth == self.depth:
                        print(f"{key}: {score}")
                        self.moves.append((new_game, score))
                    best_score = func(best_score, score)
                    if maximizing:
                        alpha = max(alpha, best_score)
                    else:
                        beta = min(beta, best_score)
                    if alpha >= beta:
                        break
                except QuoridorOnlineGameError as e:
                    self.impossible_walls.append(wall)
        return best_score

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
        # get all fields in range of the given manhatten distance
        fields_in_range = {field}
        for _ in range(distance):
            new_fields_in_range = list(fields_in_range)
            for field in fields_in_range:
                new_fields_in_range += field.neighbour_fields
            fields_in_range = set(new_fields_in_range)
        walls = []
        for field in fields_in_range:
            walls += self.get_walls_at_field(field)
        return list(set(walls))
    
    def get_walls_on_paths(self, game, players):
        walls = []
        for p in players:
            if p.gameplayer.has_surrendered:
                continue
            fields_of_path = game.fields_of_path_to_win(p.field, p.win_option_fields)
            for field in fields_of_path:
                walls += self.get_walls_at_field(field)
        return list(set(walls))

    def get_walls_at_field(self, field):
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
