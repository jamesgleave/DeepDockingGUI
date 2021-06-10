// Global variables to keep track of what selections user has made
var CURRENT_CHART = 0; // the current carousel chart to display.
var CURRENT_ITERATION = 1;
var CURRENT_MODEL = 1;
var AVERAGED = false;

var LOADING_ARCH = false; // Tracks if architecture is loading

var NUM_CHARTS = 0; // number of charts for the carousel
var NUM_ITERATIONS = 1;
var NUM_MODELS = 0;

function displayRightChart(chartData, idOfChart) {
  // Destroying chart (if it exists) first:
  destroyChart(idOfChart);

  // Callback function to make the font size responsive
  var resizeFont = function (charinst, newsize) {
    // console.log("EpochChart:", newsize);
    // Inital width is 563
    charinst.options.title.fontSize = newsize.width / 28.15;
   
    // charinst.options.legend.labels.fontSize = newsize.width / 51.63; // No ledgend

    // Axis ticks
    charinst.options.scales.yAxes[0].ticks.fontSize = newsize.width / 40.21;
    charinst.options.scales.xAxes[0].ticks.fontSize = newsize.width / 40.21;

    // Axis labels:
    charinst.options.scales.yAxes[0].scaleLabel.fontSize = newsize.width / 35.19;
    charinst.options.scales.xAxes[0].scaleLabel.fontSize = newsize.width / 35.19;
  }

  var colorChoices = ["#1F78B4", "#A6CEE3", "#fcba03", "#bf5a5a"]; // max of 4 plotted items

  // Dynamically add datasets
  var datasets = [];

  for (let i = 0; i < chartData.datasets.length; i++) {
    const elm = chartData.datasets[i];
    var dataset = {
      fill: false,
      data: elm.data,
      label: elm.label,
      borderColor: colorChoices[i],
      backgroundColor: colorChoices[i]
    }

    datasets.push(dataset);  
  }

  var data = {
    labels: chartData.labels,
    datasets: datasets
  };

  var options = {
    title: {
      display: true,
      text: chartData.title,
      fontFamily: "K2D",
      fontSize: 20,
      fontColor: "#DFFFE6",
      padding: 10
    },
    legend: {
      display: datasets.length > 1, // If there is only one dataset then we dont need a legend.
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
          fontSize: 14,
          padding: 10
        },
        display: true,
        scaleLabel: {
          display: chartData.yAxis, //null is falsey
          labelString: chartData.yAxis,
          fontFamily: "K2D",
          fontSize: 16,
          fontColor: "#DFFFE6",
          padding: 10

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
          fontSize: 14,
          padding: 10
        },
        display: true,
        scaleLabel: {
          display: chartData.xAxis, //null is falsey
          labelString: chartData.xAxis,
          fontFamily: "K2D",
          fontSize: 16,
          fontColor: "#DFFFE6",
          padding: 10
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

  var chartInstance = Chart.Line(idOfChart, {
    options: options,
    data: data
  });

  resizeFont(chartInstance, { width: document.getElementById(idOfChart).offsetWidth});
}

function displayCarouselChart(chartData) {
  // Finding chart and destroying it first:
  destroyChart("carouselChart");

  // Callback function to make the font size responsive
  var resizeFont = function (charinst, newsize) {
    // console.log("carousel:", newsize);
    // Inital width is 826
    charinst.options.legend.labels.fontSize = newsize.width / 51.63;

    // Axis ticks
    charinst.options.scales.yAxes[0].ticks.fontSize = newsize.width / 51.63;
    charinst.options.scales.xAxes[0].ticks.fontSize = newsize.width / 51.63;

    // Axis labels:
    charinst.options.scales.yAxes[0].scaleLabel.fontSize = newsize.width / 41.3;
    charinst.options.scales.xAxes[0].scaleLabel.fontSize = newsize.width / 41.3;
  }

  var colorChoices = ["#1F78B4", "#A6CEE3", "#fcba03", "#bf5a5a"]; // max of 4 plotted items

  // Dynamically add datasets
  var datasets = [];

  for (let i = 0; i < chartData.datasets.length; i++) {
    const elm = chartData.datasets[i];
    var dataset = {
      fill: false,
      data: elm.data,
      label: elm.label,
      borderColor: colorChoices[i],
      backgroundColor: colorChoices[i]
    }

    datasets.push(dataset);  
  }

  var data = {
    labels: chartData.labels,
    datasets: datasets
  };
  
  // Altering the title:
  document.getElementById('chart-carousel-name').innerHTML = chartData['title']

  var options = {
    title: {
      display: false // Title is displayed in the #chart-carousel-name
    },
    legend: {
      display: datasets.length > 1, // If there is only one dataset then we dont need a legend.
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
          display: chartData.yAxis, //null is falsey
          labelString: chartData.yAxis,
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
          display: chartData.xAxis,
          labelString: chartData.xAxis,
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

  var chartInstance = Chart.Line("carouselChart", {
    options: options,
    data: data
  });

  resizeFont(chartInstance, { width: document.getElementById("carouselChart").offsetWidth });
}

function updateButtons(){
  // This function configures buttons to be visible or not depending on the selections made
  var checkLeft = function(btn, currNum, minNum){
    if (currNum <= minNum){
      btn.style.visibility = 'hidden';
      
    } else{
      btn.style.visibility = 'visible';
    }
  };

  var checkRight = function(btn, currNum, maxNum){
    if (currNum >= maxNum-1){
      btn.style.visibility = 'hidden';
    }else{
      btn.style.visibility = 'visible';
    }
  };

  // Carousel buttons:
  checkLeft(document.getElementById('carousel-left-arrow'), CURRENT_CHART, 0);
  checkRight(document.getElementById('carousel-right-arrow'), CURRENT_CHART, NUM_CHARTS);

  // Selection buttons
  // Iteration
  checkLeft(document.getElementById('iteration-left-arrow'), CURRENT_ITERATION, 1);
  checkRight(document.getElementById('iteration-right-arrow'), CURRENT_ITERATION, NUM_ITERATIONS+1);
  
  // Model
  // Disable both if we are taking an average
  if (AVERAGED){
    document.getElementById('model-left-arrow').style.visibility = 'hidden';
    document.getElementById('model-right-arrow').style.visibility = 'hidden';
  }else {
    checkLeft(document.getElementById('model-left-arrow'), CURRENT_MODEL, 1);
    checkRight(document.getElementById('model-right-arrow'), CURRENT_MODEL, NUM_MODELS+1);
  }

  // Updating selected iteration and selected model display:
  var maintainTwoDigits = function(numb){
    var outString = numb.toString();
    if (outString.length == 1){
      return '0' + outString;
    }
    return outString;
  }

  document.getElementById('selected-iteration').innerHTML = maintainTwoDigits(CURRENT_ITERATION);
  document.getElementById('selected-model').innerHTML = maintainTwoDigits(CURRENT_MODEL);
}

function updateCharts(carouselOnly) {
  var args = "iteration=" + CURRENT_ITERATION +
              "&model=" + CURRENT_MODEL +
              "&averaged=" + AVERAGED +
              "&carousel=" + CURRENT_CHART;

  // Calls the server to retrive the chart data that corresponds to the number passed in.
  $.ajax({
    type: "GET",
    url: "/modelData?"+ args,
    dataType: 'json',
    success: function (data, status, settings) {
      // console.log(settings);
      NUM_CHARTS = data.numCharts;
      NUM_ITERATIONS = data.numIterations;
      NUM_MODELS = data.numModels;
      
      // Checking to see if we even have the data:
      if (data.currentPhase < 4) { 
        // If we aren't at phase 4 yet then dont show current iteration
        NUM_ITERATIONS--;
      }

      // Display the loading tab instead of data when no iterations 
      if (NUM_ITERATIONS == 0){
        document.querySelector('#loadingContent > h1').innerHTML = "Content not available yet, check again after phase 4!";
        switchTab(event, 'loadingContent', true);
      }else{
        displayCarouselChart(data.carouselData);
        if (!carouselOnly){ // null in js is a falsey value.
          displayRightChart(data.rightData[0], 'topRightChart');
          displayRightChart(data.rightData[1], 'bottomRightChart');
        }
        updateButtons();
      }
    },
    error: function (res, opt, err) {
      alert("Error!")
      console.log(res, opt, err);
    }
  }).done(function (response) {
    toggleLoadingScreen(false);
  });
}

// Carousel buttons:
document.getElementById('carousel-left-arrow').onclick = function (){
  // Making sure that decrementing will still be a valid chart number
  if (CURRENT_CHART - 1 >= 0){
    CURRENT_CHART -= 1;
    // Calling the server and updating the chart and buttons
    updateCharts(true); // only update carousel
  }
}

document.getElementById('carousel-right-arrow').onclick = function (){
  // Making sure that incrementing will still be a valid chart number
  if (CURRENT_CHART + 1 <  NUM_CHARTS){
    CURRENT_CHART += 1;
    // Calling the server and updating the chart and buttons
    updateCharts(true); // only carousel
  }
}

// Model Navigation buttons
document.getElementById('iteration-left-arrow').onclick = function (){
  // console.log("iter left");
  // Making sure that decrementing will still be a valid iteration number
  if (CURRENT_ITERATION - 1 >= 1){
    CURRENT_ITERATION -= 1;
    CURRENT_MODEL = 1; // must be done to avoid big error
    // Calling the server and updating the chart and buttons
    updateCharts();
  }
}

document.getElementById('iteration-right-arrow').onclick = function (){
  // console.log("iter right");
  // Making sure that incrementing will still be a valid chart number
  if (CURRENT_ITERATION + 1 <=  NUM_ITERATIONS){
    CURRENT_ITERATION += 1;
    CURRENT_MODEL = 1;
    // Calling the server and updating the chart and buttons
    updateCharts();
  }
}

document.getElementById('model-left-arrow').onclick =  function (){
  // console.log("model left");
  // Making sure that decrementing will still be a valid iteration number
  if (CURRENT_MODEL - 1 >= 1){
    CURRENT_MODEL -= 1;
    // Calling the server and updating the chart and buttons
    updateCharts();
  }
}

document.getElementById('model-right-arrow').onclick = function (){
  // console.log("model right");
  // Making sure that incrementing will still be a valid chart number
  if (CURRENT_MODEL + 1 <=  NUM_MODELS){
    CURRENT_MODEL += 1;
    // Calling the server and updating the chart and buttons
    updateCharts();
  }
}

document.getElementById('selected-average').onclick = function(event){
   AVERAGED = event.target.checked;
   updateCharts();
}

document.getElementById('view-achitecture-btn').onclick = function(){
  LOADING_ARCH = true;
  toggleLoadingScreen(true);
  addPanAndZoom('modelArchImage');
  resetImagePos('modelArchImage');

  var args = "iteration=" + CURRENT_ITERATION +
              "&model=" + CURRENT_MODEL;

  // first request to get the image
  $.ajax({ 
    type: "POST",
    url: "/modelArch?image=true&" + args,
    dataType: 'text',
    contentType: 'image/jpeg',
    beforeSend: function (xhr) {
      xhr.overrideMimeType('text/plain; charset=x-user-defined');
    },
    success: function (data, status, settings) {

      if(data.length < 1){
          alert("The image doesnt exist");
          $("#modelArchImage").attr("src", "data:image/png;base64,");
          return
      }

      var binary = "";
      var responseText = data;
      var responseTextLen = responseText.length;
  
      for ( i = 0; i < responseTextLen; i++ ) {
          binary += String.fromCharCode(responseText.charCodeAt(i) & 255)
      }
      $("#modelArchImage").attr("src", "data:image/jpeg;base64,"+btoa(binary)); 

      // Making second request to get hyperparameters:
      $.ajax({ 
        type: "GET",
        url: "/modelArch?image=false&" + args,
        dataType: 'json',
        success : function (data, status, settings){
            // Anon function to create a list element
            var createListItem = function(content){
              var li = document.createElement('li')
              li.textContent = content;
              return li;
            };
            
            var list = document.getElementById('HyperparametersList');

            // clearing data first:
            while (list.firstChild) {
              list.removeChild(list.lastChild);
            }
            
            for (var groupKey in data){ // Adding them to the hyp list
              if (groupKey ==='name'){ continue;}
              
              list.appendChild(createListItem("")); // spacing them out...

              for (var key in data[groupKey]){
                var content = key + ": " + String(data[groupKey][key]);
                list.appendChild(createListItem('- ' + content));
              }
            }
            
            // Changing the name/desc:
            document.querySelector('#modelNameImage > h2').innerHTML = 'Model Number-Name: ' + CURRENT_MODEL +'-'+ data.name;

            togglePopup('modelArch', true);
        },
        error: function (res, opt, err) {
          alert("Error in retriving Hyperparameters")
          console.log(res,opt,err);
        }
      }).done(function (response) {
        toggleLoadingScreen(false);
        LOADING_ARCH = false;
      });

    },
    error: function (res, opt, err) {
      alert("Error in retriving model arch")
      console.log(res,opt,err);
    }
  }).done(function (response) {
  });

}

document.querySelector('#modelArch .closePopupBtn').onclick = function(){
  togglePopup('modelArch', false);
}

function bootModelsTab(){
  // If loading this will cause an issue with the arch no longer seeming to be loading.
  if (!LOADING_ARCH)
    updateCharts();
}

document.getElementById("modelsBtn").onclick = function () {
  toggleLoadingScreen(true);
  bootModelsTab();
  switchTab(event, 'models');
  UPDATE_CALLBACKS["models"] = bootModelsTab;
  resetUpdateLoop();
}

