const STATE_PLACE_PLAYER = -1;
const STATE_MOVE = 0;
const STATE_PLACE_WALL = 1;
const STATE_PLAYER_DID_WIN = 2;

var canvas = document.querySelector("canvas");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;
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
var players_action_state = STATE_PLACE_PLAYER;  // action that the player is performing

var mouse = {
    x: undefined,
    y: undefined
}

function clear(){
    ctx.clearRect(0, 0, innerWidth, innerHeight)
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

window.addEventListener("mousemove", function(event) {
    mouse.x = event.x + window.scrollX;  // scrollXY corrects mouse position 
    mouse.y = event.y + window.scrollY;  // when window is scrolled
});

window.addEventListener("mouseup", function(event) {
    if (players_action_state == STATE_PLACE_PLAYER) {
        field_clicked = getFieldByCoordinates(event.x + window.scrollX, event.y + window.scrollY);
        if (field_clicked != null) {
            current_player = players[its_this_players_turn];
            movePlayer(current_player, field_clicked, true);
            if (its_this_players_turn == players.length-1) {
                // if the last player placed its figure
                nextPlayersTurn();
            } else {
                nextPlayersTurn(STATE_PLACE_PLAYER);
            }
        }
    } else if (players_action_state == STATE_MOVE) {
        field_clicked = getFieldByCoordinates(event.x + window.scrollX, event.y + window.scrollY);
        if (field_clicked != null) {
            current_player = players[its_this_players_turn];
            movePlayer(current_player, field_clicked);
        }
    } else if (players_action_state == STATE_PLACE_WALL) {
        if (last_wall.wall_can_be_placed){
            placeWall();
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
    this.neighbour_fields = []
    this.player = null;

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

    this.addNeighbour = function(field) {
        this.neighbour_fields.push(field);
        field.neighbour_fields.push(this);
    }

    this.removeNeighbour = function(field) {
        field.neighbour_fields = removeFromArray(field.neighbour_fields, this);
        this.neighbour_fields = removeFromArray(this.neighbour_fields, field);
    }

    this.getNeighbourField = function(position) {
        // Returns the neighbour of the actual field
        // Position can be "right", "bottom", "left" or "top"
        if (position == "right") {
            return getFieldByColAndRow(this.col_num + 1, this.row_num);
        } else if (position == "bottom") {
            return getFieldByColAndRow(this.col_num, this.row_num + 1);
        } else if (position == "left") {
            return getFieldByColAndRow(this.col_num - 1, this.row_num);
        } else if (position == "top") {
            return getFieldByColAndRow(this.col_num, this.row_num - 1);
        } else {
            return null;
        }
    }

    this.getNeighbourFieldLocation = function(field_to_ckeck) {
        // The inverse function of getNeighbourField()
        if (field_to_ckeck == getFieldByColAndRow(this.col_num + 1, this.row_num)) {
            return "right";
        } else if (field_to_ckeck == getFieldByColAndRow(this.col_num, this.row_num + 1)) {
            return "bottom";
        } else if (field_to_ckeck == getFieldByColAndRow(this.col_num - 1, this.row_num)) {
            return "left";
        } else if (field_to_ckeck == getFieldByColAndRow(this.col_num, this.row_num - 1)) {
            return "top";
        } else {
            return null;
        }
    }
}

function Player(name, color) {
    this.name = name;
    this.color = color;
    this.field = null;  // this is the field where the player is at
    this.size = 24;
    this.amount_walls_left = 10;  // each player has 10 walls per game by default
    this.start_option_fields = [];  // the fields this player is allowed to start from needs to reach for win
    this.win_option_fields = [];  // the fields this player needs to reach for win

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

    this.drawMoveOptions = function() {
        var move_option_fields = this.getMoveOptions();
        move_option_fields.forEach(field => {
            this.drawMoveOption(field);
        });
    }

    this.getMoveOptions = function() {
        if (players_action_state == STATE_PLACE_PLAYER) {
            // if player is not placed yet, return the fields where he can be placed
            return this.start_option_fields;
        }
        var move_option_fields = [];
        this.field.neighbour_fields.forEach(field => {
            if (field.player == null) {
                move_option_fields.push(field);
            } else {
                location_of_neighbour_field = this.field.getNeighbourFieldLocation(field);
                var new_move_option_field = field.getNeighbourField(location_of_neighbour_field);
                if (new_move_option_field != null && new_move_option_field.player == null){
                    move_option_fields.push(new_move_option_field);
                }
            }
        });
        return move_option_fields;
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

function getFieldsByColOrRow(col_num, row_num) {
    // Returns all fields in the specified column / row.
    // Inputs can be col_num=k, row_num=null or col_num=null, row_num=k . 
    // Other inputs will return null.
    if (col_num < 0 || row_num < 0 || col_num > game_board.amount_fields-1 || row_num > game_board.amount_fields-1){
        return null;
    }
    var fields_to_return = [];
    if (col_num == null) {
        for (var i = 0; i < game_board.amount_fields; i++) {
            fields_to_return.push(getFieldByColAndRow(i, row_num));
        }
    } else if (row_num == null) {
        for (var i = 0; i < game_board.amount_fields; i++) {
            fields_to_return.push(getFieldByColAndRow(col_num, i));
        }
    } else {
        return null;
    }
    return fields_to_return;
}

function isWallOverlappingWithOtherWall(wall_to_ckeck) {
    // Returns true if two walls are overlapping, otherwise false.
    // Checking:    RectA.Left < RectB.Right && RectA.Right > RectB.Left &&
    //              RectA.Top > RectB.Bottom && RectA.Bottom < RectB.Top
    var is_opverlapping = false;
    walls.forEach(wall => {
        if (wall_to_ckeck.x < wall.x + wall.width && wall_to_ckeck.x + wall_to_ckeck.width > wall.x &&
            wall_to_ckeck.y + wall_to_ckeck.length > wall.y && wall_to_ckeck.y < wall.y + wall.length) {
                is_opverlapping = true;
        }
    });
    return is_opverlapping;
}



function nextPlayersTurn(next_players_action_state=STATE_MOVE){
    its_this_players_turn += 1;
    if (its_this_players_turn >= players.length) {
        its_this_players_turn = 0;
    }
    if (players_action_state == STATE_PLACE_WALL) {
        changePlayState();
    }
    player = players[its_this_players_turn];
    updatePlayersTurnInstuction(player.name);
    players_action_state = next_players_action_state;
}

function movePlayer(the_player, new_field, is_initial_move=false) {
    if (!is_initial_move) {
        old_field = the_player.field;
        distance_x = Math.abs(new_field.col_num - old_field.col_num);  // amount fields in x axis
        distance_y = Math.abs(new_field.row_num - old_field.row_num);  // amount fields in y axis
        total_distance = distance_x + distance_y;
        if (old_field == new_field){
            showNotify("error", "", "You have to move", 3);
        } else if (!the_player.getMoveOptions().includes(new_field)) {
            showNotify("error", "", "Illegal move", 3);
        } else {
            new_field.player = the_player;
            the_player.field.player = null; 
            the_player.field = new_field;
            nextPlayersTurn();
            playAudio();
        }
    } else {
        new_field.player = the_player;
        the_player.field = new_field;
        playAudio();
    }
    if (the_player.win_option_fields.includes(the_player.field)) {
        updatePlayerWonTheGame(the_player.name);
        players_action_state = STATE_PLAYER_DID_WIN;
    }
    the_player.draw();
}

function placeWall() {
    if (!isWallOverlappingWithOtherWall(last_wall.wall)) {
        attached_field = last_wall.field_where_wall_is_attached;
        if (last_wall.wall.is_vertical) {  // removing the connection between the fields
            attached_field.removeNeighbour(attached_field.getNeighbourField("left"));
            field_on_botton = attached_field.getNeighbourField("bottom");
            field_on_botton.removeNeighbour(field_on_botton.getNeighbourField("left"));
        } else {
            attached_field.removeNeighbour(attached_field.getNeighbourField("top"));
            field_on_right = attached_field.getNeighbourField("right");
            field_on_right.removeNeighbour(field_on_right.getNeighbourField("top"));
        }

        var can_all_players_win = true;
        for (var i = 0; i < players.length; i++) {
            player = players[i];
            var can_win = checkIfPathToWinExists(player.field, player.win_option_fields);
            if (can_win == false) {
                can_all_players_win = false;
            }
        }

        if (can_all_players_win) {
            current_player = players[its_this_players_turn];
            current_player.amount_walls_left -= 1;
            last_wall.wall.placed_by = current_player;
            walls.push(last_wall.wall);
            
            refreshPlayerStats();
            last_wall.wall = new Wall();
            nextPlayersTurn();
            playAudio();
        } else {
            // readding the connection between the fields (because wall could not be placed)
            if (last_wall.wall.is_vertical) {
                field_left = attached_field.getNeighbourField("left");
                field_on_botton = attached_field.getNeighbourField("bottom");
                field_on_botton_left = attached_field.getNeighbourField("left");
                attached_field.addNeighbour(field_left);
                field_on_botton.addNeighbour(field_on_botton_left);
            } else {
                field_on_top = attached_field.getNeighbourField("top");
                field_right = attached_field.getNeighbourField("right");
                field_on_top_right = attached_field.getNeighbourField("right");
                attached_field.addNeighbour(field_on_top);
                field_right.addNeighbour(field_on_top_right);

            }
            showNotify("error", "Could not place wall", "This wall would block one player from winning", 10);
        }
    } else {
        showNotify("error", "", "Walls should not overlap", 10);
    }
}

function removeFromArray(array, value) {
    var idx = array.indexOf(value);
    if (idx !== -1) {
        array.splice(idx, 1);
    }
    return array;
}

function checkIfPathToWinExists(field, fields_to_win) {
    // Returns true if there is at least one path from field to one of 
    // the fields in fields_to_win. Otherwise returns false.
    // TODO: Find fancier way (recursion going through all paths is to much)
    for (var i = 0; i < 10000; i++) {
        if (!fields_to_win.includes(field)) {
            var next_fieldnumber = Math.floor(Math.random() * field.neighbour_fields.length);
            field = field.neighbour_fields[next_fieldnumber];
        } else {
            return true;
        }
    }
    return false;
    
}




function drawBoard() {
    game_board = new GameBoard(650); 
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
        } else if (players_action_state != STATE_PLAYER_DID_WIN) {
            players[its_this_players_turn].drawMoveOptions();
        }
    }
}

drawBoard();
createFields();
last_wall.wall = new Wall();
animate();

