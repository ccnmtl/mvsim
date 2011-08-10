
function enforceNotNegative (e) {

   forEach(getElementsByTagAndClassName('input','notnegative'),
	   function(element) {
	      if (!element) {
		 return;}
	      if (element.value < 0) {
		 element.value = 0;
	      }
	   });
}


function enforceMaxHundred (e) {

   forEach(getElementsByTagAndClassName('input','maxhundred'),
	   function(element) {
	      if (!element) {
		 return;}
	      if (element.value > 100) {
		 element.value = 100;
	      }
	   });
}


function initLimits() {
   // add handlers
   forEach(getElementsByTagAndClassName('input','notnegative'),
	   function (element) {
	      if (element.value < 0) { element.value = 0;}
	      connect(element,'onchange',enforceNotNegative);
	   }
	   );
   forEach(getElementsByTagAndClassName('input','maxhundred'),
	   function (element) {
	      if (element.value > 100) { element.value = 100;}
	      connect(element,'onchange',enforceMaxHundred);
	   }
	   );
}

addLoadEvent(initLimits);
