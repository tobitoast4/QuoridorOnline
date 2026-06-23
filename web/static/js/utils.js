function get_script_json_value(script_id) {
    let value = document.getElementById(script_id).textContent;
    try {
        return JSON.parse(value);
    } catch (e) {
        console.error('Error parsing JSON from script element:', script_id);
        return null;
    } 
}