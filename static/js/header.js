
function updatePlayersTurnInstuction(player_name){
    $('#players_turn').html("It's your turn, " + player_name + "!");
}

function updatePlayerWonTheGame(player_name){
    $('#players_turn').html("Congratiulations! " + player_name + " won the game!");
}