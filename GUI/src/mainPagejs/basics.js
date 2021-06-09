// Basic functions required by the entire html page
function togglePopup(elemID,turn_on){
  if (turn_on) {
      document.getElementById(elemID).style.visibility = "visible";
  }else{
      document.getElementById(elemID).style.visibility = "hidden";
  }
}

function toggleLoadingScreen(turn_on){
  togglePopup('loading', turn_on);
}

function switchTab(evt, tabname, activetab) {
    // Declare all variables
    var i, tabcontent, tablinks;
  
    // Get all elements with class="tabcontent" and hide them
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = "none";
    }
  
    // Get all elements with class="tablinks" and remove the class "active"
    if (!activetab){ // Won't change the tab activation
      tablinks = document.getElementsByClassName("tablinks");
      for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
      }
    }
  
    // Show the current tab, and add an "active" class to the button that opened the tab
    document.getElementById(tabname).style.display = "block";
    document.getElementById(tabname+'Btn').className += " active";
}

function flash(elmID, filters){
  var elm = document.getElementById(elmID);
  filter1 = filters? filters[0]: 'brightness(100%)';
  filter2 = filters? filters[1]: 'brightness(50%)';

  if (elm.style.filter === filter1){
    elm.style.filter = filter2;

  } else {
    elm.style.filter = filter1;
  }
};

function destroyChart(id){
  Chart.helpers.each(Chart.instances, function(instance){
    if (instance.chart.canvas.id === id){
      instance.destroy();
    }
  });
};

// Pan and zoom functionality for images:
var img_ele = null, 
  x_cursor = 0,
  y_cursor = 0,
  x_img_start = 0,
  y_img_start = 0;

function zoom(zoomincrement, img_id) {
  img_ele = document.getElementById(img_id);
  var pre_width = img_ele.getBoundingClientRect().width, pre_height = img_ele.getBoundingClientRect().height;
  img_ele.style.width = (pre_width * zoomincrement) + 'px';
  img_ele.style.height = (pre_height * zoomincrement) + 'px';
  img_ele = null;
}

//TODO: FIGURE OUT ISSUE WITH PAN MOUSE MISSMATCH
function start_drag(e) {
  img_ele = this;
  
  var starting_L = parseInt(img_ele.style.left.split('px')[0]);
  var starting_T = parseInt(img_ele.style.top.split('px')[0]);
  starting_L = (starting_L) ? starting_L : 0; // if the value is auto the conditional will be false (NaN)
  starting_T = (starting_T) ? starting_T : 0; // if the value is auto
  
  // Getting the difference between the mouse and the top left corner of the image
  x_img_start = starting_L - e.clientX; // pixel position of left side.
  y_img_start = starting_L - e.clientY;  
}

function stop_drag() {
  img_ele = null;
}

function while_drag(e) {
  e.preventDefault();
  var delta_x = x_img_start + e.clientX;
  var delta_y = y_img_start + e.clientY;
  
  if (img_ele !== null) {
    // calculating amount to move image by
    img_ele.style.left = delta_x + 'px';
    img_ele.style.top = delta_y + 'px';
  }
}

function resetPanandZoomVals(){
  img_ele = null, 
  x_cursor = 0,
  y_cursor = 0,
  x_img_ele = 0,
  y_img_ele = 0;
}

function addPanAndZoom(img_id){
  var element = document.getElementById(img_id);

    // Adds pan and zoom functionality to the element
  element.addEventListener("wheel", function(e){
    e.preventDefault();
    zoom(1 - (e.deltaY/300)* 0.1, img_id);
  });

  element.addEventListener('mousedown', start_drag);
  element.addEventListener('mousemove', while_drag);
  element.parentElement.addEventListener('mouseup', stop_drag);
}

function resetImagePos(img_id){
  var element = document.getElementById(img_id);
  element.style.left = 'auto';
  element.style.top = 'auto';

  element.style.width = 'auto';
  element.style.height = 'auto';
}

function deleteProject(name){
  var name = (name) ? name : document.querySelector('#curr_project_name').textContent.split(':')[1].trim();
  console.log('deleting project: ', name);  
  var args = 'project_name=' + name;
  toggleLoadingScreen(true);

  $.ajax({
    type: "POST",
    url: `/deleteProject?${args}`,
    dataType: 'json',
    success: function (data, status, settings) {
        console.log('project deleted', data);
    },
    error: function (res, opt, err) {
        alert('Error\n' + res.status + ': ' + err);
    }
  }).done(function (response) {
      toggleLoadingScreen(false);
  });
}

var UPDATE_RATE = null;
var UPDATE_CALLBACKS = {}; // Saves the callbacks for all the tabs opened
var UPDATE_ID; // the ID for the async update loop
const DEBUG_MODE = false;

function clientUpdateLoop(){
  // This function is a loop that runs in the background that retrives updates from the server as it comes in
  // and displays that data to the client depending on which tab they are on.

  // Checking which tab is active:
  var active = document.querySelector("body > div.tabs.disable-select > Button.active").id;
  var activeTab = active.substring(0, active.length-3);

  console.log("active tab:", activeTab);
  // Not running for top Scoring tab because that would just be annoying when viewing molec:
  if (activeTab !== "topScoring"){
    // Running the appropriate callback
    var callbackfn = UPDATE_CALLBACKS[activeTab];
    if (callbackfn) callbackfn();
  }
}

function resetUpdateLoop(){
  // Used for when we already have the update rate and 
  // want to restart the loop to prevent "double loading" of a tab.
  if (UPDATE_ID){ // Clearing any previous update loop
    clearInterval(UPDATE_ID);
    UPDATE_ID = null;
  }
  UPDATE_ID = setInterval(clientUpdateLoop, UPDATE_RATE);
  console.log("update loop reset!");
}

function startUpdateLoop(){
  $.ajax({
    type: "GET",
    url: "/getBasics",
    dataType: 'json',
    success: function (data, status, settings) {
      UPDATE_RATE = data.update_rate_ms;
      console.log("update rate (ms):", UPDATE_RATE);
      if (UPDATE_RATE){ // IF NOT UNDEF
        UPDATE_ID = setInterval(clientUpdateLoop, UPDATE_RATE);
      }
    },
    error: function (res, opt, err) {
      alert("Error!")
      console.log(res, opt, err);
    }
  });
}

function startup(){
  startUpdateLoop();
  // Changing the background color:
  document.getElementsByTagName("html")[0].style.background = "#5A6E59";
}

startup();