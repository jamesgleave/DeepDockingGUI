var selected_smile = null; //keeps track of which smile is selected to highlight it.

// Displays the selected smile
function displaySelectedSmile(e){
  if (selected_smile) selected_smile.className = ''; // clearing the last element

  selected_smile = e.path[0];
  selected_smile.className = 'disabled';

  const new_smile = selected_smile.innerText;

  // requesting image:
  displayScaffold(new_smile);
}

// Displays the scaffold from request (if none is provided than we assume mode scaffold)
function displayScaffold(smile) {
  toggleLoadingScreen(true);

  var new_text = "Most Common Murcko Scaffold";

  if (smile) new_text = smile;
  else if (selected_smile) selected_smile.className = ''; // Clearing the previous selected smile
  
  // Changing the title to match
  document.querySelector('#murckov-scaffold > div > h2').innerHTML = new_text;

  $.ajax({ 
    type: "POST",
    url: "/topScoring",
    dataType: 'text',
    contentType: 'application/json',
    data: JSON.stringify({"smile": String(smile), "image":"true"}),
    beforeSend: function (xhr) {
      xhr.overrideMimeType('text/plain; charset=x-user-defined');
    },
    success: function (data, status, settings) {
      if(data.length < 1){
          alert("The image doesnt exist");
          $("#scaffoldImage").attr("src", "data:image/png;base64,");
          return
      }
      var binary = "";
      var responseText = data;
      var responseTextLen = responseText.length;
  
      for ( i = 0; i < responseTextLen; i++ ) {
          binary += String.fromCharCode(responseText.charCodeAt(i) & 255)
      }
      $("#scaffoldImage").attr("src", "data:image/jpeg;base64,"+btoa(binary));
    },
    error: function (res, opt, err) {
      alert("Error in retriving Murcko Scaffold")
      console.log(res,opt,err);
    }
  }).done(function (response) {
    resetImagePos('scaffoldImage');
    toggleLoadingScreen(false);
  });
}

// adds SMILES to the list
function fillTopScoringList(compounds){
  var list = document.querySelector('#top-scoring-list > ul');

  // clearing data first:
  while (list.firstChild)
    list.removeChild(list.lastChild);
  
  // Adding each of them to the list:
  for (var comp in compounds){
    var li = document.createElement('li');
    var a = document.createElement('a');
    a.textContent = compounds[comp];

    // Connecting them to an appropriate callback:
    a.onclick = displaySelectedSmile;
    
    li.appendChild(a);
    list.appendChild(li);
  }
};

// Downloads a text file containing some specific text
function download(filename, text) {
  var element = document.createElement('a');
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
  element.setAttribute('download', filename);

  element.style.display = 'none';
  document.body.appendChild(element);

  element.click();

  document.body.removeChild(element);
}

// Download button -> downloads list of all molecules
document.querySelector("#download-list > img").onclick = function () {
  download('top-scoring-smiles.txt', 
          document.querySelector("#top-scoring-list > ul").innerText);
};

// Reload Button -> refreshes the image to be the most common scaffold
document.querySelector('#reload-Murcko > img').onclick = function () {
  displayScaffold();
}

function bootTopScoringTab(){
  // request to get list of all molecules:
  $.ajax({
    type: "POST",
    url: "/topScoring",
    contentType: 'application/json',
    data: JSON.stringify({"smile":"undefined", "image":"false"}),
    success: function (data, status, settings) {
        fillTopScoringList(data.top_hits);
    },
    error: function (res, opt, err) {
        alert("Error: top scoring tab failure");
        console.log(res, opt, err);
    }
  }).done(function (response) {
    // request to get the Most common Murcko scaffold
    displayScaffold();
  });
}

// Tab button
document.getElementById("topScoringBtn").onclick = function() {
  addPanAndZoom('scaffoldImage');
  toggleLoadingScreen(true);
  bootTopScoringTab();
  switchTab(event, 'topScoring');
  UPDATE_CALLBACKS["topScoring"] = bootTopScoringTab; // not used but left here for future possible use (replace with another function)
  resetUpdateLoop();
};
