let online_user_ids = [];

function refreshPlayerStats() {
    $('#stats_grid').empty();
    players.forEach(player => {
        var player_stats = $('<div class="two-col-grid"></div>');
        player_stats.append('<h2 style="text-align: right;">' + player.name + `<span 
            id="online-status-${player.player_id}" title="online" class="online-dot" style="background-color: #a8a8a8;"></span>
        </h2>`);
    
        var wall_box = $('<div id="remaining_walls_container" style="display: flex; gap: 3px; padding: 20px; padding-left: 8px;"></div>');
        for (var i = 0; i < player.amount_walls_left; i++) {
            wall_box.append('<div style="background-color: ' + player.color + '; width: 5px; height: 24px;"></div>');
        }
        player_stats.append(wall_box);
        $('#stats_grid').append(player_stats);

        if (player.player_id == this_player_id || online_user_ids.includes(player.player_id)) {
            // if the player is online or the player themselves, set the online status to green
            updatePlayerOnlineStatus(player.player_id, true);
        }
    });

}

function updatePlayerOnlineStatus(player_id, is_online) {
    var online_status_dot = $('#online-status-' + player_id);
    if (is_online) {
        online_status_dot.css('background-color', '#00DD00');
        online_status_dot.attr('title', 'online');
        online_user_ids.push(player_id);
    } else {
        online_status_dot.css('background-color', '#a8a8a8');
        online_status_dot.attr('title', 'offline');
        online_user_ids = online_user_ids.filter(id => id !== player_id);
    }
}
