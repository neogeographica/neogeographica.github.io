// jqModal initialization
jQuery(document).ready(function(){
  jQuery('.jqmWindow').each(function(){
    $(this).jqm({
      overlay: 100,
      trigger: "#trigger-" + $(this).attr('id'),
      onShow: function(h) {
        h.o.hide();
        h.o.fadeIn(200);
        h.w.fadeIn(200);
      }
    });
  });
});
