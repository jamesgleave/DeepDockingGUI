function toggleLoadingScreen(turn_on){
    if (turn_on) {
        // console.log("Displaying loading screen...");
        document.getElementById("loading").style.visibility = "visible";
        
    }else{
        // console.log("Closing loading screen.");
        document.getElementById("loading").style.visibility = "hidden";
    }
}

// gets the username and password and attempts to setup the ssh connection
function setupConnection(){
    toggleLoadingScreen(true);

    // Setting up the connection
    let user = document.getElementById("username").value;
    let pwd = document.getElementById("pwd").value;
    console.log("setting up connection...");
    // console.log("\t"+user+"\n\t"+ pwd);

    // async post request:
    $.ajax({
        type: "POST",
        url: "/sshConnect",
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({'user': user, 'pwd': pwd}),
        success: function(data, status, settings){
            toggleLoadingScreen(false);
            console.log("successful login...");
            console.log(data, status, settings)
        },
        error: function(res, opt, err){ // Handling errors (2 possible -> no VPN or Invalid creds)
            console.log(res, opt, err);
            if (res.status === 401){
                // Creating the error display box if it doesnt exist
                if (res.responseText === "creds"){
                    let errorElm = document.getElementById("errorText")
                    if (! errorElm){ // if it doesnt exist we must first create it
                        errorElm = document.createElement("p")
                        errorElm.id = "errorText"

                        let formElm = document.getElementById("cred-form");
                        formElm.insertBefore(errorElm, formElm.firstChild);
                    }
                    errorElm.textContent = "Incorrect credentials!"

                } else if (res.responseText === "vpn"){
                    let errorElm = document.getElementById("errorText")
                    if (! errorElm){ // if it doesn't exist we must first create it
                        errorElm = document.createElement("p")
                        errorElm.id = "errorText"

                        let formElm = document.getElementById("cred-form");
                        formElm.insertBefore(errorElm, formElm.firstChild);
                    }
                    errorElm.textContent = "Is your VPN on?"
                }
            } else{
                alert("Something wrong...")
            }
            toggleLoadingScreen(false);
        }
      }).done(function(response) {
        console.log(response);
        window.location = "/main" // redirects user to the main page
    });
    
}

document.getElementById('login-btn').addEventListener('click', setupConnection);

document.querySelectorAll('input').forEach( el => {
    el.addEventListener('keydown', e => {
        console.log(e.key);
        if(e.key === 'Enter') {
            let nextEl = el.nextElementSibling;
            if(nextEl.nodeName === 'INPUT') {
                nextEl.focus();
            }else if (nextEl.nodeName === 'BUTTON') {
                nextEl.focus();
            } else {
                alert("done");
            }
        }
    })
});