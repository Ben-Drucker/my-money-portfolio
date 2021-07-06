function largeDiv(div_id) {
    let divObject = document.getElementById(div_id);
    if (divObject.hidden) {
        divObject.hidden = false;
        opacityAnimation(divObject, 0, 1, 0.1)
    }
    else {
        opacityAnimation(divObject, 1, 0, 0.1)

    }
}

function plaid_init() {
    (async function pub($) {
            $.post('/main/plaid_public_token', { 
                public_token: JSON.parse(JSON.stringify(await $.post('/main/plaidinit'))).public_token }, () => {
                console.log("success!");
                let xhttp = new XMLHttpRequest();
                xhttp.onreadystatechange = function () {
                    if (this.readyState == 4 && this.status == 200) {
                        let bankResults = JSON.parse(this.responseText);
                        displayBankResults(bankResults);
                    }
                }
                xhttp.open("GET", "/main/plaid_parser", true);
                xhttp.send();
            })
    })(jQuery)
}



/* Production / Development Env Below */
// (async function get_token($) {
//     var handler = Plaid.create({
//         // Create a new link_token to initialize Link
//         token: (await $.post('/main/plaidinit')).link_token,
//         onSuccess: function (public_token, metadata) {
//             // Send the public_token to your app server.
//             // The metadata object contains info about the institution the
//             // user selected and the account ID or IDs, if the
//             // Select Account view is enabled.
//             $.post('/main/plaid_public_token', {
//                 public_token: public_token,
//             }, function () {
//                 console.log("success!");
//                 let xhttp = new XMLHttpRequest();
//                 xhttp.onreadystatechange = function () {
//                     if (this.readyState == 4 && this.status == 200) {
//                         let bankResults = JSON.parse(this.responseText);
//                         displayBankResults(bankResults);
//                     }
//                 }
//                 xhttp.open("GET", "/main/plaid_parser", true);
//                 xhttp.send();
//             });
//         },
//         onExit: function (err, metadata) {
//             // The user exited the Link flow.
//             if (err != null) {
//                 messageHider("You encountered an error and/or your link was not made.", 10)
//             }
//         },
//     });
//     handler.open();
// })(jQuery);



function messageHider(message_text, duration_secs) {
    let message_hider = document.getElementById("message_hider");
    let messages = document.getElementById("messages");
    messages.innerHTML = message_text;
    message_hider.hidden = false;
    opacityAnimation(message_hider, 0, 1, 0.5);
    setTimeout(function () {
        opacityAnimation(message_hider, 1, 0, 0.5);
    }, 1000 * duration_secs);
    message_hider.hidden = true;
    messages.innerHTML = "";
}

function opacityAnimation(object, start_opacity, end_opacity, duration_secs) {
    let numFrames = duration_secs * 60;
    let opacityChange = end_opacity - start_opacity;
    let opacityFrameDiff = opacityChange / numFrames;
    let framesCompleted = 0;
    let newOpacity;
    if (object.style.opacity == "") {
        object.style.opacity = "0";
    }
    let interval = setInterval(function () {
        framesCompleted++;
        newOpacity = parseFloat(object.style.opacity) + opacityFrameDiff;
        object.style.opacity = newOpacity;
        if (framesCompleted == numFrames) {
            clearInterval(interval);
            if (opacityChange < 0) {    //ending animation
                object.hidden = true;
            }
        }
    }, 16);
}

function displayBankResults(bankResults) {
    let results = document.getElementById("results");
    let accounts_array = bankResults.accounts;
    if (accounts_array.length == 0) {
        results.innerHTML = "Sorry. No bank accounts were found for that institution.";
        return
    }
    let form = document.getElementById("select_bank_form");
    accounts_array.forEach((account) => {
        form.innerHTML =
            "<input type='checkbox' id=" + account.id_name + " name=" + account.id_name + " value=" + account.display_name +
            "<label for=" + account.id_name + " >" + account.display_name + "<span class='green'> (Balance: $" + account.bal + ") </span> </label><br>\
            </input>" + form.innerHTML;
    });
    form.style.display = "inline-block";
    results.hidden = false;
    document.getElementById("resultsHeader").hidden = false;
}

var net_worth

window.addEventListener("load", function () {
    function sendData() {
        const xhttp = new XMLHttpRequest();
        const form_data = new FormData(form);

        xhttp.onreadystatechange = function () {
            if (this.readyState == 4 && this.status == 200) {
                let server_data = JSON.parse(this.responseText)
                let msg = server_data.message
                let net_worth = parseFloat(server_data.net_worth)
                document.getElementById("selected_accounts").innerHTML = msg
                document.getElementById("net_worth").innerHTML = "Your net worth: <span style='border: solid black 6px; border-radius: 20px; padding: 10px; whitespace: nowrap'>$ " + net_worth + "</span>"
                document.getElementById('splashscreen').style.display = 'none';
                document.getElementById('replacementdata').style.display = 'grid';
                document.getElementById('port_vis').style.borderStyle = 'solid';
                document.getElementById('port_vis').style.borderColor = 'black';
                opacityAnimation(document.getElementById('bank_popout'), 1, 0, 0.1);
                data.labels = server_data.pie_labels
                data.datasets[0].data = server_data.pie_vals
                data_debt.labels = server_data.pie_labels_debt
                data_debt.datasets[0].data = server_data.pie_vals_debt
                console.log(data, data_debt)
            }
        }

        xhttp.addEventListener("error", function (event) {
            alert('Oops! Something went wrong.');
        });

        xhttp.open("POST", "/main/select_bank_accounts");
        xhttp.send(form_data);
    }

    let form = document.getElementById("select_bank_form");
    form.addEventListener("submit", function (event) {
        event.preventDefault();
        sendData();
    });
});