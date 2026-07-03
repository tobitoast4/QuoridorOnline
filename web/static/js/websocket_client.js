/**
 * WebSocket Game Client
 * Verbindung zu WebSocket-Server für Echtzeit-Spielkommunikation
 */

class GameWebSocketClient {
    constructor(lobbyId) {
        this.lobbyId = lobbyId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        
        // Event Callbacks
        this.handlers = {
            'connect': [],
            'disconnect': [],
            'game_move': [],
            'place_wall': [],
            'chat_message': [],
            'player_connected': [],
            'error': [],
        };
    }

    /**
     * Verbindung zum WebSocket herstellen
     */
    connect() {
        // Protokoll automatisch wählen (wss:// für HTTPS, ws:// für HTTP)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}/ws/game/${this.lobbyId}/`;
        
        console.log(`WebSocket verbindet mit: ${url}`);
        this.ws = new WebSocket(url);

        this.ws.onopen = () => this.onOpen();
        this.ws.onmessage = (event) => this.onMessage(event);
        this.ws.onerror = (error) => this.onError(error);
        this.ws.onclose = () => this.onClose();
    }

    /**
     * Verbindung geöffnet
     */
    onOpen() {
        console.log('WebSocket verbunden');
        this.reconnectAttempts = 0;
        this.emit('connect');
    }

    /**
     * Nachricht vom Server empfangen
     */
    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('Nachricht empfangen:', data);
            
            // Event-Handler aufrufen
            if (data.type && this.handlers[data.type]) {
                this.handlers[data.type].forEach(handler => handler(data));
            }
        } catch (error) {
            console.error('Fehler beim Parsen der Nachricht:', error);
            this.emit('error', { message: 'Ungültige Nachricht vom Server' });
        }
    }

    /**
     * Fehler beim WebSocket
     */
    onError(error) {
        console.error('WebSocket Fehler:', error);
        this.emit('error', { message: 'Verbindungsfehler' });
    }

    /**
     * Verbindung geschlossen
     */
    onClose() {
        console.log('WebSocket getrennt');
        this.emit('disconnect');
        
        // Versuche neu zu verbinden
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Versuche erneut zu verbinden... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => this.connect(), this.reconnectDelay);
        } else {
            console.error('Maximale Reconnect-Versuche überschritten');
            this.emit('error', { message: 'Konnte sich nicht mit dem Server verbinden' });
        }
    }

    /**
     * Spielbewegung senden
     */
    sendMove(move) {
        this.send({
            type: 'game_move',
            move: move,
        });
    }

    /**
     * Wand platzieren
     */
    sendWall(wall) {
        this.send({
            type: 'place_wall',
            wall: wall,
        });
    }

    /**
     * Chat-Nachricht senden
     */
    sendChatMessage(message) {
        this.send({
            type: 'chat_message',
            message: message,
        });
    }

    /**
     * Spielstatus anfordern
     */
    requestGameState() {
        this.send({
            type: 'game_state_request',
        });
    }

    /**
     * Generische Nachricht senden
     */
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.error('WebSocket nicht verbunden');
            this.emit('error', { message: 'Nicht mit Server verbunden' });
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


// Beispiel-Verwendung:
/*
// WebSocket initialisieren
const lobbyId = 'YOUR_LOBBY_ID'; // Aus URL oder context
const gameClient = new GameWebSocketClient(lobbyId);

// Event-Listener registrieren
gameClient.on('connect', () => {
    console.log('Mit Spiel verbunden');
});

gameClient.on('game_move', (data) => {
    console.log('Spieler hat sich bewegt:', data.user_id, data.move);
    // UI aktualisieren
});

gameClient.on('place_wall', (data) => {
    console.log('Wand platziert:', data.user_id, data.wall);
});

gameClient.on('chat_message', (data) => {
    console.log(`${data.username}: ${data.message}`);
    // Chat-Nachricht anzeigen
});

gameClient.on('player_connected', (data) => {
    console.log(`${data.username} ist beigetreten`);
});

gameClient.on('error', (data) => {
    console.error('Fehler:', data.message);
});

// Verbindung herstellen
gameClient.connect();

// Spielzug senden
gameClient.sendMove({ row: 5, col: 5 });

// Wand senden
gameClient.sendWall({ position: 'h5-6' });

// Chat-Nachricht senden
gameClient.sendChatMessage('Guter Zug!');

// Verbindung trennen
// gameClient.disconnect();
*/
