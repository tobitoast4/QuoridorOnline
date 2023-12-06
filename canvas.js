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
var last_wall = {
    wall: null,
    wall_can_be_placed: false,
    field_where_wall_is_attached: null
}
// its_this_players_turn should be an integer indicating whos turn it is. 
// Should reference the player by index in the players array.
var its_this_players_turn = 0;
var players_action_state = STATE_MOVE;  // action that the player is performing

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
        if (last_wall.wall_can_be_placed){
            current_player = players[its_this_players_turn];
            last_wall.wall.placed_by = current_player;
            walls.push(last_wall.wall);
            last_wall.wall = new Wall();
            nextPlayersTurn();
        }
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
    this.width = null;
    this.length = null;
    this.is_vertical = true;  // gets changed when mouse hovers betweeen fields
    this.placed_by = null;

    this.setSizes = function(x, y, width, length) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.length = length;
    }
    
    this.draw = function() {
        ctx.beginPath();
        ctx.roundRect(this.x, this.y, this.width, this.length, 9);
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
            if (mouse.x < field.x && mouse.x > field.x - game_board.margin_between_fields * 2 &&
                mouse.y > field.y && mouse.y < field.y + game_board.field_size - game_board.margin_between_fields * 2) {
                // drawing the wall vertically between cells
                    if (field.row_num == 8){  // in the last row, the cells should not hang out of the bottom of the field
                        this.setSizes(field.x - game_board.margin_between_fields * 1.5, 
                            field.y - game_board.margin_between_fields * 0.5 - game_board.field_size, 
                            width, length);
                        field = getFieldByColAndRow(field.col_num, field.row_num - 1);
                        this.drawWallAndSaveIntermediate(true, field);
                        is_not_yet_drawn = false;
                    } else if (field.col_num != 0){
                        this.setSizes(field.x - game_board.margin_between_fields * 1.5,
                            field.y - game_board.margin_between_fields * 0.5, 
                            width, length);
                        this.drawWallAndSaveIntermediate(true, field);
                        is_not_yet_drawn = false;
                    }
            } else if (mouse.y < field.y && mouse.y > field.y - game_board.margin_between_fields * 2 &&
                mouse.x > field.x && mouse.x < field.x + game_board.field_size - game_board.margin_between_fields * 2) {
                // drawing the wall horizontally between two cells
                    if (field.col_num == 8) {  // in the last row, the cells should not hang out of field (to the right side)
                        this.setSizes(field.x - game_board.margin_between_fields * 0.5 - game_board.field_size, 
                            field.y - game_board.margin_between_fields * 1.5,
                            length, width);
                        field = getFieldByColAndRow(field.col_num - 1, field.row_num);
                        this.drawWallAndSaveIntermediate(false, field);
                        is_not_yet_drawn = false;
                    } else if (field.row_num != 0) {
                        this.setSizes(field.x - game_board.margin_between_fields * 0.5, 
                            field.y - game_board.margin_between_fields * 1.5,
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
    players_action_state = STATE_MOVE;
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
            showNotify("error", "", "Illegal move", 300);
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



function animate(){
    requestAnimationFrame(animate);
    clear();
    drawBoard();

    // update fields on hover
    for (var i = 0; i < fields.length; i++){
        fields[i].update();
    }
    
    // drawing the players
    players.forEach(player => {
        player.draw();
    });
    
    // drawing the walls
    walls.forEach(wall => {
        wall.draw();
    });

    // draw move options for current player
    if (players.length > 1) {
        if (players_action_state == STATE_MOVE) {
            players[its_this_players_turn].drawMoveOptions();
        } else if (players_action_state == STATE_PLACE_WALL) {
            last_wall.wall.drawOnHover();
        } 
    }
}

drawBoard();
drawFields();
last_wall.wall = new Wall();
animate();

