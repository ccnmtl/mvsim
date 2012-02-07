// add plus and minus increment/decrement buttons to text inputs

function force_integer(e) {
  var input = e.target();
  if (isNaN(input.value)) {
    input.value = input.value.replace(/\D/g,"");
  }
  if (input.value === '') {
    input.value = 0;
  }
  input.value = parseInt(input.value);
}

function init_force_integer() {
   forEach(getElementsByTagAndClassName('input','forceinteger'),
           function (element) {
	     connect(element,'onchange',force_integer);
           }
   );
}

addLoadEvent(init_force_integer);
