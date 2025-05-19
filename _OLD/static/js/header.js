
function updatePlayersTurnInstruction(player){
    let turn_description = $(`
        <div style="overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">
            It's your turn,
            <span class="font-effect-outline" style="font-weight: 100; color: ${player.color}">${player.name}</span> !
        </div>
    `);
    $('#players_turn').html(turn_description);
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