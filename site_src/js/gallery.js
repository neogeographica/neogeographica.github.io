/**
 * This first function block is from Galleria v1.0 
 * http://devkick.com/lab/galleria/
 * Modified by Joel Baxter as follows:
 * - removed history code, since if you aren't using it, it can bugger up the
 *   default image display when you return to a previously-loaded page
 * - removed caption code, just because I don't need it
 * - disabled clickable image links while images are loading
 * - added support for multiple galleries per page
 *
 * Galleria is copyright (c) 2008 David Hellsing
 * Licensed under the GPL licenses.
 * http://www.gnu.org/licenses/gpl.txt
 */

(function($){

var $$;


/**
 * 
 * @desc Convert images from a simple html <ul> into a thumbnail gallery
 * @author David Hellsing
 * @version 1.0
 *
 * @name Galleria
 * @type jQuery
 *
 * @cat plugins/Media
 * 
 * @example $('ul.gallery').galleria({options});
 * @desc Create a a gallery from an unordered list of images with thumbnails
 * @options
 *   insert:   (selector string) by default, Galleria will create a container div before your ul that holds the image.
 *             You can, however, specify a selector where the image will be placed instead (f.ex '#main_img')
 *   clickNext:boolean helper for adding a clickable image that leads to the next one in line
 *   onImage:  (function) a function that gets fired when the image is displayed and brings the jQuery image object.
 *             You can use it to add click functionality and effects.
 *             f.ex onImage(image) { image.css('display','none').fadeIn(); } will fadeIn each image that is displayed
 *   onThumb:  (function) a function that gets fired when the thumbnail is displayed and brings the jQuery thumb object.
 *             Works the same as onImage except it targets the thumbnail after it's loaded.
 *
**/

$$ = $.fn.galleria = function($options) {
	
	// check for basic CSS support
	if (!$$.hasCSS()) { return false; }

	// pre-loop to disable clickable links while images load (new code)
	this.each(function(){
		$(this).children('li').each(function(i) {
			var _a = $(this).find('a').is('a') ? $(this).find('a') : false;
			if (_a) {
				_a.click(function(){return false;});
			}
		});
	});
	
	// set default options
	var $defaults = {
		insert      : '.galleria_container',
		clickNext   : true,
		onImage     : function(image,thumb) {},
		onThumb     : function(thumb) {}
	};

	// extend the options
	var $opts = $.extend($defaults, $options);
	
	// bring the options to the galleria object
	for (var i in $opts) {
		if (i) {
			$.galleria[i]  = $opts[i];
		}
	}
	
	// if no insert selector, create a new division and insert it before the ul
	var _insert = ( $($opts.insert).is($opts.insert) ) ? 
		$($opts.insert) : 
		jQuery(document.createElement('div')).insertBefore(this);
		
	// create a wrapping div for the image
	var _div = $(document.createElement('div')).addClass('galleria_wrapper');
	
	// inject the wrapper in in the insert selector
	_insert.addClass('galleria_container').append(_div);
	
	//-------------
	
	return this.each(function(){
		
		// add the Galleria class
		$(this).addClass('galleria');

		// find the gallery instance class (if any) and make a selector of it
		var _instanceSelector = $(this).attr('class').match(/\bgalleria_instance_\S+/);
		if (!_instanceSelector) {
			_instanceSelector = '';
		} else {
			_instanceSelector = '.'+_instanceSelector;
		}

		// loop through list
		$(this).children('li').each(function(i) {
			
			// bring the scope
			var _container = $(this);
			                
			// build element specific options
			var _o = $.meta ? $.extend({}, $opts, _container.data()) : $opts;
			
			// remove the clickNext if image is only child
			_o.clickNext = $(this).is(':only-child') ? false : _o.clickNext;
			
			// try to fetch an anchor
			var _a = $(this).find('a').is('a') ? $(this).find('a') : false;
			
			// reference the original image as a variable and hide it
			var _img = $(this).children('img').css('display','none');
			
			// extract the original source
			var _src = _a ? _a.attr('href') : _img.attr('src');
			
			// find a title
			var _title = _a ? _a.attr('title') : _img.attr('title');
			
			// create loader image            
			var _loader = new Image();
		
			// begin loader
			$(_loader).load(function () {
				
				// try to bring the alt
				$(this).attr('alt',_img.attr('alt'));
				
				//-----------------------------------------------------------------
				// the image is loaded, let's create the thumbnail
				
				var _thumb = _a ? 
					_a.find('img').addClass('thumb noscale').css('display','none') :
					_img.clone(true).addClass('thumb').css('display','none');
				
				if (_a) { _a.replaceWith(_thumb); }
				
				if (!_thumb.hasClass('noscale')) { // scaled thumbnails!
					var w = Math.ceil( _img.width() / _img.height() * _container.height() );
					var h = Math.ceil( _img.height() / _img.width() * _container.width() );
					if (w < h) {
						_thumb.css({ height: 'auto', width: _container.width(), marginTop: -(h-_container.height())/2 });
					} else {
						_thumb.css({ width: 'auto', height: _container.height(), marginLeft: -(w-_container.width())/2 });
					}
				} else { // Center thumbnails.
					// a tiny timer fixed the width/height
					window.setTimeout(function() {
						_thumb.css({
							marginLeft: -( _thumb.width() - _container.width() )/2, 
							marginTop:  -( _thumb.height() - _container.height() )/2
						});
					}, 1);
				}
				
				// add the rel attribute
				_thumb.attr('rel',_src);
				
				// add the title attribute
				_thumb.attr('title',_title);
				
				// add the click functionality to the _thumb
				_thumb.click(function() {
					$.galleria.activate(_src, _instanceSelector);
				});
				
				// hover classes for IE6
				_thumb.hover(
					function() { $(this).addClass('hover'); },
					function() { $(this).removeClass('hover'); }
				);
				_container.hover(
					function() { _container.addClass('hover'); },
					function() { _container.removeClass('hover'); }
				);

				// prepend the thumbnail in the container
				_container.prepend(_thumb);
				
				// show the thumbnail
				_thumb.css('display','block');
				
				// call the onThumb function
				_o.onThumb(jQuery(_thumb));
				
				// check active class and activate image if match
				if (_container.hasClass('active')) {
					$.galleria.activate(_src, _instanceSelector);
					//_span.text(_title);
				}
				
				//-----------------------------------------------------------------
				
				// finally delete the original image
				_img.remove();
				
			}).error(function () {
				
				// Error handling
			    _container.html('<span class="error" style="color:red">Error loading image: '+_src+'</span>');
			
			}).attr('src', _src);
		});
	});
};

/**
 *
 * @name NextSelector
 *
 * @desc Returns the sibling sibling, or the first one
 *
**/

$$.nextSelector = function(selector) {
	return $(selector).is(':last-child') ?
		   $(selector).siblings(':first-child') :
    	   $(selector).next();
    	   
};

/**
 *
 * @name previousSelector
 *
 * @desc Returns the previous sibling, or the last one
 *
**/

$$.previousSelector = function(selector) {
	return $(selector).is(':first-child') ?
		   $(selector).siblings(':last-child') :
    	   $(selector).prev();
    	   
};

/**
 *
 * @name hasCSS
 *
 * @desc Checks for CSS support and returns a boolean value
 *
**/

$$.hasCSS = function()  {
	$('body').append(
		$(document.createElement('div')).attr('id','css_test').css({ width:'1px', height:'1px', display:'none' })
	);
	var _v = ($('#css_test').width() != 1) ? false : true;
	$('#css_test').remove();
	return _v;
};

/**
 *
 * @name onPageLoad
 *
 * @desc The function that displays the image and alters the active classes
 *
**/

$$.onPageLoad = function(_src, _instanceSelector) {
	// get the wrapper
	var _wrapper = $('div'+_instanceSelector+' > .galleria_wrapper');
	
	// get the thumb
	var _thumb = $('.galleria'+_instanceSelector+' img[rel="'+_src+'"]');
	
	if (_src) {

		// alter the active classes
		_thumb.parents('li').siblings('.active').removeClass('active');
		_thumb.parents('li').addClass('active');
	
		// define a new image
		var _img   = $(new Image()).attr('src',_src).addClass('replaced');

		// empty the wrapper and insert the new image
		_wrapper.empty().append(_img);
		
		// fire the onImage function to customize the loaded image's features
		$.galleria.onImage(_img,_thumb);
		
		// add clickable image helper
		if($.galleria.clickNext) {
			_img.css('cursor','pointer').click(function() { $.galleria.next(_instanceSelector); });
		}
		
	} else {

		// clean up the container if none are active
		_wrapper.siblings().andSelf().empty();
		
		// remove active classes
		$('.galleria'+_instanceSelector+' li.active').removeClass('active');
	}

	// place the source in the galleria.current variable
	$.galleria.current[_instanceSelector] = _src;
	
};

/**
 *
 * @name jQuery.galleria
 *
 * @desc The global galleria object holds one variable and three public methods:
 *       $.galleria.current = is the current source that's being viewed, per instance
 *       $.galleria.next(_instanceSelector) = displays the next image in line, returns to first image after the last.
 *       $.galleria.prev(_instanceSelector) = displays the previous image in line, returns to last image after the first.
 *       $.galleria.activate(_src, _instanceSelector) = displays an image from _src in the instance's galleria container.
 *
**/

$.extend({galleria : {
	current : [],
	activate : function(_src, _instanceSelector) { 
		$$.onPageLoad(_src, _instanceSelector);
	},
	next : function(_instanceSelector) {
		var _next = $($$.nextSelector($('.galleria'+_instanceSelector+' img[rel="'+$.galleria.current[_instanceSelector]+'"]').parents('li'))).find('img').attr('rel');
		$.galleria.activate(_next, _instanceSelector);
	},
	prev : function(_instanceSelector) {
		var _prev = $($$.previousSelector($('.galleria'+_instanceSelector+' img[rel="'+$.galleria.current[_instanceSelector]+'"]').parents('li'))).find('img').attr('rel');
		$.galleria.activate(_prev, _instanceSelector);
	}
}
});

})(jQuery);




/* Stuff below is NOT part of the Galleria code per se. */




/**
 * Function to remove the noscript warning in the gallery and replace it with
 * a display area.  Also apply styles to the rest of the gallery area that are
 * appropriate for having the Galleria code operational.
 */

jQuery(document).ready(function(){
  jQuery('.gallery_noscript').remove();
  jQuery('.gallery').addClass('gallery_galleria');
  jQuery('.gallery_display').addClass('gallery_display_galleria');
  jQuery('.gallery_1rowthumbs').addClass('gallery_1rowthumbs_galleria');
  jQuery('.gallery_2rowthumbs').addClass('gallery_2rowthumbs_galleria');
});


/**
 * Function for applying Galleria to the image gallery thumbnail list.
 * This is just a tweak of the similar function from the Galleria demo.
 */

jQuery(function($) {
  jQuery('ul.thumbnail_picker').galleria({
    clickNext: true,
    insert: '.gallery_display',
    onImage: function(image,thumb) {
      if (!($.browser.mozilla && navigator.appVersion.indexOf("Win")!=-1)) {
        image.css('display','none').fadeIn(500);
      }
      var _li = thumb.parents('li');
      _li.siblings().children('img.selected').removeClass('selected').fadeTo(500,0.3);
      thumb.fadeTo('fast',1).addClass('selected');
    },
    onThumb: function(thumb) {
      var _li = thumb.parents('li');
      var _fadeTo = _li.is('.active') ? '1' : '0.3';
      thumb.css({display:'none',opacity:_fadeTo}).fadeIn(1500);
      thumb.hover(
        function() { thumb.fadeTo('fast',1); },
        function() { _li.not('.active').children('img').fadeTo('fast',0.3); }
      )
    }
  });
});
