function balance_crops(crop) {
   var element = $('crops-' + crop);
   var id = element.id;
   var other = id == 'crops-cotton' ? 'crops-maize' : 'crops-cotton';
   if (element.value > 4) { element.value = 4; }
   if (element.value < 0) { element.value = 0; }
   $(other).value = 4 - parseInt($(id).value);
   draw_crops();
}

function balance_crops_cotton(e) { balance_crops('cotton'); }
function balance_crops_maize(e) { balance_crops('maize'); }

function draw_crops() {
  var amt_maize = parseInt(getElement("crops-maize").value);

  var crop_class = "crop-Maize";
  for(var i=0; i < 4; i++) {
    if(amt_maize == 0) { crop_class = "crop-Cotton"; }
    else { amt_maize--; }
    setElementClass("crop-"+i, crop_class);
  }
}

function init_crops_balancer() {
   connect('crops-maize','onchange',balance_crops_maize);
   connect('crops-cotton','onchange',balance_crops_cotton);
}

addLoadEvent(init_crops_balancer);
