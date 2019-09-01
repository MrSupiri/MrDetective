$(document).ready(function() {
    $('#loading').hide();
    // Each time the user scrolls
    $(window).scroll(function() {
       if($(window).scrollTop() + $(window).height() > $(document).height() -100) {
            $('#loading').show();

            $.ajax({
                url: '/'+clan+'/load/',
                dataType: 'html',
                success: function(html) {
                    $('#screenshots').append(html);
                    $('#loading').hide();
                }
            });
       }
    });
});

(function($) {
    var $window = $(window),
        x = document.getElementById("card-holder");

    $window.resize(function resize() {
        if ($window.width() > 750 && $window.width() < 975) {
            x.style.fontSize = "0.7rem";
        }
        else {
            x.style.fontSize = "1rem";
        }
        // alert($window.width());
    }).trigger('resize');
})(jQuery);

function sharenow(ssid) {
    window.open ('//www.facebook.com/sharer/sharer.php?u=https://mrdetective.supiritech.com/ba/'+clan+'/ss/'+ssid,'','width=250, height=250, scrollbars=yes');
}

function copy_link() {
  var copyText = document.getElementById("clipboard_link");
  copyText.select();
  document.execCommand("Copy");
  $("#clipboard").modal('toggle');
}

function copy_clipboard(ssid) {
    document.getElementById("clipboard_link").value = 'https://mrdetective.supiritech.com/'+clan+'/ss/'+ssid;
    $("#clipboard").modal();
}

function correct_ss(ssid) {
    select_ss = ssid;
    document.getElementById("correct-ss-text").innerHTML = 'Screenshot: <b>#'+select_ss+'</b>';
    $("#correct-prediction").modal();
}

function update_ai() {

}

function show_ss(image_array, clan_name) {

    for(var i = 0; i < image_array.length; i++) {
        document.getElementById("view-ss-"+i).innerHTML = ': '+image_array[i];
    }

    $("#view-screenshot").modal();

    document.getElementById("view-ss-img").src = '/static/screenshots/'+clan_name+'/'+image_array[0]+'.jpg';
    // document.getElementById("view-ss-img").src = '/static/'+clan+'/screenshots/'+image_array[0]+'.jpg';
}

function update_search(value) {
    document.getElementById("search_type").value = value;
}
