
function updatePlayersTurnInstuction(player_name){
    $('#players_turn').html("It's your turn, " + player_name + "!");
}

function updatePlayerWonTheGame(player_name){
    $('#players_turn').html("" + player_name + " won the game!");

    $('#game_over_overlay').removeAttr("style");
    $('#game_over_overlay_text').text("" + player_name + " won the game!");
}

function closeGameOverScreen(){
    $('#game_over_overlay').attr("style", "display:none");
}

function playAgain(){
    window.location.replace(server_url + 'lobby/' + next_lobby_id);
}