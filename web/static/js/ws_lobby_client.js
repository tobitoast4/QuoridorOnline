var gameClient = null;
var next_lobby_id = null;
var complete_game_data = null;
var current_round_diff = 0;

var clear_last_error_msg_started = false;
var last_error_msg = null;
var players_created = false;

function throwOnError(json_obj) {
    // If there is the key "error" in a json_obj, show the value.
    // E.g.: {"error": "Player can not move here"} should show a notify and return true.
    // E.g.: {"status": "success"} should return false.
    if (Object.hasOwn(json_obj, "error")) {
        if (json_obj["error"].startsWith("JSONDecodeError")) {
            console.log(json_obj["error"]);
        } else {
            throw json_obj["error"];
        }
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


async function movePlayerAsync(player_id, new_field_col_num, new_field_row_num) {
    gameClient.sendMove(player_id, new_field_col_num, new_field_row_num);
}

async function placeWallAsync(player_id, col_start, row_start, col_end, row_end) {
    gameClient.sendWall(player_id, col_start, row_start, col_end, row_end);
}

async function surrenderAsync() {
    gameClient.sendSurrender();
}

async function createPlayers() {
    // var complete_game_data = await getGameDataAsync();
    let game_data = complete_game_data["game"];
    var initial_setup_json = game_data["initial_setup"]; //TODO: Use the amount fields property??
    var players_json = initial_setup_json["players"];
    for (var p = 0; p < players_json.length; p++) {
        var player_json = players_json[p];
        var player = new Player(player_json.user.game_user.id,
                                player_json.user.game_user.username,
                                player_json.amount_walls_left,
                                player_json.user.color, 
                                player_json.user.has_surrendered);

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
    players_created = true;
}


// ####################
// Methods for in lobby
// ####################

async function startGameAsync() {
    try {
        var response = await fetch(server_url + "start_game/" + current_lobby_id, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie("csrftoken", ""),
                'Content-Type': 'application/json'
            }
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
                'X-CSRFToken': getCookie("csrftoken", ""),
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
                'X-CSRFToken': getCookie("csrftoken", ""),
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
                'X-CSRFToken': getCookie("csrftoken", ""),
                'Content-Type': 'application/json'
            }
        });
        var data = await response.json();
        throwOnError(data);
        if (data.hasOwnProperty("error")) {
            showNotify("error", "", data["error"], 6);
        }
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
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie("csrftoken", ""),
                'Content-Type': 'application/json'
            }
        });
        var data = await response.json();
        throwOnError(data);
        var status = response.status;
        if (status == 200) {
            if (data.lobby.game) {
                window.location.replace(server_url + data.lobby.game);
            } else {
                var lobby_owner_id = data.lobby.owner.game_user.id;
                var list_of_players = $('#list_of_players');
                list_of_players.empty();
                data.lobby.gameplayer_set.forEach(player => {
                    if (player.game_user.id == lobby_owner_id) {
                        list_of_players.append("<div style='display: flex; padding: 10px 0; word-wrap: anywhere;'>" +
                                                    "<div class='color-of-user-in-list' style='background-color: " + player.color + "'></div>" +
                                                    player.game_user.username +
                                                    "<i class='fa fa-user-circle-o' aria-hidden='true' style='margin-left: 12px'></i>" +
                                                "</div>");
                    } else {
                        list_of_players.append("<div style='display: flex; padding: 10px 0; word-wrap: anywhere;'>" +
                                                    "<div class='color-of-user-in-list' style='background-color: " + player.color + "'></div>" +
                                                    player.game_user.username +
                                               "</div>");
                    }
                });

                if (data.lobby.is_private) {
                    $("#change-lobby-visibility-button").html('<i class="fa fa-lock" aria-hidden="true"></i>');
                } else {
                    $("#change-lobby-visibility-button").html('<i class="fa fa-globe" aria-hidden="true"></i>');
                }

                // update amount_of_walls_per_player
                $('#current-amount-of-walls-per-player').html(data.lobby.amount_of_walls_per_player);
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
                'X-CSRFToken': getCookie("csrftoken", ""),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "new_user_name": new_player_name
            })
        });
        var data = await response.json();
        throwOnError(data);
        showNotify("success", "", data["status"], 6);
        $("#button_update_player_name").removeAttr("style");
        $("#button_update_player_name_icon").removeAttr("style");
    } catch (error) {
        showNewError(error);
    }
}

async function updateColor(new_color) {
    try {
        var response = await fetch(server_url + "change_color", {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie("csrftoken", ""),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "lobby_id": current_lobby_id,
                "new_color": new_color
            })
        });
        var data = await response.json();
        throwOnError(data);
        showNotify("success", "", data["status"], 6);
        $('#players-color').attr("style", "background-color: " + data["color"]);
    } catch (error) {
        showNewError(error);
    }
}


class GameWebSocketClient {
    constructor(lobbyId) {
        this.lobbyId = lobbyId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1500;

        // Event Callbacks
        this.handlers = {
            'connect': [],
            'disconnect': [],
            'game_move': [],
            'place_wall': [],
            'game_state': [],
            'chat_message': [],
            'player_connected': [],
            'error': [],
        };
    }

    connect() {
        // Protokoll automatisch wählen (wss:// für HTTPS, ws:// für HTTP)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}/ws/game/${this.lobbyId}/`;
        
        this.ws = new WebSocket(url);

        this.ws.onopen = () => this.onOpen();
        this.ws.onmessage = (event) => this.onMessage(event);
        this.ws.onerror = (error) => this.onError(error);
        this.ws.onclose = () => this.onClose();
    }

    onOpen() {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.emit('connect');
    }

    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            // Event Handler
            if (data.type && this.handlers[data.type]) {
                this.handlers[data.type].forEach(handler => handler(data));
            }
        } catch (error) {
            console.error('Error parsing message:', error);
            this.emit('error', { message: 'Invalid message from server' });
        }
    }

    onError(error) {
        console.error('WebSocket error:', error);
        this.emit('error', { message: 'Connection error' });
    }

    onClose() {
        console.log('WebSocket disconnected');
        this.emit('disconnect');
        
        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => this.connect(), this.reconnectDelay);
        } else {
            console.error('Maximum reconnect attempts exceeded');
            this.emit('error', { message: 'Could not connect to server' });
        }
    }

    sendMove(player_id, new_field_col_num, new_field_row_num) {
        this.send({
            type: 'game_move',
            message: {
                "user_id": player_id,
                "new_field_col_num": new_field_col_num,
                "new_field_row_num": new_field_row_num,
            },
        });
    }

    sendWall(player_id, col_start, row_start, col_end, row_end) {
        this.send({
            type: 'place_wall',
            message: {
                "user_id": player_id,
                "col_start" : col_start,
                "row_start" : row_start,
                "col_end" : col_end,
                "row_end" : row_end
            },
        });
    }

    sendSurrender() {
        this.send({
            type: 'surrender',
            message: {},
        });
    }

    // sendChatMessage(message) {
    //     this.send({
    //         type: 'chat_message',
    //         message: message,
    //     });
    // }

    requestGameState() {
        this.send({
            type: 'game_state_request',
        });
    }

    /** Generic message*/
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.error('WebSocket not connected');
            this.emit('error', { message: 'Not connected to server' });
        }
    }

    /**
     * Event-Handler registrieren
     */
    on(event, handler) {
        if (this.handlers[event]) {
            this.handlers[event].push(handler);
        }
    }

    /**
     * Event-Handler entfernen
     */
    off(event, handler) {
        if (this.handlers[event]) {
            this.handlers[event] = this.handlers[event].filter(h => h !== handler);
        }
    }

    /**
     * Event auslösen
     */
    emit(event, data = {}) {
        if (this.handlers[event]) {
            this.handlers[event].forEach(handler => handler(data));
        }
    }

    /**
     * Verbindung trennen
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}


gameClient = new GameWebSocketClient(current_lobby_id);
gameClient.connect();
gameClient.on('connect', () => {
    gameClient.requestGameState();  // get initial game state when connected
});

gameClient.on('game_state', (data) => {
    complete_game_data = data.message;
    if (!players_created) {
        createPlayers();
        next_lobby_id = complete_game_data.game.next_lobby_id;
    }
    updateGame(round_diff=0, play_audio=true, fetched_game_data_is_new=true);
});

gameClient.on('error', (data) => {
    showNotify("error", "", data.message, 6);
});
