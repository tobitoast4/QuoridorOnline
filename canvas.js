var canvas = document.querySelector("canvas");
var players_turn_div = document.getElementById("players_turn");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight * 0.8;
var ctx = canvas.getContext("2d");

var game_board;
var fields = [];
var players = [];
// its_this_players_turn should be an integer indicating whos turn it is. 
// Should reference the player by index in the players array.
var its_this_players_turn = 0; 

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
    field_clicked = getFieldByCoordinates(event.x, event.y);
    if (field_clicked != null) {
        current_player = players[its_this_players_turn];
        
        movePlayer(current_player, field_clicked);
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
        current_field_col = this.field.col_num;
        current_field_row = this.field.row_num;
        // TODO: make this code fancier
        field_move_option = getFieldByColAndRow(current_field_col - 1, current_field_row);
        if (field_move_option != null) {
            this.drawMoveOption(field_move_option);
        }
        field_move_option = getFieldByColAndRow(current_field_col + 1, current_field_row);
        if (field_move_option != null) {
            this.drawMoveOption(field_move_option);
        }
        field_move_option = getFieldByColAndRow(current_field_col, current_field_row - 1);
        if (field_move_option != null) {
            this.drawMoveOption(field_move_option);
        }
        field_move_option = getFieldByColAndRow(current_field_col, current_field_row + 1);
        if (field_move_option != null) {
            this.drawMoveOption(field_move_option);
        }
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



function getFieldByCoordinates(x, y){
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
            showNotify("error", "Invalid move", "You have to move", 30);
        } else if (total_distance > 1){
            showNotify("error", "Invalid move", "You can only move one field up/down or one to the sides", 300);
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
        players[its_this_players_turn].drawMoveOptions();
    }
}

drawBoard();
drawFields();
animate();

