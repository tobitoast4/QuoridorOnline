var cookie_name_audio_file = "audio_file";

// initially set button size
let button_size_value = getSliderValue("buttonsize");
setButtonSizes(button_size_value);

// initially set audio file
setCookie(cookie_name_audio_file, "normal_clack.wav");


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

function openSettingsMenu(){
    $('#settings_overlay').removeAttr("style");

    let audio_level = getSliderValue("audio");
    $('#slider-audio').attr("value", audio_level);
    if (audio_level == 0) {
        $('#slider-audio-value').html("off");
    } else {
        $('#slider-audio-value').html(`${audio_level} %`);
    }

    let buttonsize_level = getSliderValue("buttonsize");
    $('#slider-buttonsize').attr("value", buttonsize_level);
    $('#slider-buttonsize-value').html(`${buttonsize_level} %`);

    let zoom_level = getSliderValue("zoom");
    $('#slider-zoom').attr("value", zoom_level);
    $('#slider-zoom-value').html(`${zoom_level} %`);
}

function closeSettingsMenu(){
    $('#settings_overlay').attr("style", "display:none");
}

function setButtonSizes(value) {
    // set button sizes initially
    // value should be something between 0 and 150
    ["button-inspect-previous-round", "button-inspect-next-round", "button-inspect-current-round",
    "button-place-walls", "button-settings", "button-toggle-wall-color"].forEach(button_id => {
        const initial_button_size = 81;
        const initial_font_size = 16;
        const initial_icon_size = 32;
        const initial_padding = 18;
        let new_size = initial_button_size * value / 100;
        let new_font_size = initial_font_size * (value / 100);
        let new_padding = initial_padding * (value / 100);
        let new_icon_size = initial_icon_size * (value / 100);
        $(`#${button_id}`).attr("style", `width: ${new_size}px; height: ${new_size}px;
                            font-size: ${new_font_size}px; padding: ${new_padding}px`);
        $(`#${button_id}-icon`).attr("style", `font-size: ${new_icon_size}px`);
    });
}

function setSliderValue(slider_name, value) {
    // slider_name should be audio / button-size / zoom
    let cookie_name = `${slider_name}_level`;
    setCookie(cookie_name, value);
}

function getSliderValue(slider_name) {
    // slider_name should be audio / buttonsize / zoom
    let cookie_name = `${slider_name}_level`;
    let cookie_value = getCookie(cookie_name, -1);
    if (cookie_value == -1) {  // set cookie initially if not exists
        setCookie(cookie_name, 100);
        return 100;
    }
    return cookie_value;
}

function toggleWallColor() {
    if (getCookie("wall_color_as_player_color", "") == "true") {
        setCookie("wall_color_as_player_color", "false");
    } else {
        setCookie("wall_color_as_player_color", "true");
    }
}


// TODO: Remove this old audio functionality
function toggleAudio() {
    if (getCookie(cookie_name_play_audio, "") == "true") {
        setCookie(cookie_name_play_audio, "false");
    } else {
        setCookie(cookie_name_play_audio, "true");
        playAudio();
    }
}

function playAudio() {
    let audio_level = getSliderValue("audio");
    var audio = new Audio('/static/res/' + getCookie(cookie_name_audio_file, ""));
    audio.volume = (audio_level / 100);
    audio.play();
}
