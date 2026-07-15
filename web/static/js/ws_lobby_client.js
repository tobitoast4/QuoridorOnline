var gameClient = null;
var next_lobby_id = null;
var complete_game_data = null;


// ####################
// Methods for in lobby
// ####################

async function startGameAsync() {
    gameClient.sendStartGame();
}

async function changeVisibility() {
    gameClient.changeVisibility();
}

async function changeAmountOfWallsPerPlayer(new_amount) {
    gameClient.changeAmountOfWallsPerPlayer(new_amount);
}

async function updatePlayerName() {
    let new_player_name = $('#input-players-name').val();
    gameClient.renamePlayer(new_player_name);
    $("#button_update_player_name").removeAttr("style");
    $("#button_update_player_name_icon").removeAttr("style");
}

async function updateColor(new_color) {
    gameClient.changeColor(new_color);
}


class LobbyWebSocketClient {
    constructor(lobbyId) {
        this.lobbyId = lobbyId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        this.reconnectDelay = 2000;

        // Event Callbacks
        this.handlers = {
            'connect': [],
            'disconnect': [],
            'lobby_state': [],
            'error': [],
        };
    }

    connect() {
        // Select protocol based on the current page's protocol (ws for http, wss for https)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}/ws/lobby/${this.lobbyId}/`;
        
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

    sendStartGame() {
        this.send({type: 'start_game', message: {}});
    }

    changeVisibility() {
        this.send({type: 'change_lobby_visibility', message: {}});
    }

    changeAmountOfWallsPerPlayer(new_amount) {
        this.send({type: 'change_amount_of_walls_per_player', message: { "new_amount": new_amount }});
    }

    renamePlayer(new_name) {
        this.send({type: 'rename_player', message: { "new_name": new_name }});
    }

    changeColor(new_color) {
        this.send({type: 'change_color', message: { "new_color": new_color }});
    }

    // sendChatMessage(message) {
    //     this.send({
    //         type: 'chat_message',
    //         message: message,
    //     });
    // }

    requestLobbyState() {
        this.send({
            type: 'lobby_state_request',
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


gameClient = new LobbyWebSocketClient(current_lobby_id);
gameClient.connect();
gameClient.on('connect', () => {
    gameClient.requestLobbyState();  // get initial lobby state when connected
});

window.addEventListener("beforeunload", () => {
    gameClient.disconnect();
});

gameClient.on('lobby_state', (data) => {
    lobby_data = data.message;

    if (lobby_data.game) {
        window.location.replace(window.location.origin + "/game/" + lobby_data.id);
    } else {
        var lobby_owner_id = null;
        if (lobby_data.owner && lobby_data.owner.game_user) {
            lobby_owner_id = lobby_data.owner.game_user.id;
        }
        var list_of_players = $('#list_of_players');
        list_of_players.empty();
        lobby_data.gameplayer_set.forEach(player => {
            if (player.game_user.id == this_player_id) {
                $('#players-color').css('background-color', player.color);
            }

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

        if (lobby_data.is_private) {
            $("#change-lobby-visibility-button").html('<i class="fa fa-lock" aria-hidden="true"></i>');
        } else {
            $("#change-lobby-visibility-button").html('<i class="fa fa-globe" aria-hidden="true"></i>');
        }

        // update amount_of_walls_per_player
        $('#current-amount-of-walls-per-player').html(lobby_data.amount_of_walls_per_player);
    }
});

gameClient.on('error', (data) => {
    showNotify("error", "", data.message, 6);
});
