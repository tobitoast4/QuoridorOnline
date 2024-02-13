var server_url = null;
var current_lobby_id = null;
var next_lobby_id = null;
var this_player_id = null;
var this_player_name = null;
var complete_game_data = null;

var clear_last_error_msg_started = false;
var last_error_msg = null;

function throwOnError(json_obj) {
    // If there is the key "error" in a json_obj, show the value.
    // E.g.: {"error": "Player can not move here"} should show a notify and return true.
    // E.g.: {"status": "success"} should return false.
    if (Object.hasOwn(json_obj, "error")) {
        throw json_obj["error"];
    }
}

function showNewError(error) {
    // shows an error if it is not the same as last_error_msg
    // also sets an interval to reset last_error_msg back to null
    error = error.toString();
    if (last_error_msg != error) {
        last_error_msg = error;
        showNotify("error", "", error, 6);
    }
    if (!clear_last_error_msg_started) {  // ensures to only start one of these threads
        clear_last_error_msg_started = true;
        setTimeout(() => {
            last_error_msg = null;
            clear_last_error_msg_started = false;
        }, 5000);
    }
}


// ####################
// Methods for the game
// ####################

async function getGameDataAsync() {
    var data_to_be_returned = null;
    try {
        var response = await fetch(server_url + "get_game_data/" + current_lobby_id, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        data_to_be_returned = await response.json();
        throwOnError(data_to_be_returned);
    } catch (error) {
        showNewError(error);
    }

    return data_to_be_returned;
}

async function movePlayerAsync(player_id, new_field_col_num, new_field_row_num) {
    try {
        var response = await fetch(server_url + "game_move_player/" + current_lobby_id, {
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
        showNewError(error);
        updateGame(round_diff=1);  // when user views previous rounds and fails to move
    }
}

async function placeWallAsync(player_id, col_start, row_start, col_end, row_end) {
    try {
        var response = await fetch(server_url + "game_place_wall/" + current_lobby_id, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "user_id": player_id,
                "col_start" : col_start,
                "row_start" : row_start,
                "col_end" : col_end,
                "row_end" : row_end
            })
        });
        data = await response.json();
        throwOnError(data);
    } catch (error) {
        showNewError(error);
        updateGame(round_diff=1);  // when user views previous rounds and fails to place a wall
    }
}

async function createPlayers() {
    var game_data = await getGameDataAsync();
    var initial_setup_json = game_data["initial_setup"]; //TODO: Use the amount fields property??
    var players_json = initial_setup_json["players"];
    var colors = ["red", "blue", "green", "purple"];
    for (var p = 0; p < players_json.length; p++) {
        var player_json = players_json[p];
        var player = new Player(player_json["user"]["id"],
                                player_json["user"]["name"],
                                player_json["amount_walls_left"],
                                colors[p]);

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


    last_wall.wall = new Wall(getPlayerById(this_player_id));
    refreshPlayerStats();
}

async function updateGame(round_diff=0, play_audio=true) {
    // use round_diff=0 to not update the game if game_data did not change (this is usually called by the polling loop)
    // use round_diff=1 to actively load the current round
    // use round_diff=2 to actively load the last round
    // use round_diff=3 to actively load the round before last round
    // ......
    let new_complete_game_data = await getGameDataAsync();
    let fetched_game_data_is_new = JSON.stringify(new_complete_game_data) != JSON.stringify(complete_game_data);

    if (next_lobby_id == null){
        next_lobby_id = new_complete_game_data["next_lobby_id"];
    }
    if (fetched_game_data_is_new) {
        current_round_diff = 0;  // defined in game_online.js
    }
    if (fetched_game_data_is_new || round_diff != 0) {
        changePlayState(reset=true);
        if (play_audio) {
            playAudio();
        }
        complete_game_data = new_complete_game_data;
        game_data = complete_game_data["game"];

        if (round_diff <= 1) {
            round_diff = 1;
        }
        if (round_diff > game_data.length) {
            round_diff = game_data.length;
        }

        let current_game_data = game_data[game_data.length - round_diff];

        // update players
        let players_json = current_game_data.game_board.players;
        players_json.forEach(player_json => {
            let players_field = player_json["field"];
            if (players_field != null) {
                this.updatePlayer(player_json["user"]["id"],
                                  players_field,
                                  player_json["amount_walls_left"],
                                  player_json["move_options"]);
            }
        });

        // update walls
        let walls_json = current_game_data.game_board.walls;
        walls = [];  // remove all existing walls
        walls_json.forEach(wall_json => {
            let start = wall_json["start"];
            let end = wall_json["end"];
            placeWallByServerCoordinates(wall_json["player_id"], start["col"], start["row"], end["col"], end["row"]);
        });

        if (round_diff <= 1) {
            players_action_state = current_game_data["state"];
            its_this_players_turn = current_game_data["its_this_players_turn"];
            if (players_action_state == 2) {
                let last_players_turn = its_this_players_turn - 1;
                if (last_players_turn < 0) {
                    last_players_turn = players.length - 1;
                }
                last_player = players[last_players_turn];
                updatePlayerWonTheGame(last_player.name);
            } else {
                player = players[its_this_players_turn];
                updatePlayersTurnInstuction(player.name);
            }
        }
    }
}

function updatePlayer(player_id, players_field, amount_walls_left, move_options) {
    // get the correct player in the game
    for (var p = 0; p < players.length; p++) {
        var the_player = players[p];
        if (the_player.player_id == player_id) {
            // update amount_walls_left
            the_player.amount_walls_left = amount_walls_left;
            refreshPlayerStats();

            // update position
            let new_field = getFieldByColAndRow(players_field["col_num"], players_field["row_num"]);
            new_field.player = the_player;
            if (the_player.field != null) {
                the_player.field.player = null;
            }
            the_player.field = new_field;

            // update move_options
            let new_move_options = [];
            move_options.forEach(move_option => {
                let field = getFieldByColAndRow(move_option["col_num"], move_option["row_num"]);
                new_move_options.push(field);
            });
            the_player.move_option_fields = new_move_options;
            break;
        }
    }
}


// ####################
// Methods for in lobby
// ####################

async function startGameAsync() {
    try {
        var response = await fetch(server_url + "start_game/" + current_lobby_id, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "user_id": this_player_id,
                "user_name": this_player_name,
            })
        });
        var data = await response.json();
        throwOnError(data);
    } catch (error) {
        showNewError(error);
    }
}

async function changeVisibility() {
    try {
        var response = await fetch(server_url + "change_lobby_visibility/" + current_lobby_id, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        var data = await response.json();
        throwOnError(data);
        if (data.hasOwnProperty("status")) {
            showNotify("success", "", data["status"], 6);
        }
    } catch (error) {
        showNewError(error);
    }
}

async function changeAmountOfWallsPerPlayer(new_amount) {
    try {
        var response = await fetch(server_url + "change_amount_of_walls_per_player/" + current_lobby_id, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "new_amount": new_amount,
            })
        });
        var data = await response.json();
        throwOnError(data);
    } catch (error) {
        showNewError(error);
    }
}

async function getRandomPublicLobby() {
    try {
        var response = await fetch(server_url + "get_random_lobby", {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        var data = await response.json();
        throwOnError(data);
        if (data.hasOwnProperty("lobby_url")) {
            window.location.replace(data["lobby_url"]);
        }
    } catch (error) {
        showNewError(error);
    }
}

async function getLobbyAsync() {
    try {
        var response = await fetch(server_url + "get_lobby/" + current_lobby_id, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "user_id": this_player_id,
                "user_name": this_player_name,
            })
        });
        var data = await response.json();
        throwOnError(data);
        var status = response.status;
        if (status == 200) {
            if (data.hasOwnProperty("players") && data.hasOwnProperty("lobby_owner")
            && data.hasOwnProperty("is_private") && data.hasOwnProperty("amount_of_walls_per_player")) {
                var lobby_owner_id = data["lobby_owner"]["id"];
                var list_of_players = $('#list_of_players');
                list_of_players.empty();
                data.players.forEach(player => {
                    if (player.id == lobby_owner_id) {
                        list_of_players.append("<div style='display: inline-block; padding: 10px 0; word-wrap: anywhere;'>" + player.name +
                                               "<i class='fa fa-user-circle-o' aria-hidden='true' style='margin-left: 12px'></i>" +
                                               "</div>");
                    } else {
                        list_of_players.append("<div style='padding: 10px 0; word-wrap: anywhere;'>" + player.name + "</div>");
                    }
                });

                if (data["is_private"]) {
                    $("#change-lobby-visibility-button").html('<i class="fa fa-lock" aria-hidden="true"></i>');
                } else {
                    $("#change-lobby-visibility-button").html('<i class="fa fa-globe" aria-hidden="true"></i>');
                }

                // update amount_of_walls_per_player
                $('#current-amount-of-walls-per-player').html(data["amount_of_walls_per_player"]);
            } else if (data.hasOwnProperty("game")) {
                window.location.replace(data.game);
            }
        }
    } catch (error) {
        showNewError(error);
    }
}

async function updatePlayerName() {
    let new_player_name = $('#input-players-name').val();

    try {
        var response = await fetch(server_url + "rename_player", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "lobby_id": current_lobby_id,
                "user_id": this_player_id,
                "new_user_name": new_player_name
            })
        });
        var data = await response.json();
        throwOnError(data);
        showNotify("success", "", data["status"], 6);
    } catch (error) {
        showNewError(error);
    }
}

