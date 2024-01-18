const STATE_PLACE_PLAYER = -1;
const STATE_MOVE = 0;
const STATE_PLACE_WALL = 1;
const STATE_PLAYER_DID_WIN = 2;

var canvas = document.querySelector("canvas");

canvas.width = window.innerWidth;
canvas.height = 850;
var ctx = canvas.getContext("2d");

var game_board;
var current_round_diff = 0;
var fields = [];
var players = [];
var walls = [];
var last_wall = {
    wall: null,
    wall_can_be_placed: false,
    field_where_wall_is_attached: null
}
// its_this_players_turn should be an integer indicating whose turn it is.
// Should reference the player by index in the players array.
var its_this_players_turn = 0;
var players_action_state = STATE_PLACE_PLAYER;  // action that the player is performing

var mouse = {
    x: undefined,
    y: undefined
}

// ##########################
// this is for mobile devices
let last_touch_X = -1;
let last_touch_Y = -1;
document.addEventListener('touchend', e => {
    last_touch_X = -1;
    last_touch_Y = -1;
})

document.addEventListener("touchmove", function clicked(e) {
    if (last_touch_X >= 0) {
        let touch_distance_X = e.touches[0].screenX - last_touch_X;
        let touch_distance_Y = e.touches[0].screenY - last_touch_Y;
        mouse.x = mouse.x + touch_distance_X;
        mouse.y = mouse.y + touch_distance_Y;
    }
    last_touch_X = e.touches[0].screenX;
    last_touch_Y = e.touches[0].screenY;
});
// ##########################

function clear(){
    ctx.clearRect(0, 0, innerWidth, innerHeight)
}

window.addEventListener("mousemove", function(event) {
    mouse.x = event.x + window.scrollX;  // scrollXY corrects mouse position 
    mouse.y = event.y + window.scrollY;  // when window is scrolled
});

window.addEventListener("mouseup", function(event) {
    current_player = players[its_this_players_turn];
    if (players_action_state == STATE_PLACE_PLAYER) {
        field_clicked = getFieldByCoordinates(event.x + window.scrollX, event.y + window.scrollY);
        if (field_clicked != null) {
            movePlayerAsync(current_player.player_id, field_clicked.col_num, field_clicked.row_num);
        }
    } else if (players_action_state == STATE_MOVE) {
        field_clicked = getFieldByCoordinates(event.x + window.scrollX, event.y + window.scrollY);
        if (field_clicked != null) {
            movePlayerAsync(current_player.player_id, field_clicked.col_num, field_clicked.row_num);
        }
    } else if (players_action_state == STATE_PLACE_WALL) {
        if (last_wall.wall_can_be_placed){
            placeWall(current_player);
        }
    }
});

document.addEventListener('keyup', function(event) {
    if (event.key == '.') {
        field_clicked = getFieldByCoordinates(mouse.x + window.scrollX, mouse.y + window.scrollY);
        console.log(field_clicked);
    } else if (event.key) {
        changePlayState();
    }
});

function changePlayState() {
    // switches between STATE_MOVE and STATE_PLACE_WALL
    if (players_action_state == STATE_MOVE) {
        players_action_state = STATE_PLACE_WALL;
        // adapt button style
        $('#button-place-walls').toggleClass("control-button-active");
    } else if (players_action_state == STATE_PLACE_WALL) {
        players_action_state = STATE_MOVE;
        // adapt button style
        $('#button-place-walls').toggleClass("control-button-active");
    }
}

window.addEventListener("resize", function(event) {
    canvas.width = window.innerWidth;
    if (canvas.width < game_board.size) {
        canvas.width = game_board.size;
    }
    canvas.height = window.innerHeight;
    if (canvas.height < game_board.size) {
        canvas.height = game_board.size;
    }
})


function GameBoard(size) {
    this.size = size;
    this.start_x = canvas.width/2 - this.size/2;
    this.start_y = 100;
    this.amount_fields = 9;
    this.field_size = this.size / this.amount_fields; // this is the field size INCLUDING the GAP
    this.margin_between_fields = 8;
    this.wall_width = this.margin_between_fields;
    this.wall_length = this.field_size * 2 - this.margin_between_fields * 1.5;

    this.draw = function() {
        ctx.beginPath();
        ctx.roundRect(this.start_x - this.margin_between_fields*2, this.start_y - this.margin_between_fields*2, 
            this.size + this.margin_between_fields*4, this.size + this.margin_between_fields*4, 24);
        
        ctx.fillStyle = "#bbf7d0";
        ctx.fill();
    }
}

function Field(x, y, col_num, row_num) {
    this.x = x + game_board.margin_between_fields - game_board.start_x;
    this.y = y + game_board.margin_between_fields - game_board.start_y;
    this.col_num = col_num;
    this.row_num = row_num;
    this.size = game_board.field_size - game_board.margin_between_fields;
    this.fill_color = "white";

    this.draw = function() {
        ctx.beginPath();
        size = this.size - game_board.margin_between_fields;
        ctx.roundRect(this.x + game_board.start_x, this.y + game_board.start_y, size, size, 15);
        ctx.strokeStyle = "black";
        ctx.fillStyle = this.fill_color;
        ctx.stroke();
        ctx.fill();
    }

    this.update = function() {
        // hover effect
        if (mouse.x > this.x + game_board.start_x && mouse.x < this.x + game_board.start_x + this.size - game_board.margin_between_fields 
           && mouse.y > this.y + game_board.start_y && mouse.y < this.y + game_board.start_y + this.size - game_board.margin_between_fields){
            this.fill_color = "#e0e0e0";
            // console.log("Col: " + this.col_num + " Row: " + this.row_num);
            // console.log(this);
        } else {
            this.fill_color = "white";
        }

        this.draw();
    }
}

function Player(player_id, name, amount_walls_left, color) {
    this.player_id = player_id;
    this.name = name;
    this.color = color;
    this.field = null;  // this is the field where the player is at
    this.size = 24;
    this.amount_walls_left = amount_walls_left;  // each player has 10 walls per game by default
    this.start_option_fields = [];  // the fields this player is allowed to start from needs to reach for win
    this.win_option_fields = [];  // the fields this player needs to reach for win
    this.move_option_fields = [];  // the fields this player can move to in the next round

    this.draw = function() {
        if (this.field != null) {  // if player is not placed yet, dont draw it
            // expects the field where to draw the player
            this.field = getFieldByColAndRow(this.field.col_num, this.field.row_num);  // This line is necessary for 
            // resize event. Otherwise players will not move on resizing.
            ctx.beginPath();
            ctx.roundRect(this.field.x + game_board.start_x + game_board.field_size/2 - game_board.margin_between_fields - this.size/2, 
                          this.field.y + game_board.start_y + game_board.field_size/2 - game_board.margin_between_fields - this.size/2, 
                          this.size, this.size, 9);
            ctx.strokeStyle = this.color;
            ctx.fillStyle = this.color;
            ctx.stroke();
            ctx.fill();
        }
    }

    this.drawMoveOptions = function(initial_options=false) {
        var move_option_fields = null;
        if (initial_options) {
             move_option_fields = this.start_option_fields;
        } else {
             move_option_fields = this.move_option_fields;
        }
        move_option_fields.forEach(field => {
            this.drawMoveOption(field);
        });
    }

    this.drawMoveOption = function(field) {
        radius = 3;
        ctx.beginPath();
        ctx.arc(field.x + game_board.start_x + game_board.field_size/2 - game_board.margin_between_fields, 
                field.y + game_board.start_y + game_board.field_size/2 - game_board.margin_between_fields, 
                radius, 0, 2 * Math.PI);
        ctx.fillStyle = this.color;
        ctx.fill();
    }
}

function Wall() {
    this.x = null;
    this.y = null;
    this.width = null;
    this.length = null;
    this.is_vertical = true;  // gets changed when mouse hovers betweeen fields
    this.placed_by = null;

    this.setSizes = function(x, y, width, length) {
        this.x = x - game_board.start_x;  // making it work for resizing
        this.y = y - game_board.start_y;
        this.width = width;
        this.length = length;
    }
    
    this.draw = function() {
        ctx.beginPath();
        ctx.roundRect(this.x + game_board.start_x, this.y + game_board.start_y, this.width, this.length, 9);
        ctx.fillStyle = "brown";
        ctx.fill();
    }
    
    this.drawOnHover = function() {
        // this method takes care:
        //  1. that a wall is drawn in empty space
        //  2. that a wall is drwan between two fields (sticky wall)
        //  3. the information of where the wall is is stored and can be used on mouseclick to place the wall
        last_wall.wall_can_be_placed = false; // states that the wall is currently not sticked to a field (-> loose in space)
        var width = game_board.wall_width;
        var length = game_board.wall_length;
        var is_not_yet_drawn = true;
        fields.forEach(field => {
            var field_x = field.x + game_board.start_x;
            var field_y = field.y + game_board.start_y;
            if (mouse.x < field_x && mouse.x > field_x - game_board.margin_between_fields * 2 &&
                mouse.y > field_y && mouse.y < field_y + game_board.field_size - game_board.margin_between_fields * 2) {
                // drawing the wall vertically between cells
                    if (field.row_num == game_board.amount_fields-1){  // in the last row, the cells should not hang out of the bottom of the field
                        this.setSizes(field_x - game_board.margin_between_fields * 1.5, 
                            field_y - game_board.margin_between_fields * 0.25 - game_board.field_size, 
                            width, length);
                        field = getFieldByColAndRow(field.col_num, field.row_num - 1);
                        this.drawWallAndSaveIntermediate(true, field);
                        is_not_yet_drawn = false;
                    } else if (field.col_num != 0){
                        this.setSizes(field_x - game_board.margin_between_fields * 1.5,
                            field_y - game_board.margin_between_fields * 0.25, 
                            width, length);
                        this.drawWallAndSaveIntermediate(true, field);
                        is_not_yet_drawn = false;
                    }
            } else if (mouse.y < field_y && mouse.y > field_y - game_board.margin_between_fields * 2 &&
                mouse.x > field_x && mouse.x < field_x + game_board.field_size - game_board.margin_between_fields * 2) {
                // drawing the wall horizontally between two cells
                    if (field.col_num == game_board.amount_fields-1) {  // in the last row, the cells should not hang out of field (to the right side)
                        this.setSizes(field_x - game_board.margin_between_fields * 0.25 - game_board.field_size, 
                            field_y - game_board.margin_between_fields * 1.5,
                            length, width);
                        field = getFieldByColAndRow(field.col_num - 1, field.row_num);
                        this.drawWallAndSaveIntermediate(false, field);
                        is_not_yet_drawn = false;
                    } else if (field.row_num != 0) {
                        this.setSizes(field_x - game_board.margin_between_fields * 0.25, 
                            field_y - game_board.margin_between_fields * 1.5,
                            length, width);
                        this.drawWallAndSaveIntermediate(false, field);
                        is_not_yet_drawn = false;
                    }
            } 
        });
        

        if (is_not_yet_drawn) {  // draw the wall at mouse position if it is not drawn already ('sticky') between two cells
            if (this.is_vertical) {  // keep the last orientation
                this.setSizes(mouse.x - 0.5 * width, mouse.y - 0.25 * length, width, length);
                this.draw();
            } else {
                this.setSizes(mouse.x - 0.25 * length, mouse.y - 0.5 * width, length, width);
                this.draw();
            }
        }
    }
    
    this.drawWallAndSaveIntermediate = function(is_vertical, field) {
        this.draw();
        this.is_vertical = is_vertical;
        last_wall.wall_can_be_placed = true;
        last_wall.field_where_wall_is_attached = field;
    }
}


function getFieldByCoordinates(x, y) {
    var field_to_return = null;
    fields.forEach(field => {
        var field_x = field.x + game_board.start_x;
        var field_y = field.y + game_board.start_y;
        if (x > field_x && x < field_x + field.size - game_board.margin_between_fields 
            && y > field_y && y < field_y + field.size - game_board.margin_between_fields){
                field_to_return = field;
        }
    });
    return field_to_return;
}

function getFieldByColAndRow(col_num, row_num) {
    if (col_num < 0 || row_num < 0 || col_num > game_board.amount_fields-1 || row_num > game_board.amount_fields-1){
        return null;
    }
    var field_to_return = null;
    fields.forEach(field => {
        if (field.col_num == col_num && field.row_num == row_num) {
            field_to_return = field;
        }
    });
    return field_to_return;
}

function placeWall(the_player) {
    attached_field = last_wall.field_where_wall_is_attached;
    let col_start = -1;
    let row_start = -1;
    let col_end = -1;
    let row_end = -1;
    console.log(attached_field);
    // convert to format (col_start, row_start, col_end, row_end) // TODO: unify this
    if (last_wall.wall.is_vertical) {
        col_start = attached_field.col_num - 0.5;
        col_end = attached_field.col_num - 0.5;
        row_start = attached_field.row_num;
        row_end = attached_field.row_num + 1;
    } else {
        row_start = attached_field.row_num - 0.5;
        row_end = attached_field.row_num - 0.5;
        col_start = attached_field.col_num;
        col_end = attached_field.col_num + 1;
    }

    placeWallAsync(the_player.player_id, col_start, row_start, col_end, row_end);
}

function placeWallByServerCoordinates(col_start, row_start, col_end, row_end) {
    var width = game_board.wall_width;
    var length = game_board.wall_length;
    let wall = new Wall();
    if (col_start == col_end) {  // wall is vertical
        let field = getFieldByColAndRow(col_start + 0.5, row_start);
        var field_x = field.x + game_board.start_x;
        var field_y = field.y + game_board.start_y;
        console.log(field);
        wall.setSizes(field_x - game_board.margin_between_fields * 1.5,
            field_y - game_board.margin_between_fields * 0.25,
            width, length);
    } else {
        let field = getFieldByColAndRow(col_start, row_start + 0.5);
        var field_x = field.x + game_board.start_x;
        var field_y = field.y + game_board.start_y;
        wall.setSizes(field_x - game_board.margin_between_fields * 0.25,
            field_y - game_board.margin_between_fields * 1.5,
            length, width);
    }

    wall.draw();
    walls.push(wall);
}


function viewPreviousOrNextGameRound(round_diff) {
    current_round_diff = current_round_diff + round_diff;
    if (current_round_diff <= 0) {
        current_round_diff = 0;
    }
    let game_data = complete_game_data["game"];  // complete_game_data is defined in query_server.js
    if (current_round_diff > game_data.length - players.length) {
        current_round_diff = game_data.length - players.length;
    }

    updateGame(current_round_diff+1);
}

function itsLoggedInPlayersTurn(field, fields_to_win) {
    // Indicates if the currently logged in player is at turn.
    // Returns ture if yes, false if no.
    if (this_player_id == players[its_this_players_turn].player_id) {  // it's the other players turn
        return true;
    } else {
        return false;
    }
}


function drawBoard() {
    game_board = new GameBoard(canvas.height - 200);
    game_board.draw();
}

function createFields() {
    var field_col_num = 0;
    for (var x = game_board.start_x; x < game_board.start_x + game_board.size - 1; x += game_board.field_size) {
        var field_row_num = 0;
        for (var y = game_board.start_y; y < game_board.start_y + game_board.size - 1; y += game_board.field_size) {
            var field = new Field(x, y, field_col_num, field_row_num, game_board);
            fields.push(field);
            field_row_num++;
        }
        field_col_num++;
    }
}

function animate(){
    requestAnimationFrame(animate);
    clear();
    drawBoard();

    // drawing the fields (and updating on hover)
    fields.forEach(field => {
        field.update();
    });
    
    // drawing the players
    players.forEach(player => {
        player.draw();
    });
    
    // drawing the walls
    walls.forEach(wall => {
        wall.draw();
    });

    // draw move options for current player
    if (players.length >= 1) {
        if (players_action_state == STATE_PLACE_WALL) {
            last_wall.wall.drawOnHover();
        } else if (players_action_state == STATE_PLACE_PLAYER) {
            if (itsLoggedInPlayersTurn() && current_round_diff == 0) {
                players[its_this_players_turn].drawMoveOptions(true);
            }
        } else if (players_action_state != STATE_PLAYER_DID_WIN) {
            if (itsLoggedInPlayersTurn() && current_round_diff == 0) {
                players[its_this_players_turn].drawMoveOptions();
            }
        }
    }
}

drawBoard();
createFields();
last_wall.wall = new Wall();
animate();
