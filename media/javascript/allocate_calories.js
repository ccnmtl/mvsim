var calories_available = 0;
var starting_calories_available = 0;
var needed_calories = 0;

function purchase_subsistence_calories() {
  var delta = needed_calories - starting_calories_available;
  delta = Math.ceil(delta / 10.0);
  $("food-to-buy").value = delta;
  update_calories_available();
  update_shopping_cart();
};

function update_calories_available (){
   var q = parseInt($('food-to-buy').value);
   if(isNaN(q) || q < 0) {
      $('food-to-buy').value = 0;
      q = 0;
   }

  calories_available = starting_calories_available + (q * 10.0);
   $('amount-calories2').innerHTML = calories_available;

   var inputs = getElementsByTagAndClassName('input','allocate-calories');
   if (inputs.length == 1) {
      // there's only one family member alive.
      // allocate all food to them.
      inputs[0].value = calories_available;
   }

   forEach(inputs,
	   function (element) {
	      var cals = parseInt(element.value);
	      if(isNaN(cals) || cals < 0) {
	         element.value = 0;
	         cals = 0;
   	   }
 	      calories_available -= cals;
	   }
	  );

   $('amount-calories').innerHTML = calories_available;

   if (calories_available >= needed_calories) {
      hideElement($('allocate-calories-blurb'));
      hideElement($('allocate-calories-table'));
      showElement($('enough-calories-allocated'));
      showElement($('calorie-needs'));
   } else {
      showElement($('allocate-calories-blurb'));
      showElement($('allocate-calories-table'));
      hideElement($('enough-calories-allocated'));
      hideElement($('calorie-needs'));
   }
}

function init_allocate_calories() {
   if (!$('food-to-buy')) return; // no calorie allocation this turn

   starting_calories_available = parseFloat(scrapeText($('amount-calories')).replace(/\,/,""));
   needed_calories = parseFloat(scrapeText($('needed-calories')));

   connect('food-to-buy','onchange',update_calories_available);

   forEach(getElementsByTagAndClassName('input','allocate-calories'),
	   function (element) {
	      connect(element,'onchange',update_calories_available);
	   });
   update_calories_available();
}

addLoadEvent(init_allocate_calories);

