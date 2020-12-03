function deleteDevice(deviceId) {
    var result = confirm("Are you sure you want to delete this device?");
    if (result) {
        var xhttp = new XMLHttpRequest();
        $.ajax({
            url: location.origin + "/api/v1/devices/" + deviceId,
            type: "delete",
            data: {vals: ''},
            success: function(response) {
                if (response.redirect) {
                    window.location.href = response.redirect_url;
                }
            },
            error: function(response) {
                alert("Could not delete device");
            },
        });
    }
}

function deleteSchedule(scheduleId) {
    var result = confirm("Are you sure you want to delete this schedule?");
    if (result) {
        var xhttp = new XMLHttpRequest();
        $.ajax({
            url: location.origin + "/api/v1/schedules/" + scheduleId,
            type: "delete",
            data: {vals: ''},
            success: function(response) {
                location.reload();
            },
            error: function(response) {
                alert("Could not delete schedule");
            }
        });
    }
}

function getChartDataFromAPI(url) {
    $.ajax({
        url: url,
        type: "get",
        data: {vals: ''},
        success: function(response) {
            JSON.stringify(response);
            for (var prop in response) {
                renderChart(response[prop].title, response[prop]);
            }
        },
    });
}

function renderChart(title, chartData) {
    var canvas = document.createElement('canvas');
    canvas.id = title;
    canvas.width = 1000;
    canvas.height = 600;
    
    var body = document.getElementById("charts");
    body.appendChild(canvas);

    var ctx = document.getElementById(title).getContext("2d");

    var chart = new Chart(ctx, chartData);
}
