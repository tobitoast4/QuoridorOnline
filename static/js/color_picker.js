document.addEventListener("mouseup", function(event) {
    if (event.target.className.includes("color-picker-color")) {
        $("#color-picker").fadeOut(400);
    } else if (event.target.id != "color-picker" && event.target.id != "color-picker-icon") {
        $("#color-picker").fadeOut(100);
    }
});

function openColorPicker(){
    let offset = $('#players-color').offset();
    $('#color-picker').attr("style", `top: ${offset.top - 128}px; left: ${window.innerWidth - 96}px`);
    $("#color-picker").fadeIn(300);
    $("#color-picker").draggable()
    console.log(offset);
}
