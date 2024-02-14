from quoridor import game
from quoridor import player
import user


def create_game_from_json(json_dict):
    initial_setup = json_dict["initial_setup"]
    game_data = json_dict["game"]
    game_data_last_round = game_data[len(game_data)-1]

    new_game = game.Game([], 0, "", skip_user_check=True)  # we don't need to set users: [user.User],
                            # amount_walls: 0 here, as they will be overridden anyway afterwards
    new_game.state = game_data_last_round["state"]
    new_game.its_this_players_turn = game_data_last_round["its_this_players_turn"]
    new_game.turn = game_data_last_round["turn"]
    new_game.game_data = json_dict

    game_data_last_round_players = game_data_last_round["game_board"]["players"]
    new_players = []
    for player_dict in game_data_last_round_players:
        new_user = create_user_from_dict(player_dict["user"])
        amount_walls_left = player_dict["amount_walls_left"]
        new_player = player.Player(new_user, amount_walls_left)
        # get field and set player to field and field to player
        if player_dict["field"] is not None:
            new_player.field = new_game.game_board.getFieldByColAndRow(player_dict["field"]["col_num"],
                                                                       player_dict["field"]["row_num"])
            new_player.field.player = new_player
        # set start_option_fields and win_option_fields
        start_and_win_option_fields = get_start_and_win_option_fields_of_player(initial_setup, new_user,
                                                                                new_game.game_board)
        new_player.start_option_fields = start_and_win_option_fields["start_option_fields"]
        new_player.win_option_fields = start_and_win_option_fields["win_option_fields"]
        new_players.append(new_player)
    new_game.game_board.players = new_players

    game_data_last_round_walls = game_data_last_round["game_board"]["walls"]
    for wall_dict in game_data_last_round_walls:
        new_game.place_wall(wall_dict["player_id"], wall_dict["start"]["col"], wall_dict["start"]["row"],
                            wall_dict["end"]["col"], wall_dict["end"]["row"], skip_user_check=True)
    return new_game


def get_start_and_win_option_fields_of_player(initial_setup, new_user, game_board):
    initial_setup_players = initial_setup["players"]
    for p_dict in initial_setup_players:
        if p_dict["user"]["id"] == new_user.id:
            start_option_fields_dict = p_dict["start_option_fields"]
            win_option_fields_dict = p_dict["win_option_fields"]
            return {
                "start_option_fields": get_field_list_from_field_dict_list(start_option_fields_dict, game_board),
                "win_option_fields": get_field_list_from_field_dict_list(win_option_fields_dict, game_board)
            }


def get_field_list_from_field_dict_list(field_list, game_board):
    fields = []
    for field_dict in field_list:
        fields.append(game_board.getFieldByColAndRow(field_dict["col_num"], field_dict["row_num"]))
    return fields


def create_user_from_dict(json_dict):
    new_user = user.User()
    new_user.id = json_dict["id"]
    new_user.name = json_dict["name"]
    new_user.color = json_dict["color"]
    return new_user
