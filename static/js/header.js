
function updatePlayersTurnInstuction(player_name){
    $('#players_turn').html("It's your turn, " + player_name + "!");
}

function updatePlayerWonTheGame(player_name){
    $('#players_turn').html("" + player_name + " won the game!");

    $('#back_to_menu_overlay').removeAttr("style");
    $('#back_to_menu_overlay_text').text("" + player_name + " won the game!");
}

function closeGameOverScreen(){
    $('#back_to_menu_overlay').attr("style", "display:none");
}

function playAgain(){
    window.location.replace(server_url + 'lobby/' + next_lobby_id);
}