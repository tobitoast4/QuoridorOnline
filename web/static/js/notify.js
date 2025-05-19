var counter = 0;

function showNotify(notify_type, title, description, timeout) {
    /* Shows a toast alert on the bottom right.
    notify_type should either be "error" or "success".
    */
    var notify_holder = document.getElementById("notify-holder");
    var htmlObject = document.createElement('div');

    var icon = `fas fa-triangle-exclamation`;
    if (notify_type == "success") icon = `far fa-circle-check`;

    var title_element = "";
    if (title != ""){
        title_element = "<strong>" + title + ": </strong>";
    }
    htmlObject.innerHTML = `
        <div class="alert ` + notify_type + `">
            <i style="margin-right: 5px" class="` + icon + `"></i>
            <span class="close-btn" id="close-button-` + counter + `">&times;</span>
            ` + title_element + description + `
        </div>
    `;

    notify_holder.appendChild(htmlObject);

    // Add the close functionality
    var close = document.getElementById("close-button-" + counter);
    close.onclick = function(){ removeNotify(close) };

    // Remove notify automatically after timeout seconds
    setTimeout(function() {
        removeNotify(close);
    }, timeout * 1000);

    counter++;
}

function removeNotify(close_button_element){
    var div = close_button_element.parentElement;
    div.style.opacity = "0";
    setTimeout(function() {
        div.style.display = "none";
    }, 600);
}