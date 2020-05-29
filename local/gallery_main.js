
$( document ).ready(function(){
	var myscroller = document.scrollingElement || document.documentElement;
	var myticker = null;
	var scrollspeed = 5;
	$("body").keydown(function(e){
		//console.log(e)
		myticker && (clearInterval(myticker), myticker = null);
		if(document.activeElement.localName!="input")
		{
			
			//console.log("Handling");
			if(e.originalEvent.key=="ArrowRight")
			{
				if(typeof(onarrow_next_handler)=="function")
					{onarrow_next_handler();return false;}
				if(typeof(onarrow_next_page)=="string")
					{window.location.assign(onarrow_next_page);return false;}
				return;
			}
			if(e.originalEvent.key=="ArrowLeft")
			{
				if(typeof(onarrow_prev_handler)=="function")
					{onarrow_prev_handler();return false;}
				if(typeof(onarrow_prev_page)=="string")
					{return window.location.assign(onarrow_prev_page);return false;}
				return;
			}
			if(e.originalEvent.key=="ArrowDown")
			{
				myticker = setInterval(function() {
                        myscroller.scrollTop += scrollspeed
                    }, 5);
				return;
			}
			if(e.originalEvent.key=="ArrowUp")
			{
				myticker = setInterval(function() {
                        myscroller.scrollTop -= scrollspeed
                    }, 5);
				return;
			}
			
		}
		
	});

	$("body").keyup(function(e){
		 myticker && (clearInterval(myticker), myticker = null);
	});
	
	if(typeof(page_url_override)=="string")
	{
		history.replaceState({}, document.title, page_url_override);
	}
});