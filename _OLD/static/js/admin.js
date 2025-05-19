//var lobbies_in_group = undefined;
//var labels_as_str = undefined;
//var data = undefined;
var labels = [];
// convert labels from string (e.g. "2024-02-23") to Date object)
for (let i = 0; i < labels_as_str.length; i++) {
    labels.push(new Date(labels_as_str[i]));
}
labels.push(new Date());  // add today's date to x axis

let currently_list_of_lobbies = null;

var jsonViewer = new JSONViewer();
document.querySelector("#selected_game_json_container").appendChild(jsonViewer.getContainer());

const ctx = document.getElementById("lineChart").getContext("2d");
const lineChart = new Chart(ctx, {
    type: "bar",
    data: {
    labels: labels,
    datasets: [
            {
                label: "Amount of games",
                data: data,
            },
        ],
    },
    options: {
        scales: {
            x: {
                type: "time",
            }
        },
        plugins: {
            tooltip: {
                enabled: false
            }
        }
    }
});

// Add click event listener to the chart
document.getElementById("lineChart").addEventListener("click", function(event) {
    const activePoints = lineChart.getElementsAtEventForMode(event, 'point', lineChart.options);
    if (activePoints.length > 0) {
        const clickedDatasetIndex = activePoints[0].datasetIndex;
        const clickedDataIndex = activePoints[0].index;
        const value = lineChart.data.datasets[clickedDatasetIndex].data[clickedDataIndex];
        const label = lineChart.data.labels[clickedDataIndex];
        let date = label.toISOString();
        let date_formatted = date.substring(0, date.indexOf('T'));

        currently_list_of_lobbies = lobbies_in_group[date_formatted];
        fillTableListOfGames();
    }
});

function fillTableListOfGames() {
    let table = $(`
        <table>
            <thead>
                <tr>
                    <th>Lobby ID</th>
                    <th>Time created</th>
                    <th>Amount of players</th>
                    <th></th>
                </tr>
            </thead>
        </table>
    `);
    let table_body = $(`<tbody></tbody>`)
    currently_list_of_lobbies.forEach((lobby) => {
    let link_to_game = "<td></td>";
        if (!isNaN(lobby.amount_players)) {
            link_to_game = `
                <td>
                    <a href='${server_url}game/${lobby.lobby_id}' target='_blank' style='color: black'>
                        <i class="fa fa-external-link" aria-hidden="true"></i>
                    </a>
                </td>
            `;
        }
        table_body.append(`
            <tr id="row-${lobby.lobby_id}">
                <td>
                    <div style="cursor:pointer; color:#551a8b; text-decoration:underline;"
                         onclick="getLobbyJson('${lobby.lobby_id}')">
                            ${lobby.lobby_id}
                    </div>
                </td>
                <td>${lobby.time_created}</td>
                <td>${lobby.amount_players}</td>
                ${link_to_game}
            </tr>
        `);
    });
    table.append(table_body);

    $('#list_of_games_container').html(table);
    $('#amount_of_lobbies_in_list').html("(" + currently_list_of_lobbies.length + ")");
}


async function getLobbyJson(lobby_id) {
    fillTableListOfGames();  // to remove the old selected color
    $('#row-' + lobby_id).attr("style", "background-color: #D6EEEE");
    try {
        var response = await fetch(server_url + "get_lobby_json/" + lobby_id, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        var data = await response.json();
        jsonViewer.showJSON(data);
    } catch (error) {
        console.log(error);
    }
}

// Initially show all games in the list
let list_of_all_lobbies = [];
Object.entries(lobbies_in_group).forEach(([k,value]) => {
    value.forEach((lobby) => {
        list_of_all_lobbies.push(lobby);
    });
});
currently_list_of_lobbies = list_of_all_lobbies;
fillTableListOfGames();