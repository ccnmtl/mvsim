// minimums and maximums to enforce
var effort_min = [];
var effort_max = [];

function setSchoolEffort(e) {
   var name = e.src().id.substring(7);
   var school_effort = parseInt($("effort-"+name+"-school").innerHTML);
   var current_effort = $("effort-"+name).value;
   var allowed_effort = parseInt($("effort-"+name+"-maximum").innerHTML);

   if(e.src().checked) {
      var new_effort = Math.max(0, current_effort - school_effort);
      $("effort-"+name).value = new_effort;
      setEffortMax("effort-"+name, new_effort);
   }
   else {
      setEffortMax("effort-"+name, allowed_effort);
      var new_effort = Math.min(current_effort + school_effort, allowed_effort);
      $("effort-"+name).value = new_effort;
   }
   updateTotalEffort();
}

function setEffortMin(element, value) {
  effort_min[element] = value;
}
function getEffortMin(element) {
  if (element in effort_min) { return effort_min[element]; }
  return 0;
}
function setEffortMax(element, value) {
  effort_max[element] = value;
}
function getEffortMax(element) {
  if (element in effort_max) { return effort_max[element]; }
  return 1000;
}

function showOverExertedMessage(id) {
   var name = id.split('-')[1];
   showElement($('effort-over-' + name));
}

function hideOverExertedMessage(id) {
   var name = id.split('-')[1];
   hideElement($('effort-over-' + name));
}

function changeEffort(e) {
  var id = e.src().id;
  if(parseInt(getElement(id).value) < getEffortMin(id)) {
     getElement(id).value = getEffortMin(id);
  }
  if(parseInt(getElement(id).value) > getEffortMax(id)) {
     showOverExertedMessage(id);
     getElement(id).value = getEffortMax(id);
  } else {
     hideOverExertedMessage(id);
  }
  updateTotalEffort();
}

function changeFamilyEffort(e) {
  var id = e.src().id;
  // force it to an integer (since the backend will treat it as one anyway)
  var value = parseInt(getElement(id).value);
  getElement(id).value = value;
  if(parseInt(getElement(id).value) < getEffortMin(id)) {
     getElement(id).value = getEffortMin(id);
  }
  drawPlot();
}

function updateTotalEffort(){
  var total_effort = 0;
  forEach(getElementsByTagAndClassName(null, "individual_effort"),
     function(element) {
        // force it to an integer (since the backend will treat it as one anyway)
//        element.value = parseInt(element.value);
        total_effort += parseInt(element.value);

       // update graphic
       getElement(element.id + '-graphic').innerHTML = element.value;
     }
  );
  getElement("total_effort").innerHTML = total_effort;
  drawPlot();
}

function drawPlot() {
  var total_effort = getElement("total_effort").innerHTML;
  var available_effort = total_effort;
  var overallocated = 0;

  var slider_data = Array();
  var i=1;

  forEach(getElementsByTagAndClassName(null, "family_effort"),
     function(element) {
        available_effort = parseFloat(available_effort) - parseFloat(element.value);

        // add to graph array
        slider_data.push(parseFloat(element.value));
        i++;

        // update graphic
        getElement(element.id + '-inner').innerHTML = element.value;
     }
  );

  if (available_effort < 0) {
     overallocated = 0 - available_effort;
     available_effort = 0;
  }

  // add available effort to the graph
  slider_data.push(available_effort);

  var labels = ["farming", "fishing", "fuel wood", "water", "small business", "idle"];
  makeSlider("effort-graph",slider_data,labels);

  if(overallocated > 0) {
    setEffortMessage("You are currently overallocated by " + overallocated + " hour(s).");
  }
  else { setEffortMessage(""); }

  // set allocated effort
  var classname = 'normal_effort';
  if(overallocated > 0) {
    classname = 'overallocated_effort';
  }
  setElementClass('allocated_effort', classname);
  $("allocated_effort").innerHTML = parseInt(total_effort) + parseInt(overallocated)
                                    - available_effort;
}

function setEffortMessage(message) {
  $("effort_message").innerHTML = message;
}

function initEffortMonitor() {
   forEach(getElementsByTagAndClassName(null, "individual_effort"),
      function(element) {
         connect(element, "onchange", changeEffort);
         setEffortMax(element.id, $(element.id + "-maximum").innerHTML);
      }
   );

   forEach(getElementsByTagAndClassName(null, "family_effort"),
      function(element) {
	      connect(element, "onchange", changeFamilyEffort);
      }
   );

	forEach(getElementsByTagAndClassName(null, "enroll-school"),
	   function(element) {
   	   connect(element, "onclick", setSchoolEffort);
    	   signal(element, "onclick");
	   }
	);

   updateTotalEffort();
}


addLoadEvent(initEffortMonitor);
