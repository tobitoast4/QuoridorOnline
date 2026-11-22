function getCookie(cookieName, defaultValue) {
    const prefix = `${cookieName}=`;
    const cookies = decodeURIComponent(document.cookie).split(";");
    for (const cookie of cookies) {
        const trimmedCookie = cookie.trim();
        if (trimmedCookie.startsWith(prefix)) {
            return trimmedCookie.substring(prefix.length);
        }
    }
    return defaultValue;
}

function get_script_json_value(script_id) {
    let value = document.getElementById(script_id).textContent;
    try {
        return JSON.parse(value);
    } catch (e) {
        console.error('Error parsing JSON from script element:', script_id);
        return null;
    } 
}
