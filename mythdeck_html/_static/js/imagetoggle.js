jQuery(document).ready(function($){
  $('.changeable').on({
    'click': function(){
      if ($(this).hasClass('changed')) {
        $('.left-image').removeClass('changed');
        $('.right-image').removeClass('changed');
        $('.left-image').attr('src','../_images/default-left.png');
        $('.right-image').attr('src','../_images/default-right.png');
      } else {
        $('.left-image').addClass('changed');
        $('.right-image').addClass('changed');
        $('.left-image').attr('src','../_static/modeshift-left.png');
        $('.right-image').attr('src','../_static/modeshift-right.png');
      }
    }
  });
});
