function toggleVillageView(e) {
  var id = e.src().id;
  if(id == 'VillageActions') {
    swapElementClass("graphic", "family-graphic", "village-graphic");
    hideElement("family-view");
    showElement("village-view");
  }
  else {
    swapElementClass("graphic", "village-graphic", "family-graphic");
    hideElement("village-view");
    showElement("family-view");
  }
}

function initVillageView() {
   // if village actions tab is showing,
   if(hasElementClass("family-actions-tab", "tabbertabhide")) {
      swapElementClass("graphic", "family-graphic", "village-graphic");
      hideElement("family-view");
      showElement("village-view");
   }
   
   connect("FamilyActions", "onclick", toggleVillageView);
   connect("VillageActions", "onclick", toggleVillageView);
}

addLoadEvent(initVillageView);