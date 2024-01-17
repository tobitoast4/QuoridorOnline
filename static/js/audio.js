var cookie_name_play_audio = "play_audio";
var cookie_name_audio_file = "audio_file";
setButtonIcon();

function toggleAudio() {
    if (getCookie(cookie_name_play_audio, "") == "true") {
        setCookie(cookie_name_play_audio, "false");
    } else {
        setCookie(cookie_name_play_audio, "true");
        playAudio();
    }
    setButtonIcon();
}

function setButtonIcon() {
    if (getCookie(cookie_name_play_audio, "") == "true") {
        $("#button-sound-mute").html('<i class="fa fa-volume-up" style="font-size: 32px" aria-hidden="true"></i>');
    } else {
        $("#button-sound-mute").html('<i class="fa fa-volume-off" style="font-size: 32px" aria-hidden="true"></i>');
    }
}

function playAudio() {
    if (getCookie(cookie_name_play_audio, "") == "") {
        // set cookie initially if not exists
        setCookie(cookie_name_play_audio, "true");
        setCookie(cookie_name_audio_file, "normal_clack.wav");
    }
    if (getCookie(cookie_name_play_audio, "false") == "true") {
        var audio = new Audio('/static/res/' + getCookie(cookie_name_audio_file, ""));
        audio.play();
    }
}

function setCookie(cookie_name, value) {
    document.cookie = "" + cookie_name + "=" + value + "; path=/";
}

function getCookie(cookie_name, default_value) {
    var name = cookie_name + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return default_value;
}