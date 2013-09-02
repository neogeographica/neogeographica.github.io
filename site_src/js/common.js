/**
 * Some versions of some browsers will apply focus style to the link that
 * was used to leave the page, when you return using the back button.  Let's
 * not do that.
 */

jQuery(document).ready(function(){
  jQuery('a').blur();
});
