var gametypesEnabled = 0;

// Enable button to show the popup, default to CTF gametype, prep the popup.
jQuery(document).ready(function(){
  jQuery('#popup').show();
  setGametype(0);
  jQuery('#overview').jqm({
    overlay: 100,
    onShow: function(h) {
      h.o.hide();
      h.o.fadeIn(200);
      h.w.fadeIn(200);
    }
  });
});

// Turn the mapview on or off.
function toggleMap() {
  jQuery('#mapview').toggle();
};

// Change the kinds of visible icons... this is triggered by clicking
// on the armor, weapons, or powerups checkbox in the form.
function toggleType(prefix) {
  var iconIndex = 0,
      iconId = prefix + iconIndex,
      icon = jQuery(iconId),
      bitfield;
  while (icon.length != 0) {
    if (icon.is(':visible')) {
      icon.hide();
    }
    else {
      bitfield = jQuery(iconId+'Img').attr('name');
      if (bitfield & gametypesEnabled) {
        icon.show();
      }
    }
    iconIndex++;
    iconId = prefix + iconIndex;
    icon = jQuery(iconId);
  }
};

// Show all the icons of a particular kind for the current gametype.
function showGametypeIcons(prefix) {
  var iconIndex = 0,
      iconId = prefix + iconIndex,
      icon = jQuery(iconId),
      bitfield;
  while (icon.length != 0) {
    bitfield = jQuery(iconId+'Img').attr('name');
    if (bitfield & gametypesEnabled) {
      icon.show();
    }
    else {
      icon.hide();
    }
    iconIndex++;
    iconId = prefix + iconIndex;
    icon = jQuery(iconId);
  }
};

// Change the gametype and then display the correct icons... this is
// triggered by clicking on a gametype radiobutton in the form.
function setGametype(bitpos) {
  gametypesEnabled = 1 << bitpos;
  if (jQuery('#armorCheck').is(':checked')) {
    showGametypeIcons('#a');
  }
  if (jQuery('#weaponsCheck').is(':checked')) {
    showGametypeIcons('#w');
  }
  if (jQuery('#powerupsCheck').is(':checked')) {
    showGametypeIcons('#p');
  }
  if (jQuery('#spawnsCheck').is(':checked')) {
    showGametypeIcons('#s');
  }
  if (jQuery('#respawnsCheck').is(':checked')) {
    showGametypeIcons('#r');
  }
  showGametypeIcons('#m');
  showGametypeIcons('#f');
};
