function parseCash(text) {
  text = text.replace(/\,/g,"");
  return parseFloat(text);
};

jQuery(window).load(function() {
  forEach(getElementsByTagAndClassName('input','village_improvement_choice'),
	function(el) {
	  connect(el, 'onchange', update_village_fund);
	});
  });

function update_village_fund(e) {
  var el = e._src;
  var price = jQuery(el).closest("tr").find("span.village_improvement_price").text();
  price = parseCash(price);
  var fund = getVillageFund();
  if( jQuery(el).attr("checked") ) {
    fund -= price;
  } else {
    fund += price;
  };
  var money = format_money(fund);
  jQuery("#village_fund_amount").text(money);
};

function getVillageFund() {
  var fund = jQuery("#village_fund_amount").text();
  var fund = parseCash(fund);
  return fund;
};

