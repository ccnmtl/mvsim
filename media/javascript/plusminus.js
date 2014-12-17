// add plus and minus increment/decrement buttons to text inputs

function plusminus_original_id (id) {
   var parts = id.split('-');
   parts.pop();
   return parts.join('-');
}

function plus_clicked(e) {
   var input = $(plusminus_original_id(e.target().id));
   input.value++;
   if( input.name == 'purchase-fertilizer-quantity' && input.value > 1 )
       input.value = 1;
   if( input.name == 'purchase-high_yield_seeds-quantity' && input.value > 1 )
       input.value = 1;
   signal(input,'onchange');
}

function minus_clicked(e) {
   var input = $(plusminus_original_id(e.target().id));
   input.value--;
   if( input.name == 'purchase-fertilizer-quantity' && input.value > 1 )
       input.value = 1;
   if( input.name == 'purchase-high_yield_seeds-quantity' && input.value > 1 )
       input.value = 1;
   signal(input,'onchange');
}

function add_plus_minus_buttons(element) {
   var id = element.id;
   element.style.border = "1px solid black";
   var parent = element.parentNode;

   var plus = IMG({"src" : "../images/btn_plus.gif",
         "border": '0',"alt" : "+",
         "width" : "12",
         "height" : "14",
      "id" : id + "-plus",
      "class" : "plus-button"
   });

   var minus = IMG({"src" : "../images/btn_minus.gif",
         "border": '0',"alt" : "+",
         "width" : "12",
         "height" : "14",
      "id" : id + "-minus",
      "class" : "minus-button"
   });

   var placeholder = SPAN({'id' : 'plusminus-placeholder'});

   swapDOM(element,placeholder);

   var table = TABLE({'border' : '0','cellpadding' : '0','cellspacing' : '0'},
         TBODY({},
                     TR({},
                        TD({'rowSpan' : '2', 'style' : 'padding: 0px;'},
                           element
                           ),
                        TD({'style' : 'padding: 0px;'},plus)
                        ),
                     TR({},
                        TD({'style' : 'padding: 0px;'},minus)
                        )
                     ));

   swapDOM(placeholder,table);
   connect(plus,'onclick',plus_clicked);
   connect(minus,'onclick',minus_clicked);
}

function init_plusminus() {
   forEach(getElementsByTagAndClassName('input','plusminus'),
           function (element) {
              add_plus_minus_buttons(element);
           }
           );

}

addLoadEvent(init_plusminus);
