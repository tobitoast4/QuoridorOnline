var clear_last_error_msg_started = false;
var last_error_msg = null;

async function getRandomPublicLobby() {
    try {
        var response = await fetch(window.location.origin + "/get_random_lobby", {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie("csrftoken", ""),
                'Content-Type': 'application/json'
            }
        });
        var data = await response.json();
        throwOnError(data);
        if (data.hasOwnProperty("error")) {
            showNotify("error", "", data["error"], 6);
        }
        if (data.hasOwnProperty("lobby_url")) {
            window.location.replace(data["lobby_url"]);
        }
    } catch (error) {
        showNewError(error);
    }
}

function showNewError(error) {
    // shows an error if it is not the same as last_error_msg
    // also sets an interval to reset last_error_msg back to null
    error = error.toString();
    if (last_error_msg != error) {
        last_error_msg = error;
        showNotify("error", "", error, 6);
    }
    if (!clear_last_error_msg_started) {  // ensures to only start one of these threads
        clear_last_error_msg_started = true;
        setTimeout(() => {
            last_error_msg = null;
            clear_last_error_msg_started = false;
        }, 5000);
    }
}

function throwOnError(json_obj) {
    // If there is the key "error" in a json_obj, show the value.
    // E.g.: {"error": "Player can not move here"} should show a notify and return true.
    // E.g.: {"status": "success"} should return false.
    if (Object.hasOwn(json_obj, "error")) {
        if (json_obj["error"].startsWith("JSONDecodeError")) {
            console.log(json_obj["error"]);
        } else {
            throw json_obj["error"];
        }
    }
}
