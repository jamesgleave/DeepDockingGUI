function enableValidTabs(projectInfo){
    // Enables or disables tabs depending on the current state.
    // starting off will all disabled:
    document.querySelectorAll('.tablinks').forEach(e => {
        // The start tab will always be enabled.
        if (e.id === "startRBtn"){
            e.title = '';
            e.disabled = false;
        } else {
            e.title = 'Not yet :)';
            e.disabled = true;
        }
    });

    // Only enabling tabs if we are logged in to the cluster
    if (projectInfo.logged_in){
        // Getting progress info: to decide if we can display the next tabs
        $.ajax({
            type: "GET",
            url: "/progressData",
            dataType: 'json',
            success: function (data, status, settings) {
                var models_T = document.getElementById('modelsBtn');
                var prog_T = document.getElementById('progBtn');
                var top_T = document.getElementById('topScoringBtn');

                if (data.currentInfo.iter > 1){
                    top_T.disabled = false;
                    models_T.disabled = false;
                    top_T.title = '';
                    models_T.title = '';
                }else if (data.currentInfo.phase >= 4){
                    models_T.disabled = false;
                    models_T.title = '';
                }
                // enabling if we have a project loaded which is the case if it is successful
                prog_T.disabled = false;
                prog_T.title = '';
            },error: function(res, opt, err){
                console.log('No data to show');
            }
        });
    }
}

function enableValidBtns(projectInfo){
    // Enabling selecting a project iff there are projects available and are logged in.
    console.log(projectInfo);
    if (projectInfo.logged_in){
        document.getElementById('newProjBtn').disabled = false;

        if (projectInfo.projects_list && projectInfo.projects_list.length > 0){
            document.getElementById('loadProjBtn').disabled = false;

            // Looping through and adding those names to the form to be selected
            var form = document.getElementById('load-project-cascade');

            // clearing data first:
            while (form.firstChild)
                form.removeChild(form.lastChild);

            // Adding each of the projects to the list:
            for (p_name of projectInfo.projects_list) {
                var e_name = document.createElement('option');
                e_name.text = p_name.split('.json')[0];
                form.appendChild(e_name);
            }
        }
    }

    // Update specs is enabled when we have selected a project.
    if (projectInfo.specs){

        // Can only get progress data if we are logged in and loaded the project
        if (projectInfo.logged_in){
            // Starting off by disabling all phases
            document.querySelectorAll('#phaseRunner > button:not(.largeBtn)').forEach(e => e.disabled = true);
            document.getElementById('startPhaseFinal').disabled = true;

            // Phase buttons
            $.ajax({
                type: "GET",
                url: "/progressData",
                dataType: 'json',
                success: function (data, status, settings) {
                    document.getElementById('deleteProjBtn').disabled = false;
                    document.getElementById('updateSpecsBtn').disabled = false;
                    document.getElementById('runAllPhases').disabled = false;
                    document.getElementById('resetPhase').disabled = false;


                    // // Switching on the currently running phase button
                    // // TODO: fix this
                    // const curr_phase = data.currentInfo.phase;
                    // const completed = data.is_idle; // if false -> stil running
                    // if (curr_phase == 0){
                    //     document.getElementById('startPhase1').disabled = false;
                    //     if (data.currentInfo.iter > 1)
                    //         document.getElementById('startPhaseFinal').disabled = false;
                    // }else {
                    //     document.getElementById('startPhase'+ (curr_phase)).disabled = false;
                    // }
                    
                    // // If it is done then we also show the next phase:
                    // if  (completed){
                    //     if (curr_phase < 5)
                    //         document.getElementById('startPhase'+ (curr_phase+1)).disabled = false;
                    //     else
                    //         document.getElementById('startPhase1').disabled = false;
                    //         if (data.currentInfo.iter > 1)
                    //             document.getElementById('startPhaseFinal').disabled = false;
                    // }
                }
            });
        }
    }
}

function updateInfoCenter(projectInfo){
    // updates text in the info center to help user know what to do
    var info_center = document.querySelector('#infoCenter > p');
    
    if (projectInfo.logged_in){
        if (projectInfo.specs){ // will be none if no project is available
            if (projectInfo.b_status !== 'fetching')
                info_center.innerText = "Project has been loaded successfully!";
            else
                info_center.innerText = "Please load a project...";
        }
        else
            info_center.innerText = "Please create a project...";
    }else
        info_center.innerText = "You are not connected to the cluster!\n\nPlease go back to the login page.";
        /*
        link = document.createElement("a")
        link.innerText = "login"
        link.href = "/"
        info_center.append(link)
        */
}

function displayProjectInfo(projectInfo){
    var specs = projectInfo.specs;
    var inputs = document.querySelectorAll('#specs input');
    updateInfoCenter(projectInfo);

    if (specs){
        // Only changed if we have a project loaded
        if (projectInfo.b_status && projectInfo.b_status !== 'fetching'){
            // Changing name:
            document.getElementById('curr_project_name').innerText = "Current Project: " + specs.log_file.project_name

            // Changing placeholders for inputs:
            for (input of inputs)
                // The name of the element is the same as its dictionary key:
                input.value = specs.specifications[input.id];
        }else
            inputs.forEach(i => i.placeholder = 'No data...');

            
        enableValidTabs(projectInfo);
    }
    enableValidBtns(projectInfo);
}

function updateProjectInfo(project_name){
    toggleLoadingScreen(true);
    var args = "projectName=" + project_name;
    $.ajax({
        type: "GET",
        url: "/getProjectInfo?" + args,
        dataType: 'json',
        success: function (data, status, settings) {
            displayProjectInfo(data);
        },
        error: function (res, opt, err) {
            if (res.status == 400) {
                alert('BAD REQUEST: Missing/invalid project specifications. Please try again.');

            } else{
                alert('Error\n' + res.status + ': ' + err);
            }
            console.log(res.status);
        }
    }).done(function (response) {
        toggleLoadingScreen(false);
    });
}

function boot(){
    $.ajax({
        type: "GET",
        url: "/getProjectInfo?projectName=undefined",
        dataType: 'json',
        success: function (data, status, settings) {
            displayProjectInfo(data); //if null it displays 'nodata...'
        },
        error: function (res, opt, err) {
            if (res.status == 400) {
                alert('BAD REQUEST: Missing/invalid project specifications. Please try again.');

            } else{
                alert('Error\n' + res.status + ': ' + err);
            }
            
            console.log(res.status);
        }
    }).done(function (response) {
        toggleLoadingScreen(false);
    });
}

function loadProject(project_name){
    var args = 'projectName='+ project_name;
    toggleLoadingScreen(true);
    $.ajax({
        type: "POST",
        url: "/loadProject?" + args,
        dataType: 'json',
        success: function (data, status, settings) {
            console.log('Project is loaded!');
            updateProjectInfo(project_name);
        },
        error: function (res, opt, err) {
            if (res.status == 400) {
                alert('BAD REQUEST: Missing/invalid project specifications. Please try again.');

            } else if (res.status == 404){
                alert('Error 404: The project you are looking for was not found on the cluster');

            } else{
                alert('Error\n' + res.status + ': ' + err);
            }
            
            console.log(res.status);
        }
    }).done(function (response) {
        toggleLoadingScreen(false);
        // closing popup:
        togglePopup('loadProject-popup', false);
    });
}

// load project POPUP btn
document.getElementById('loadProjBtn').onclick = function(){
    togglePopup('loadProject-popup', true);
};

// close popup btn:
document.querySelector('#loadProject-popup > div > a').onclick = function(){
    togglePopup('loadProject-popup', false);
};

// Load Project btn
document.getElementById('loadSelectedProjectBtn').onclick = function(){
    // Getting the name of the project selected from dropdown.
    var selectedP_I = document.querySelector('#load-project-cascade').selectedIndex;
    var project_name = document.querySelectorAll('#load-project-cascade option')[selectedP_I].textContent;
    toggleLoadingScreen(true);
    loadProject(project_name);
};

// new project btn
document.getElementById('newProjBtn').onclick = function(){
    togglePopup('newProject-popup', true);
};

// close popup btn:
document.querySelector('#newProject-popup > div > a').onclick = function(){
    togglePopup('newProject-popup', false);
};

// Opening extra parameters popup for job submission
document.querySelector('#addExtraParamBtn').onclick = function(){
    togglePopup('extraParam-popup', true);
}

// Saving said parameters and closing
document.querySelector('#saveExtraParam').onclick = function(){
    togglePopup('extraParam-popup', false);
}

// closing said popup 
document.querySelector('#extraParam-popup > div > a').onclick = function(){
    // Clearing the data (no saving)
    document.querySelector('#slurm_headers').value = '';

    // closing popup
    togglePopup('extraParam-popup', false);
}

// Submit button for creating a new project:
document.querySelector('#submitNewProjBtn').onclick = function(){
    // Check to see if everything that is required was filled in:
    var requiredInputs = document.querySelectorAll('#newProject-popup .required');
    var completed_form = true;
    for (e of requiredInputs){
        var title_el = e.parentElement.querySelector('h4');
        if (!e.value){ // empty string is falsey
            title_el.style.color = '#FF7373';
            completed_form = false;
        } else{
           title_el.style.color = '#DFFFE6';
        }
    }

    if (completed_form){
        toggleLoadingScreen(true);
        // Gathering all the form values into an argument json:
        var inputs = document.querySelectorAll('#newProject-popup input');
        var form_info = {};

        for (let i = 0; i < inputs.length; i++) {
            const input = inputs[i];
            // The ids are named after their dictionary keys
            var i_key = input.id.split('-popup')[0];
            form_info[i_key] = (input.value) ? input.value : input.placeholder;
        }
        // Extra slurm headers:
        var headers = document.querySelector('#slurm_headers');
        var h_key = headers.id.split('-popup')[0];

        form_info[h_key] = (headers.value) ? headers.value.split('\n') : [];

        console.log(form_info);

        $.ajax({
            type: "POST",
            url: `/newProject?`,
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(form_info),
            success: function (data, status, settings) {
                console.log('Project is created!');
                updateProjectInfo(data.project_name);
            },
            error: function (res, opt, err) {
                if (res.status == 400) {
                    alert('BAD REQUEST: Missing/invalid project specifications. Please try again.');

                } else{
                    alert('Error\n' + res.status + ': ' + err);
                }

                console.log(res.status);
            }
        }).done(function (response) {
            toggleLoadingScreen(false);
            // closing popup:
            togglePopup('newProject-popup', false);
        });
    }else
        console.log('form incomplete');
}

function callScriptRunner(args, callback, ...c_args){
    toggleLoadingScreen(true);
    $.ajax({
        type: "POST",
        url: `/runScripts?${args}`,
        dataType: 'json',
        success: function (data, status, settings) {
            console.log('Ran script', data);
            if (data.script == "delete_project"){
                console.log('Project deleted reloading...');
                document.location.reload();
            }
        },
        error: function (res, opt, err) {
            alert('Error\n' + res.status + ': ' + err);
        }
    }).done(function (response) {
        toggleLoadingScreen(false);
        callback(...c_args);
    });
}

function confirmChoice(promptText, paragraphText, buttonText, callback, arg){
    togglePopup('popupPrompt', true);
    // Changing prompt text
    document.getElementById('promptText').innerHTML = promptText;

    // Changing paragraph text
    document.querySelector('#popupPrompt p').innerHTML = paragraphText;

    // Changing button text
    var btn = document.getElementById('promptBtn');
    btn.innerHTML = buttonText;
    
    // Changing callback of btn:
    btn.onclick = function(){
        if (callback)
            callback(arg);
        
        // Closing the popup:
        togglePopup('popupPrompt', false);
    };
}

// close prompt popup:
document.querySelector('#popupPrompt .closePopupBtn').onclick = function(){
    togglePopup('popupPrompt', false);
};

// Delete project btn
document.getElementById('deleteProjBtn').onclick = function(){
    // Launching confirmation before running 
    confirmChoice("Are you sure?", "You won't be able to recover it...", "Delete Project", callScriptRunner, 'script=delete_project');
};

// resets the current Phase
document.getElementById('resetPhase').onclick = function(){
    // Launching confirmation before running 
    confirmChoice("Are you sure?", "This will delete all data for the current or previous phase.", "Reset Last Phase", callScriptRunner, 'script=reset_phase');
};

// run ALL phases btn
document.getElementById('runAllPhases').onclick = function(){
    // With callback to display submission confirmation
    callScriptRunner('script=phase_a', confirmChoice, 'Request Submitted!', 
        "This might take a while to show up, check your cluster if it is pending.", "Okay!");
};

// run phase 1
document.getElementById('startPhase1').onclick = function(){
    callScriptRunner('script=phase_1', confirmChoice, 'Request Submitted!', 
        "This might take a while to show up, check your cluster if it is pending.", "Okay!");
};

// run phase 2
document.getElementById('startPhase2').onclick = function(){
    callScriptRunner('script=phase_2', confirmChoice, 'Request Submitted!', 
        "This might take a while to show up, check your cluster if it is pending.", "Okay!");
};

// run phase 3
document.getElementById('startPhase3').onclick = function(){
    callScriptRunner('script=phase_3', confirmChoice, 'Request Submitted!', 
        "This might take a while to show up, check your cluster if it is pending.", "Okay!");
};

// run phase 4
document.getElementById('startPhase4').onclick = function(){
    callScriptRunner('script=phase_4', confirmChoice, 'Request Submitted!', 
        "This might take a while to show up, check your cluster if it is pending.", "Okay!");
};

// run phase 5
document.getElementById('startPhase5').onclick = function(){
    callScriptRunner('script=phase_5', confirmChoice, 'Request Submitted!', 
        "This might take a while to show up, check your cluster if it is pending.", "Okay!");
};

// Run Final Phase btn
document.getElementById('startPhaseFinal').onclick = function(){
    callScriptRunner('script=phase_f', confirmChoice, 'Request Submitted!', 
        "This might take a while to show up, check your cluster if it is pending.", "Okay!");
};

// Update specs btn
document.getElementById('updateSpecsBtn').onclick = function(){
    // Gathering all the form values into an argument string:
    var inputs = document.querySelectorAll('#specs input');
    var args = 'script=update_specs'

    for (let i = 0; i < inputs.length; i++) {
        const input = inputs[i];
        // The ids are named after their dictionary keys
        args += '&' + input.id + '=';
        args += (input.value) ? input.value.replace('&', '') : input.placeholder;
    }
    // console.log(args);
    callScriptRunner(args);
};
// "Start a Run" tab button
document.getElementById("startRBtn").onclick = function() {
    switchTab(event, 'startR');
}

// This must be run at boot:
boot();