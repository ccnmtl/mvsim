
var healths = Array();

//<div class='hscale'><div class='hscale-inner' style='width:${person.health}px;'>
//	      &nbsp;&nbsp;${person.health}</div></div><br />

function update_doctor_visits() {
   forEach(getElementsByTagAndClassName('input','doctor-checkbox'),
	   function(element) {
	      var name = element.id.split('-')[1];
	      var original_health = healths[name];
	      if (element.checked) {
		var new_health;
		if( original_health > 90.0 ) {
		  new_health = 100;
		} else {
 		  var delta_health = (100.0 - original_health) / 2.0;
		  new_health = Math.round(original_health + delta_health);
		}
		 if (new_health > 100) { new_health = 100; }
		 $('health-' + name).innerHTML = new_health;
		 $('health-' + name + "-graphic").innerHTML = new_health;
		 $('hscale-' + name).style.width = new_health + "px";
		 // no more sickness
		 if ($('sick-' + name)) {
		       $('sick-' + name).style.color = '#666';
		 }
	      } else {
		 $('health-' + name).innerHTML = original_health;
		 $('health-' + name + "-graphic").innerHTML = original_health;
		 $('hscale-' + name).style.width = original_health + "px";

		 if ($('sick-' + name)) {
		    $('sick-' + name).style.color = '#000';
		 }
	      }
	   }
	   );
}


function init_doctor_visits() {
   // figure out initial health values
   forEach(getElementsByTagAndClassName('span','person-health'),
	   function(element) {
	      var name = element.id.split('-')[1];
	      healths[name] = parseInt(scrapeText(element));
	   }
	   );

   // add handlers
   forEach(getElementsByTagAndClassName('input','doctor-checkbox'),
	   function (element) {
	      connect(element,'onchange',update_doctor_visits);
	      connect(element,'onclick',update_doctor_visits);
	   }
	   );
}

addLoadEvent(init_doctor_visits);
