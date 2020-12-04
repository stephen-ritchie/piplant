function updateForm(value) {
    if (value === "tp_link_smart_plug") {
        let input = document.createElement("input");
        input.className = "form-control";
        input.placeholder = "IP Address";
        input.type = "text";
        input.name = "ip_address";
        input.id = "ip_address";
        input.required = true;

        let form = document.getElementById("additional-inputs");
        form.appendChild(input);
    } else if (value === "ds18b20") {
        let input = document.createElement("input");
        input.className = "form-control";
        input.placeholder = "Serial Number";
        input.type = "text";
        input.name = "serial_number";
        input.id = "serial_number";
        input.required = true;

        let form = document.getElementById("additional-inputs");
        form.appendChild(input);
    } else {
        if (document.contains(document.getElementById("ip_address"))) {
            document.getElementById("ip_address").remove();
        }
        if (document.contains(document.getElementById("serial_number"))) {
            document.getElementById("serial_number").remove();
        }
    }
}