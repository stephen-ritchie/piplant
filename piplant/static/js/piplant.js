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