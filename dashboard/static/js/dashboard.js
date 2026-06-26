var server_url = null;
var labels = [];

// convert labels from string (e.g. "2024-02-23") to Date object)
for (let i = 0; i < labels_as_str.length; i++) {
    labels.push(new Date(labels_as_str[i]));
}
labels.push(new Date());  // add today's date to x axis

let currently_list_of_lobbies = null;

var jsonViewer = new JSONViewer();
document.querySelector("#selected_game_json_container").appendChild(jsonViewer.getContainer());

const lobbyLimitSelect = document.getElementById('lobbyLimitSelect');
let currentPageSize = new URLSearchParams(window.location.search).get('page_size');
if (currentPageSize) {
    lobbyLimitSelect.value = currentPageSize;
}

lobbyLimitSelect.addEventListener('change', function() {
    setPageSize(this.value);
});

const ctx = document.getElementById("lineChart").getContext("2d");
const lineChart = new Chart(ctx, {
    type: "line",
    data: {
        labels: labels,
        datasets: [
            {
                label: "Amount of games",
                data: data,
                fill: false,
                tension: 0.25,
                pointRadius: 1,
                pointHoverRadius: 5
            },
        ],
    },
    options: {
        responsive: true,
        scales: {
            x: {
                type: "time",
                time: {
                    unit: "day"
                }
            }
        },
        plugins: {
            zoom: {
                pan: {
                    enabled: true,
                    threshold: 10
                },
                zoom: {
                    wheel: {
                        enabled: true
                    },
                    pinch: {
                        enabled: true
                    },
                    drag: {
                        enabled: true,
                        backgroundColor: 'rgba(225,225,225,0.15)',
                        borderColor: 'rgba(225,225,225,0.4)',
                        threshold: 10,
                        mode: 'x'
                    },
                    mode: 'x'
                },
            },
            tooltip: {
                enabled: true
            }
        }
    }
});

document.getElementById('resetZoomBtn').addEventListener('click', function() {
    if (typeof lineChart.resetZoom === 'function') {
        lineChart.resetZoom();
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

        currently_list_of_lobbies = lobbies.filter(lobby => lobby.time_created.startsWith(date_formatted));
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
    let i = 0;
    currently_list_of_lobbies.forEach((lobby) => {
        if (currentPageSize && i > currentPageSize) {
            return;
        }
        i++;

        let link_to_game = "<td></td>";
        if (lobby.game) {
            link_to_game = `
                <td>
                    <a href='/game/${lobby.lobby_id}' target='_blank' style='color: black'>
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
        var response = await fetch("/dashboard/get_lobby/" + lobby_id, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        var data = await response.json();
        jsonViewer.showJSON(data["lobby"]);
    } catch (error) {
        console.log(error);
    }
}

function reloadDashboardWithDateOffset(daysBack) {
    var url = new URL(window.location);

    if (daysBack === null) {
        url.searchParams.delete('date_from');
        window.location.href = url;
        return;
    }

    const targetDate = new Date();
    targetDate.setDate(targetDate.getDate() - daysBack);

    const year = targetDate.getFullYear();
    const month = String(targetDate.getMonth() + 1).padStart(2, '0');
    const day = String(targetDate.getDate()).padStart(2, '0');
    const formattedDate = `${year}-${month}-${day}`;

    url.searchParams.set('date_from', formattedDate);
    window.location.href = url;
}

function setPageSize(pageSize) {
    var url = new URL(window.location);

    if (pageSize == "") {
        url.searchParams.delete('page_size');
        currentPageSize = pageSize;
    } else {
        url.searchParams.set('page_size', pageSize);
        currentPageSize = pageSize;
    }
    history.pushState({}, "", url);

    fillTableListOfGames();
}

async function deleteEmptyLobbies() {
    try {
        var response = await fetch(server_url + "dashboard/delete_empty_lobbies/" , {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie("csrftoken", ""),
                'Content-Type': 'application/json',
            }
        });
        await response.json();
    } catch (error) {
        console.log(error);
    }

    window.location = window.location;
}


// Initially show all games in the list
currently_list_of_lobbies = lobbies;
fillTableListOfGames();