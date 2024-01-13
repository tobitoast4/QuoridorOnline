var current_lobby_id = null;
var this_player_id = null;
var game_data = null;

var last_error_msg = null;

function throwOnError(json_obj) {
    // If there is the key "error" in a json_obj, show the value.
    // E.g.: {"error": "Player can not move here"} should show a notify and return true.
    // E.g.: {"status": "success"} should return false.
    if (Object.hasOwn(json_obj, "error")) {
        throw json_obj["error"];
    }
}

async function getGameDataAsync() {
    var data_to_be_returned = null;
    try {
        var response = await fetch("http://127.0.0.1:5009/get_game_data/" + current_lobby_id, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        data_to_be_returned = await response.json();
        throwOnError(data_to_be_returned);
        console.log(data_to_be_returned)
    } catch (error) {
        error = error.toString();
        if (last_error_msg != error) {
            last_error_msg = error;
            showNotify("error", "", error, 6);
        }
    }

    return data_to_be_returned;
}

async function movePlayerAsync(player_id, new_field_col_num, new_field_row_num) {
    try {
        var response = await fetch("http://127.0.0.1:5009/game_move_player/" + current_lobby_id, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "user_id": player_id,
                "new_field_col_num": new_field_col_num,
                "new_field_row_num": new_field_row_num,
            })
        });
        data = await response.json();
        throwOnError(data);
    } catch (error) {
        showNotify("error", "", error, 6);
    }
}

async function createPlayers() {
    var game_data = await getGameDataAsync();
    var initial_setup_json = game_data["initial_setup"]; //TODO: Use the amount fields property??
    var players_json = initial_setup_json["players"];
    var colors = ["red", "blue", "green", "black"];
    for (var p = 0; p < players_json.length; p++) {
        var player_json = players_json[p];
        var player = new Player(player_json["user"]["id"], player_json["user"]["name"], colors[p]);

        // Add start_ and win_option_fields
        for (var i = 0; i < player_json["start_option_fields"].length; i++) {
            var col_num = player_json["start_option_fields"][i]["col_num"];
            var row_num = player_json["start_option_fields"][i]["row_num"];
            var field = getFieldByColAndRow(col_num, row_num);
            player.start_option_fields.push(field);
        }
        for (var i = 0; i < player_json["win_option_fields"].length; i++) {
            var col_num = player_json["win_option_fields"][i]["col_num"];
            var row_num = player_json["win_option_fields"][i]["row_num"];
            var field = getFieldByColAndRow(col_num, row_num);
            player.win_option_fields.push(field);
        }

        players.push(player);  // players is defined in game.js
    }

    refreshPlayerStats();
}

async function updatePlayers() {
    let new_game_data = await getGameDataAsync();
    if (JSON.stringify(new_game_data) != JSON.stringify(game_data)) {
        console.log(new_game_data);
        game_data = new_game_data;
        let current_game_round = game_data.game;
        let players_json = current_game_round.game_board.players;

        players_json.forEach(player_json => {
            let players_field = player_json["field"];
            if (players_field != null) {
                this.updatePlayerPosition(player_json["user"]["id"], players_field["col_num"], players_field["row_num"]);
            }
        });

        players_action_state = current_game_round["state"];
        if (players_action_state == 2) {
            updatePlayerWonTheGame(player.name);
        } else {
            its_this_players_turn = current_game_round["its_this_players_turn"];
            player = players[its_this_players_turn];
            updatePlayersTurnInstuction(player.name);
        }
    }
}

function updatePlayerPosition(player_id, col_num, row_num) {
    // get the correct player in the game
    for (var p = 0; p < players.length; p++) {
        var the_player = players[p];
        if (the_player.player_id == player_id) {
            let new_field = getFieldByColAndRow(col_num, row_num);
            new_field.player = the_player;
            if (the_player.field != null) {
                the_player.field.player = null;
            }
            the_player.field = new_field;
            break;
        }
    }
}


