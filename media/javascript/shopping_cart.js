
var starting_cash = 0;
var cash = 0;
var food_to_buy_cost = 0;
var cart = new Array();
var doctor_visits_cost = 0;
var school_cost = 0;
var assets_total = 0;
var bank_loan = 0;

function item_from_id(id) {
   var a = id.split('-');
   return a[1];
}

function item_price(item) {
   if (!$(item+'-purchase-price')) {
      return parseFloat(scrapeText($(item + "-sell-price")).replace(/\,/g,""));
   }
   return parseFloat(scrapeText($(item + "-purchase-price")).replace(/\,/g,""));
}

function add_item_to_cart(item) {
   var price = item_price(item);
   var quantity = $("purchase-" + item + "-quantity").value;
   // disallow negative values

   if (quantity < 0) {
      quantity = 0;
      $("purchase-" + item + "-quantity").value = quantity;
   }
   cart[item] = quantity * price;
}

function add_item_to_be_sold(item) {
   var price = item_price(item);
   var quantity = $("sell-" + item + "-quantity").value;

  // disallow negative values
   if (quantity < 0) {
      quantity = 0;
      $("sell-" + item + "-quantity").value = quantity;
   }
  var num_owned = parseFloat(scrapeText($("num_owned-" + item)));
   if( quantity > num_owned ) {
      quantity = num_owned;
      $("sell-" + item + "-quantity").value = quantity;
   }
   cart[item] = quantity * price * -1;
}

function update_cash_display(c) {
   $('cash').innerHTML = format_money(c);
   if (c < 0) {
      $('cash').style.color = '#f00';
   } else {
      $('cash').style.color = '#000';
   }
}

function format_money(amount) {
   var sign = "";
   if(amount < 0) { sign = "-"; }
   amount = Math.abs(amount);
   var left = Math.floor(amount*100+0.50000000001)
   var right = left % 100;
   if(right<10) { right = "0" + right; }
   left = Math.floor(left/100).toString()
   strCash = sign + left.split("").reverse().join("").
             replace(/(\d{3})/g,"$1,").replace(/,$/,"").
             split("").reverse().join("") + "." + right;
   return strCash;
}

function total_cart() {
   var total = 0;
   for (var i in cart) {
      total += cart[i];
   }
   total += food_to_buy_cost;
   total += doctor_visits_cost;
   total += school_cost;
   total += assets_total;
   cash = starting_cash - total;
   cash += bank_loan;
   return cash;
}

function update_shopping_cart(e) {
   forEach(getElementsByTagAndClassName('input','purchase-item-input'),
	   function (element) {
	      var item = item_from_id(element.id);
	      add_item_to_cart(item);
	   }
	   );

	forEach(getElementsByTagAndClassName('input','sell-item-input'),
	   function (element) {
	      var item = item_from_id(element.id);
	      add_item_to_be_sold(item);
	   }
	   );

   add_food_to_buy_to_cart();
   add_doctor_visits_to_cart();
   add_school_costs_to_cart();
   add_family_assets_to_cart();
   add_bank_loan();
   total_cart();
   update_cash_display(cash);
}

function add_bank_loan() {
  if( $("microfinance_borrow") ) {
    var loan = parseFloat($("microfinance_borrow").value);
    bank_loan = loan;
  };
};

function add_food_to_buy_to_cart() {
   if ($('food-to-buy')) {
      var foodCost = parseFloat(scrapeText($('cost-of-food')).replace(/\,/g,""));
      var quantity_food_to_buy = $('food-to-buy').value;
      food_to_buy_cost = quantity_food_to_buy * foodCost;
   }
}

function add_doctor_visits_to_cart() {
   doctor_visits_cost = 0;
   if (!$('cost-of-doctor')) { return; }
   var doctorCost = parseFloat(scrapeText($('cost-of-doctor')).replace(/\,/g,""));
   forEach(getElementsByTagAndClassName('input','doctor-checkbox'),
	   function (element) {
	      if (element.checked) {
		 doctor_visits_cost += doctorCost;
	      }
	   }
	);
}

function add_school_costs_to_cart() {
   school_cost = 0;
   forEach(getElementsByTagAndClassName('input','enroll-secondary'),
	   function (element) {
	      if (element.checked) {
		 school_cost += 1;
	      }
	   }
	);
}

function add_family_assets_to_cart() {
   assets_total = parseFloat($('small_business_investment').value);
}

function init_shopping_cart() {
   cash = parseFloat(scrapeText($('cash')).replace(/\,/g,""));

   starting_cash = cash;
   forEach(getElementsByTagAndClassName('input','purchase-item-input'),
	   function (element) {
	      connect(element,'onchange',update_shopping_cart);
	      connect(element,'onfocus',update_shopping_cart);
	      connect(element,'onblur',update_shopping_cart);
	      connect(element,'plusminus',update_shopping_cart);
	      var item = item_from_id(element.id);
	      add_item_to_cart(item);
	   }
	   );
   forEach(getElementsByTagAndClassName('input','sell-item-input'),
	   function (element) {
	      connect(element,'onchange',update_shopping_cart);
	      connect(element,'onfocus',update_shopping_cart);
	      connect(element,'onblur',update_shopping_cart);
	      connect(element,'plusminus',update_shopping_cart);
	      var item = item_from_id(element.id);
	      add_item_to_be_sold(item);
	   }
	   );
   if ($('food-to-buy')) {
      connect($('food-to-buy'),'onchange',update_shopping_cart);
   }
   connect('small_business_investment','onchange',update_shopping_cart);
   forEach(getElementsByTagAndClassName('input','doctor-checkbox'),
	   function (element) {
	      connect(element,'onchange',update_shopping_cart);
	      connect(element,'onclick',update_shopping_cart);
	   }
	   );
   forEach(getElementsByTagAndClassName('input','enroll-secondary'),
	   function (element) {
	      connect(element,'onchange',update_shopping_cart);
	      connect(element,'onclick',update_shopping_cart);
	   }
	   );
   if( $("microfinance_borrow") ) {
     connect($("microfinance_borrow"), 'onchange', update_shopping_cart);
     connect($("microfinance_borrow"), 'onfocus', update_shopping_cart);
     connect($("microfinance_borrow"), 'onblur', update_shopping_cart);
     connect($("microfinance_borrow"), 'plusminus', update_shopping_cart);
   };
   add_food_to_buy_to_cart();
   add_doctor_visits_to_cart();
   add_school_costs_to_cart();
   total_cart();
   update_cash_display(cash);
}

addLoadEvent(init_shopping_cart);
