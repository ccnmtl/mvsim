function validateCalorieAllocation() {
   // gets called from validation.js on form submit.

   if (!$('food-to-buy')) return true; // no allocation necessary

   if (calories_available == 0) {
     var inputs = getElementsByTagAndClassName('input','allocate-calories');
     for( var i=0; i<inputs.length; ++i ) {
       var calories_allocated = parseFloat(inputs[i].value);
       if( calories_allocated > 0 ) {
	 return true;
       }
     }
     return confirm("You have no food available!  Are you sure you want to end the season " +
		    "without purchasing any calories?");
   }

   if (calories_available >= needed_calories) {
      // divide up the calories evenly
      var inputs = getElementsByTagAndClassName('input','allocate-calories');
      var num = inputs.length;
      var divided = calories_available / num;

      forEach(inputs,
	      function(element) {element.value = divided;}
	      );
      return true;
   }

   alert("You must allocate all your calories");
   return false;
};

function validateShoppingCart() {
   if (cash > -100) {
       return true;
   }
   alert("Sorry, you are not allowed to go more than CFA 100 into debt.");
   return false;
};

function validateVillageFund() {
  fund = getVillageFund();
  if( fund < 0 ) {
    alert("The village fund has dropped below CFA 0.  You're buying too much stuff.");
    return false;
  };
  return true;
};

// meta-validator which will eventually call the other validation methods
function validate() {
  if(! validateEfforts()) { return false; }
  if(! validateCalorieAllocation()) { return false; }
  if(! validateShoppingCart()) { return false; }
  if(! validatePurchaseLimits()) { return false; }
  if(! validateBorrowLimit() ) {
    return false;
  }
  if(! validateVillageFund() ) {
    return false;
  }
  // other validation calls go here
  return true;
}

function validateBorrowLimit() {
  var limit = $("microfinance_max_borrow").innerHTML.replace(/\,/g,"");
  var limit = parseFloat(limit);
  var current = parseFloat($("microfinance_borrow").value);
  if( current > limit ) {
    alert("Error: You cannot borrow more than CFA " + limit +
	  " from the rural bank.\n" +
	  "You must reduce the amount of your loan before you continue.")
    return false;
  };
  return true;
};

// check effort limits
function validateEfforts() {
  if (getElement("effort_message").innerHTML != "") {
    alert("Error: You have allocated more effort than you are contributing.\n" +
          "Either increase your individual effort or decrease effort on some activity.");
    return false;
  }

  if( parseFloat($("effort-small-business").value) > 0 ) {
    var capital = parseFloat($("existing_business_capital").innerHTML);
    capital += parseFloat($("small_business_investment").value);
    if( capital <= 0 ) {
      alert("Error: You are allocating effort to small business, but you have no small business capital.\n" +
	    "Either reduce your small business effort to zero, or invest in small business.");
      return false;
    }
  }

  return true;
};

function validatePurchaseLimits() {
  if( getElement("purchase-fertilizer-quantity").value > 1 ) {
    alert("In this version of the MVSim, you may only buy a single season's supply (1 bag) of fertilizer per turn.");
    return false;
  }
  if( getElement("purchase-high_yield_seeds-quantity").value > 1 ) {
    alert("In this version of the MVSim, you may only buy a single season's supply (1 bag) of high-yield seed per turn.");
    return false;
  }
  return true;
};
