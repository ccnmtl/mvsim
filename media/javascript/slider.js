/* requires MochiKit base and DragAndDrop:
   <script type="text/javascript" src="http://ccnmtl.columbia.edu/scripts/MochiKit/MochiKit.js"></script>
   <script type="text/javascript" src="http://ccnmtl.columbia.edu/scripts/MochiKit/DragAndDrop.js"></script>
*/

/* information for style overrides:
   - override by using !important in a stylesheet
   - the container div is class "slider-container" and id (div id), where (div id) is the id that was passed in
   - the div containing the graph is class "slider-graph" and id "slider-(div id)-graph"
   - each area of the graph is class "slider-area" and is id "slider-(div id)-area-(label)"
   - the div containing the labels is class "slider-labels" and id "slider-(div id)-labels"
   - each individual label is in a div of class "slider-label" and id "slider-(div id)-label-(label)"
*/

/* make a vertical slider to represent data.
   - labels are optional:
     - if labels is not provided or evaluates to false, no labels will be shown.
     - if labels is an array, its contents will be used as the labels.
     - if labels is not an array but evaluates to true, default labels will be used.
     - if the label array is too short for all the data, default labels will be used for all remaining data areas.
   - set sliders = true for optional sliders
*/

function makeSlider(graph_div,data,labels,sliders) {
  if(! sliders) { sliders = false; }

  // find data total
  var data_total = 0;
  for(var i=0; i<data.length; i++) { data_total += data[i]; }
  
  var colors = ["#cd5c5c", "#f4a460", "#ffec8b", "#9bcd9b", "#a4d3ee", "#ab82ff", "#cdb79e", "#cdcdc1", "#fffaf0", "#eed5d2"];

  var showLabels = true;
  if(! labels) { showLabels = false; }
  
  // generate default labels if none were provided
  if(showLabels && typeof labels != "object") {
     labels = Array();
     for(var i=0; i<data.length; i++) {
        labels.push((i+1).toString());
     }
  }
  
  if(showLabels &&  labels.length < data.length) {
    for(var i=labels.length; i<data.length; i++) {
       labels.push((i+1).toString());
    }
  }
  
  // create container div
  var graph_height = $(graph_div).style.height || "300px";
  //var graph_width = parseInt($(graph_div).style.width) || 250;

  var parentdiv = DIV({'class':'slider-container', 'id':graph_div});
  parentdiv.style.height = graph_height;
  //parentdiv.style.width = graph_width;
  
  // create graph div and set some style options
  var sliderbar = DIV({'class':'slider-graph', 'id':'slider-'+graph_div+'-graph'});
  sliderbar.style.display = "block";
  sliderbar.style.cssFloat = "left";     // Firefox
  sliderbar.style.styleFloat = "left";   // IE
  if(showLabels) { sliderbar.style.width = "50px"; }
  else { sliderbar.style.width = $(graph_div).style.width || "300px"; }
  sliderbar.style.height = graph_height;
  sliderbar.style.textAlign = "center";
  sliderbar.style.backgroundColor = "white";
  sliderbar.style.border = "gray";
  sliderbar.style.borderStyle = "solid";
  sliderbar.style.borderWidth = "1px";

  // create label div and set some style options
  var labelbar = DIV({'class':'slider-labels', 'id':'slider-'+graph_div+'-labels'});
  labelbar.style.display = "block";
  labelbar.style.cssFloat = "left";     // Firefox
  labelbar.style.styleFloat = "left";   // IE
  labelbar.style.height = graph_height;
  labelbar.style.textAlign = "left";
  labelbar.style.marginLeft = "5px";
  labelbar.style.fontSize = "0.8em";
  labelbar.style.lineHeight = "0px";

  // figure out slider stuff
  if(sliders) {
    var numberAreas = data.length;
    var handle = createDOM("DIV", {'class':'slider-handle', 'id':'slider-'+graph_div+'-handle-'+i+'-'+i+1});cc
  }
  
  var lastalign = 0;
  for(var i=0; i<data.length; i++) {
    var percent = parseFloat(data[i]) / data_total * 100.0;
    if(data[i] == 0) { continue; }

    var classLabel = i;
    if(showLabels) { classLabel = labels[i].replace(/ /g, "-"); }

    var area = createDOM("DIV", {'class':'slider-area', 'id':'slider-'+graph_div+'-area-'+classLabel});
    area.style.width = "100%";
    area.style.height = percent+'%';
    area.style.backgroundColor = colors[i%10];
    appendChildNodes(sliderbar, area);
    
    // add label to label bar
    if(showLabels) {
       var label = DIV({'class':'slider-label','id':'slider-'+graph_div+'-label-'+classLabel}, labels[i] + ": " + Math.round(percent,2) + "%");

       // this aligns the label to the middle of its associated bar on the graph
       label.style.position = "relative";
       label.style.top = 0.01 * (lastalign + percent/2) * parseInt(graph_height) + "px";  // if height not in pixels, this will break
       appendChildNodes(labelbar, label);
    }
    
    lastalign += percent;
  }
  
  appendChildNodes(parentdiv, sliderbar);
  if (showLabels) { appendChildNodes(parentdiv, labelbar); }
  swapDOM(graph_div,parentdiv);
}

function makeHandle(id) {
    var height_of_parent = 200;
    var height_of_bar = 10;
    var bottom_limit = height_of_parent - height_of_bar;
    new Draggable($(id), {'snap':snapTo(0,bottom_limit)});
}