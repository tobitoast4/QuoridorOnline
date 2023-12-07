
function refreshPlayerStats(){
    $('#stats_grid').empty();
    players.forEach(player => {
        var player_stats = $('<div class="two-col-grid"></div>');
        player_stats.append('<h2 style="text-align: right;">' + player.name + '</h2>');
    
        var wall_box = $('<div id="remaining_walls_container" style="display: flex; gap: 3px; padding: 20px"></div>');
        for (var i = 0; i < player.amount_walls_left; i++) {
            wall_box.append('<div style="background-color: ' + player.color + '; width: 5px; height: 24px;"></div>');
        }
        player_stats.append(wall_box);
        $('#stats_grid').append(player_stats);
    });
}