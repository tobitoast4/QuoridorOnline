const STATE_MOVE = 0;
const STATE_PLACE_WALL = 1;

var canvas = document.querySelector("canvas");
var players_turn_div = document.getElementById("players_turn");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight * 0.9;
var ctx = canvas.getContext("2d");

var game_board;
var fields = [];
var players = [];
var walls = [];
// its_this_players_turn should be an integer indicating whos turn it is. 
// Should reference the player by index in the players array.
var its_this_players_turn = 0;
var players_action_state = STATE_MOVE;  // action that the player is performing

var last_sticky_wall = {
    x: null,
    y: null,
    is_vertical: null
}

function clear(){
    ctx.clearRect(0, 0, innerWidth, innerHeight)
}

var mouse = {
    x: undefined,
    y: undefined
}

window.addEventListener("mousemove", function(event) {
    mouse.x = event.x;
    mouse.y = event.y;
});

window.addEventListener("mouseup", function(event) {
    if (players_action_state == STATE_MOVE) {
        field_clicked = getFieldByCoordinates(event.x, event.y);
        if (field_clicked != null) {
            current_player = players[its_this_players_turn];
            
            movePlayer(current_player, field_clicked);
        }
    } else if (players_action_state == STATE_PLACE_WALL) {

    }
});

document.addEventListener('keyup', function(event) {
    if (event.key = ' ') {
        if (players_action_state == STATE_MOVE) {
            players_action_state = STATE_PLACE_WALL;
        } else if (players_action_state == STATE_PLACE_WALL) {
            players_action_state = STATE_MOVE;
        }
    }
});

window.addEventListener("resize", function(event) {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    fields = [];
    clear();
    drawFields(); 
    drawPlayers();
})


function GameBoard(size) {
    this.size = size;
    this.start_x = canvas.width/2 - this.size/2;
    this.start_y = 100;
    this.field_size = this.size / 9; // this is the field size INCLUDING the GAP
    this.margin_between_fields = 8;
    this.wall_width = this.margin_between_fields;
    this.wall_length = this.field_size * 2 - this.margin_between_fields;

    this.draw = function() {
        ctx.beginPath();
        ctx.roundRect(this.start_x - this.margin_between_fields*2, this.start_y - this.margin_between_fields*2, 
            this.size + this.margin_between_fields*4, this.size + this.margin_between_fields*4, 24);
        
        ctx.fillStyle = "#bbf7d0";
        ctx.fill();
    }
}

function Field(x, y, col_num, row_num, game_board) {
    this.x = x + game_board.margin_between_fields;
    this.y = y + game_board.margin_between_fields;
    this.col_num = col_num;
    this.row_num = row_num;
    this.size = game_board.field_size - game_board.margin_between_fields;
    this.fill_color = "white";
    this.neighbour_fields = []
    this.player = null;

    this.draw = function() {
        ctx.beginPath();
        size = this.size - game_board.margin_between_fields;
        ctx.roundRect(this.x, this.y, size, size, 15);
        ctx.strokeStyle = "black";
        ctx.fillStyle = this.fill_color;
        ctx.stroke();
        ctx.fill();
    }

    this.update = function() {
        // hover effect
        if (mouse.x > this.x && mouse.x < this.x + this.size - game_board.margin_between_fields 
           && mouse.y > this.y && mouse.y < this.y + this.size - game_board.margin_between_fields){
            this.fill_color = "#e0e0e0";
            // console.log("Col: " + this.col_num + " Row: " + this.row_num);
            //console.log(this);
        } else {
            this.fill_color = "white";
        }

        this.draw();
    }
}

function Player(name, color){
    this.name = name;
    this.color = color;
    this.field = null;  // this is the field where the player is at
    this.size = 24;

    this.draw = function() {
        // expects the field where to draw the player
        this.field = getFieldByColAndRow(this.field.col_num, this.field.row_num);  // This line is necessary for 
        // resize event. Otherwise players will not move on resizing.
        ctx.beginPath();
        ctx.roundRect(this.field.x + game_board.field_size/2 - game_board.margin_between_fields - this.size/2, 
                      this.field.y + game_board.field_size/2 - game_board.margin_between_fields - this.size/2, 
                      this.size, this.size, 9);
        ctx.strokeStyle = this.color;
        ctx.fillStyle = this.color;
        ctx.stroke();
        ctx.fill();
    }

    this.drawMoveOptions = function() {
        current_players_field = getFieldByColAndRow(this.field.col_num, this.field.row_num);
        current_players_field.neighbour_fields.forEach(field => {
            this.drawMoveOption(field);
        });
    }

    this.drawMoveOption = function(field) {
        radius = 3;
        ctx.beginPath();
        ctx.arc(field.x + game_board.field_size/2 - game_board.margin_between_fields, 
                field.y + game_board.field_size/2 - game_board.margin_between_fields, 
                radius, 0, 2 * Math.PI);
        ctx.fillStyle = this.color;
        ctx.fill();
    }
}

function Wall(){
    this.x = null;
    this.y = null;
    this.width = game_board.margin_between_fields;
    this.length = game_board.field_size * 2 - game_board.margin_between_fields;
    this.is_vertical = true;
    this.placed_by = null;

    this.draw = function(x, y, width, height) {
        ctx.beginPath();
        ctx.roundRect(x, y, width, height, 9);
        ctx.fillStyle = "brown";
        ctx.fill();
    }
    
    this.drawSelf = function(x, y, width, height) {
        ctx.beginPath();
        ctx.roundRect(x, y, width, height, 9);
        ctx.fillStyle = "brown";
        ctx.fill();
    }
    
    this.drawOnHover = function() {
        var is_not_yet_drawn = true;
        fields.forEach(field => {
            if (mouse.x < field.x && mouse.x > field.x - game_board.margin_between_fields * 2 &&
                mouse.y > field.y && mouse.y < field.y + game_board.field_size - game_board.margin_between_fields * 2) {
                // drawing the wall vertically between cells
                    if (field.row_num == 8){  // in the last row, the cells should not hang out of the bottom of the field
                        this.draw(field.x - game_board.margin_between_fields * 1.5, 
                            field.y - game_board.margin_between_fields * 0.5 - game_board.field_size, 
                            this.width, this.length);
                    } else if (field.col_num != 0){
                        this.draw(field.x - game_board.margin_between_fields * 1.5,
                            field.y - game_board.margin_between_fields * 0.5, 
                            this.width, this.length);
                    }
                    is_not_yet_drawn = false;
                    this.is_vertical = true;
            } else if (mouse.y < field.y && mouse.y > field.y - game_board.margin_between_fields * 2 &&
                mouse.x > field.x && mouse.x < field.x + game_board.field_size - game_board.margin_between_fields * 2) {
                // drawing the wall horizontally between two cells
                    if (field.col_num == 8) {  // in the last row, the cells should not hang out of field (to the right side)
                        this.draw(field.x - game_board.margin_between_fields * 0.5 - game_board.field_size, 
                            field.y - game_board.margin_between_fields * 1.5,
                            this.length, this.width);
                    } else if (field.row_num != 0) {
                        this.draw(field.x - game_board.margin_between_fields * 0.5, 
                            field.y - game_board.margin_between_fields * 1.5,
                            this.length, this.width);
                    }
                    is_not_yet_drawn = false;
                    this.is_vertical = false;
            } 
        });

        if (is_not_yet_drawn) {  // draw the wall at mouse position if it is not drawn already ('sticky') between two cells
            if (this.is_vertical) {  // keep the last orientation
                this.draw(mouse.x - 0.5 * this.width, mouse.y - 0.25 * this.length, this.width, this.length);
            } else {
                this.draw(mouse.x - 0.25 * this.length, mouse.y - 0.5 * this.width, this.length, this.width);
            }
        }
    }
}

this.drawNewWallByLastPosition = function() {
    wall = new Wall();
    ctx.beginPath();
    ctx.roundRect(last_sticky_wall.x, last_sticky_wall.y, last_sticky_wall.width, last_sticky_wall.height, 9);
    ctx.fillStyle = "brown";
    ctx.fill();
}





function getFieldByCoordinates(x, y) {
    var field_to_return = null;
    fields.forEach(field => {
        if (x > field.x && x < field.x + field.size - game_board.margin_between_fields 
            && y > field.y && y < field.y + field.size - game_board.margin_between_fields){
                field_to_return = field;
        }
    });
    return field_to_return;
}

function getFieldByColAndRow(col_num, row_num){
    if (col_num < 0 || row_num < 0 || col_num > 8 || row_num > 8){
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

function nextPlayersTurn(){
    its_this_players_turn += 1;
    if (its_this_players_turn >= players.length) {
        its_this_players_turn = 0;
    }
    player = players[its_this_players_turn];
    players_turn_div.innerHTML = "It's your turn, " + player.name + "!";
}

function movePlayer(the_player, new_field, is_initial_move=false) {
    if (!is_initial_move) {
        old_field = the_player.field;
        distance_x = Math.abs(new_field.col_num - old_field.col_num);  // amount fields in x axis
        distance_y = Math.abs(new_field.row_num - old_field.row_num);  // amount fields in y axis
        total_distance = distance_x + distance_y;
        if (total_distance == 0){
            showNotify("error", "", "You have to move", 30);
        } else if (total_distance > 1){
            showNotify("error", "", "You can only move one field up/down or one to the sides", 300);
        } else {
            new_field.player = the_player;
            the_player.field = new_field
            the_player.draw();
            nextPlayersTurn();
        }
    } else {
        new_field.player = the_player;
        the_player.field = new_field
        the_player.draw();
    }
}






function drawBoard() {
    game_board = new GameBoard(600); 
    game_board.draw();
}

function drawFields() {
    var field_col_num = 0;
    for (var x = game_board.start_x; x < game_board.start_x + game_board.size - 1; x += game_board.field_size) {
        var field_row_num = 0;
        for (var y = game_board.start_y; y < game_board.start_y + game_board.size - 1; y += game_board.field_size) {
            var field = new Field(x, y, field_col_num, field_row_num, game_board);
            fields.push(field);
            field.draw();
            field_row_num++;
        }
        field_col_num++;
    }

    // Add the neighbour fields as references of each field
    fields.forEach(field => {
        field_on_top = getFieldByColAndRow(field.col_num - 1, field.row_num);
        if (field_on_top != null) field.neighbour_fields.push(field_on_top);
        field_on_bottom = getFieldByColAndRow(field.col_num + 1, field.row_num);
        if (field_on_bottom != null) field.neighbour_fields.push(field_on_bottom);
        field_left = getFieldByColAndRow(field.col_num, field.row_num - 1);
        if (field_left != null) field.neighbour_fields.push(field_left);
        field_right = getFieldByColAndRow(field.col_num, field.row_num + 1);
        if (field_right != null) field.neighbour_fields.push(field_right);
    });
}

function drawPlayers() {
    players.forEach(player => {
        player.draw();
    });
}


function animate(){
    requestAnimationFrame(animate);
    clear();
    drawBoard();

    // update fields on hover
    for (var i = 0; i < fields.length; i++){
        fields[i].update();
    }
    
    drawPlayers();
    // draw move options for current player
    if (players.length > 1) {
        if (players_action_state == STATE_MOVE) {
            players[its_this_players_turn].drawMoveOptions();
        } else if (players_action_state == STATE_PLACE_WALL) {
            wall.drawOnHover();
        } 
    }
}

drawBoard();
drawFields();
wall = new Wall();
animate();

