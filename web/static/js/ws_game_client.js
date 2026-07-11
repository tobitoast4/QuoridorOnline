var gameClient = null;
var next_lobby_id = null;
var complete_game_data = null;
var current_round_diff = 0;

var clear_last_error_msg_started = false;
var last_error_msg = null;
var players_created = false;




async function movePlayerAsync(player_id, new_field_col_num, new_field_row_num) {
    gameClient.sendMove(player_id, new_field_col_num, new_field_row_num);
}

async function placeWallAsync(player_id, col_start, row_start, col_end, row_end) {
    gameClient.sendWall(player_id, col_start, row_start, col_end, row_end);
}

async function surrenderAsync() {
    gameClient.sendSurrender();
}

async function calculateAiAsync() {
    try {
        const response = await fetch(window.location.origin + "/calculate_ai/", {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie("csrftoken", ""),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "lobby_id": current_lobby_id
            })
        });
        const data = await response.json();
        return data;
    } catch (error) {
        throw error;
    }
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

async function updateGame(round_diff=0, play_audio=true, fetched_game_data_is_new=true) {
    // use round_diff=0 to not update the game if game_data did not change (this is usually called by the polling loop)
    // use round_diff=1 to actively load the current round
    // use round_diff=2 to actively load the last round
    // use round_diff=3 to actively load the round before last round
    // ......
    let game_data = complete_game_data.game;
    let game = game_data.game;
    let next_lobby_id = game_data["next_lobby_id"];

    if (fetched_game_data_is_new) {
        current_round_diff = 0;  // defined in game_online.js
    }
    if (fetched_game_data_is_new || round_diff != 0) {
        changePlayState(reset=true);
        if (play_audio) {
            playAudio();
        }
        // complete_game_data = new_game_data;

        if (round_diff <= 1) {
            round_diff = 1;
        }
        if (round_diff > game.length) {
            round_diff = game.length;
        }

        let current_round = game[game.length - round_diff];

        // update players
        let players_json = current_round.game_board.players;
        players_json.forEach(player_json => {
            let players_field = player_json["field"];
            if (players_field == null) {
                if (player_json.user.has_surrendered) {
                    this.removePlayer(player_json.user.game_user.id, player_json.user);
                }
            } else {
                this.updatePlayer(player_json.user.game_user.id,
                                  players_field,
                                  player_json["amount_walls_left"],
                                  player_json["move_options"]);
            }
        });

        // update walls
        let walls_json = current_round.game_board.walls;
        walls = [];  // remove all existing walls
        walls_json.forEach(wall_json => {
            let start = wall_json["start"];
            let end = wall_json["end"];
            placeWallByServerCoordinates(wall_json["player_id"], start["col"], start["row"], end["col"], end["row"]);
        });

        if (round_diff <= 1) {
            players_action_state = current_round["state"];
            its_this_players_turn = current_round["its_this_players_turn"];
            if (complete_game_data.winner != null) {
                let winner = complete_game_data.winner;
                let colored_name = $(`
                    <span class="font-effect-outline" style="font-weight: 100; color: ${winner.color}">${winner.game_user.username}</span>
                `);
                updatePlayerWonTheGame(colored_name);
            } else {
                player = players[its_this_players_turn];
                updatePlayersTurnInstruction(player);
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

function removePlayer(player_id, player) {
    // get the correct player in the game
    for (var p = 0; p < players.length; p++) {
        var the_player = players[p];
        if (the_player.player_id == player_id && the_player.field != null) {
            the_player.field.player = null;
            the_player.field = null;
            let colored_name = `
                <span class="font-effect-outline" style="font-weight: 100; color: ${player.color}">${player.game_user.username}</span>
            `;
            showNotify("info", "", colored_name + " has surrendered", 6);
            break;
        }
    }
}



class GameWebSocketClient {
    constructor(lobbyId) {
        this.lobbyId = lobbyId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        this.reconnectDelay = 2000;

        // Event Callbacks
        this.handlers = {
            'connect': [],
            'player_connected': [],
            'player_disconnected': [],
            'game_state': [],
            'online_state': [],
            'error': [],
        };
    }

    connect() {
        // Select protocol based on the current page's protocol (ws for http, wss for https)
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
    }

    onClose() {
        this.emit('disconnect');
        
        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                showNotify("error", "", `Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`, 10);
                setTimeout(() => this.connect(), this.reconnectDelay);
            }, 2 * this.reconnectDelay);  // initial delay before showing the notification and attempting to reconnect
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

    requestOnlineState() {
        this.send({
            type: 'online_state_request',
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
    gameClient.requestOnlineState();  // check which of the players are online
});

gameClient.on('game_state', (data) => {
    complete_game_data = data.message;
    if (!players_created) {
        createPlayers();
        next_lobby_id = complete_game_data.game.next_lobby_id;
    }
    updateGame(round_diff=0, play_audio=true, fetched_game_data_is_new=true);
});

gameClient.on('online_state', (data) => {
    online_user_ids = data.message;
    online_user_ids.forEach(user_id => {
        updatePlayerOnlineStatus(user_id, true);
    });
});

gameClient.on('player_connected', (data) => {
    updatePlayerOnlineStatus(data.user_id, true);
});

gameClient.on('player_disconnected', (data) => {
    updatePlayerOnlineStatus(data.user_id, false);
});

gameClient.on('error', (data) => {
    showNotify("error", "", data.message, 6);
});
