// Displays the current iteration and phase
function displayCurrentInfo(currentInfo) {
    document.querySelector("#current-Iter > .number-display > p").innerHTML = currentInfo.iter;
    document.querySelector("#current-Phase > .number-display > p").innerHTML = currentInfo.phase;
}

// Displays the ETAs
function displayETAs(ETAs) {
    document.querySelector("#ETA-Full > .percent").innerHTML =  ETAs.full + "%"

    document.querySelector("#ETA-Iteration > .percent").innerHTML = ETAs.iter + "%";

    document.querySelector("#ETA-Phase > .bestETA").innerHTML = "Best - " + ETAs.phase.best;
    document.querySelector("#ETA-Phase > .worstETA").innerHTML = "Worst - " + ETAs.phase.worst;
    document.querySelector("#ETA-Phase > .averageETA").innerHTML = "Average - " + ETAs.phase.average;
}


function displayMolecRemainingChart(chartData) {
    // Destroying chart (if it exists) first:
    destroyChart('molecRemainingChart');

    // Callback function to make the font size responsive
    var resizeFont = function(charinst, newsize){
        charinst.options.title.fontSize = newsize.width / 51.22;
        
        charinst.options.legend.labels.fontSize = newsize.width / 115.25;
        
        charinst.options.scales.yAxes[0].ticks.fontSize = newsize.width / 115.25;
        charinst.options.scales.yAxes[0].scaleLabel.fontSize = newsize.width / 92.2;

        charinst.options.scales.xAxes[0].ticks.fontSize = newsize.width / 115.25;
        charinst.options.scales.xAxes[0].scaleLabel.fontSize = newsize.width / 92.2;
    }

    var data = {
        labels: chartData.modelPred.x,
        datasets: [{
            fill: false,
            label: "Predicted by Model",
            backgroundColor: "#1F78B4",
            borderColor: "#1F78B4",
            data: chartData.modelPred.y,
        }, {
            fill: false,
            label: "Actual Value",
            backgroundColor: "#A6CEE3",
            borderColor: "#A6CEE3",
            data: chartData.actual.y,
        }]
    };

    var options = {
        title: {
            display: true,
            text: "Molecules Remaining",
            fontFamily: "K2D",
            fontSize: 36,
            fontColor: "#DFFFE6",
            padding: 0
        },
        legend: {
            display: true,
            position: "top",
            labels: {
                boxWidth: 15,
                padding: 15,
                fontFamily: "K2D",
                fontSize: 16,
                fontColor: "#DFFFE6"
            }
        },
        scales: {
            yAxes: [{
                id: "y-axis-molec",
                ticks: {
                  fontColor: "#A3A3A3",
                  fontFamily: "K2D",
                  fontSize: 16,
                  padding: 10
                },
                display: true,
                scaleLabel: {
                    display: true,
                    labelString: "Number of Molecules",
                    fontFamily: "K2D",
                    fontSize: 20,
                    fontColor: "#DFFFE6"

                },
                stacked: false,
                gridLines: {
                    display: true,
                    color: "#A3A3A3",
                    drawTicks: false,
                    drawBorder: true
                }
            }],
            xAxes: [{
                id: "x-axis-iter",
                ticks: {
                    fontColor: "#A3A3A3",
                    fontFamily: "K2D",
                    fontSize: 16,
                    padding: 10
                },
                display: true,
                scaleLabel: {
                    display: true,
                    labelString: "Iteration",
                    fontFamily: "K2D",
                    fontSize: 20,
                    fontColor: "#DFFFE6"
                },
                gridLines: {
                    display: true,
                    color: "#A3A3A3",
                    drawTicks: false,
                    drawBorder: false
                }
            }]
        },
        responsiveAnimationDuration: 250,
        responsive: true,
        maintainAspectRatio: false,
        onResize: resizeFont,
        plugins: {
            zoom: {
                // Container for pan options
                pan: {
                    // Boolean to enable panning
                    enabled: true,
    
                    // Panning directions. Remove the appropriate direction to disable 
                    // Eg. 'y' would only allow panning in the y direction
                    mode: 'xy'
                },
    
                // Container for zoom options
                zoom: {
                    // Boolean to enable zooming
                    enabled: true,
    
                    // Zooming directions. Remove the appropriate direction to disable 
                    // Eg. 'y' would only allow zooming in the y direction
                    mode: 'xy',
                }
            }
        }      
    };
    

    var chartInstance = Chart.Line("molecRemainingChart", {
        options: options,
        data: data
    });

    resizeFont(chartInstance, {width: document.getElementById("molecRemainingChart").offsetWidth});
}

var IDLE_ASNYC_ID; // Interval id for blinking indicator light

document.getElementById("progBtn").onclick = function() {
    toggleLoadingScreen(true);

    // Async GET request for the data needed for this tab.
    $.ajax({
        type: "GET",
        url: "/progressData",
        dataType: 'json',
        success: function (data, status, settings) {
            displayCurrentInfo(data.currentInfo);
            displayETAs(data.ETAs);
            displayMolecRemainingChart(data.molecRemainingData);
            
            // Clearing any previously set intervals:
            if (IDLE_ASNYC_ID) {
                clearInterval(IDLE_ASNYC_ID);
                IDLE_ASNYC_ID = null;
            }
        
            indicator = document.getElementById('idleStatus');
            // Checking to see if there is anything running/pending/canceling:
            if (!data.is_idle){
                // Flashing green when we have stuff running and most are not pending
                pending_no = parseInt(data.pending.pending);
                running_no = parseInt(data.pending.running);
                tot_no = pending_no + running_no;
                percent_pending = pending_no/tot_no;
                flashing = true;
                
                // If none are pending 0.0 we display a blinking green (default)
                if (percent_pending === 0){
                    indicator.src = indicator.src.substr(0, indicator.src.length - 5) + 'g.svg';
                } else if (percent_pending < 1){ // blinking yellow if some pending
                    indicator.src = indicator.src.substr(0, indicator.src.length - 5) + 'y.svg';
                } else { // stale yellow if all pending
                    indicator.src = indicator.src.substr(0, indicator.src.length - 5) + 'y.svg';
                    flashing = false
                }
                // flashing
                if (flashing) IDLE_ASNYC_ID = setInterval(function(){flash('idleStatus')}, 500);
            } else { //stale green if nothing is running or pending.
                indicator.src = indicator.src.substr(0, indicator.src.length - 5) + 'g.svg';
                indicator.style.filter = 'brightness(50%)';
            }
            // if pending then we apply a yellow filter before flashing
            switchTab(event, 'prog');
        },
        error: function (res, opt, err) {
            if (res.start == 404) {
                // Project is not loaded yet...
            }
            alert("Error!")
            console.log(res, opt, err);
        }
    }).done(function (response) {
        toggleLoadingScreen(false);
    });
}


