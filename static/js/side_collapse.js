$(document).ready(function(){
    $('.sidebar_collapse').on('click',function(){
        if($(this).hasClass("fa-chevron-left")){
            document.documentElement.style.setProperty("--content-ratio", ".8");
            $(this).removeClass("fa-chevron-left");
            $(this).addClass("fa-chevron-right")
        }else{
            document.documentElement.style.setProperty("--content-ratio", ".6");
            $(this).removeClass("fa-chevron-right");
            $(this).addClass("fa-chevron-left");
        }
    });
  });
