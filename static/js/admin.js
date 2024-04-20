//var lobbies_in_group = undefined;
//var labels_as_str = undefined;
//var data = undefined;
var labels = [];
// convert labels from string (e.g. "2024-02-23") to Date object)
for (let i = 0; i < labels_as_str.length; i++) {
    labels.push(new Date(labels_as_str[i]));
}
labels.push(new Date());  // push the date of today, to have todays date on the most right

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
        console.log();

        let table = $(`<table></table>`);

        lobbies_in_group[date_formatted].forEach(async (lobby_id) => {
            table.append(`
                <tr>
                    <td>
                        <a href="#" onclick="getLobbyJson('${lobby_id}')">${lobby_id}</a>
                    </td>
                </tr>
            `);
        });

        $('#list_of_games_container').html(table);
    }
});


async function getLobbyJson(lobby_id) {
    try {
        var response = await fetch(server_url + "get_lobby_json/" + lobby_id, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        var data = await response.json();
        console.log(data);
        data_str = JSON.stringify(data, null, 4);
        $('#selected_game_json_container').html(data_str);
    } catch (error) {
    }
}