
async function updatePlayerName() {
    let new_player_name = $('#input-players-name').val();

    try {
        var response = await fetch(server_url + "rename_player", {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie("csrftoken", ""),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "new_user_name": new_player_name
            })
        });
        var data = await response.json();
        throwOnError(data);
        showNotify("success", "", data["status"], 6);
        $("#button_update_player_name").removeAttr("style");
        $("#button_update_player_name_icon").removeAttr("style");
    } catch (error) {
        showNewError(error);
    }
}

async function updateColor(new_color) {
    try {
        var response = await fetch(server_url + "change_color", {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie("csrftoken", ""),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "lobby_id": current_lobby_id,
                "new_color": new_color
            })
        });
        var data = await response.json();
        throwOnError(data);
        showNotify("success", "", data["status"], 6);
        $('#players-color').attr("style", "background-color: " + data["color"]);
    } catch (error) {
        showNewError(error);
    }
}