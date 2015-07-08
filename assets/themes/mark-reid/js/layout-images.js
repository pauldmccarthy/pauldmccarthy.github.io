$(function() {

    // gaargh, it should be easier to
    // get the visible size of an element.
    // Thanks http://stackoverflow.com/a/26831113
    var visHeight = function($el) {
        var elH = $el.outerHeight(),
            H   = $(window).height(),
            r   = $el[0].getBoundingClientRect(), t=r.top, b=r.bottom;
        return Math.max(0, t>0? Math.min(elH, H-t) : (b<H?b:H));
    }

    $(".layout-images").each(function(li, el) {

        var $el = $(el);

        var elWidth  = $el.parent().width();
        var elHeight = visHeight($el.parent());

        var rowWidth  = elWidth;

        var userId  = $el.attr("data-user");
        var albumId = $el.attr("data-album");
        var pics    = $el.attr("data-pics");

        pics = pics.split(";");
        pics = pics.map(function(p) { return p.toLowerCase(); });

        $.picasa.images(userId, albumId, function(images) {

            images = images.filter(function(i) {
                filename = i.url.split("/").pop().toLowerCase();
                return pics.indexOf(filename) > -1;
            });

            // Allow space for 2px padding
            // on either side of each image -
            // see screen.css
            rowWidth -= 4 * images.length;

            var imgWidths  = images.map(function(e) { return e.width;  });
            var imgHeights = images.map(function(e) { return e.height; });

            // shrink images so they fit horizontally
            var ttlWidth = imgWidths.reduce( function(a, b) { return a + b; });
            if (ttlWidth > rowWidth) {
                
                var shrink = 1.0 * rowWidth / ttlWidth;
                for (var i = 0; i < images.length; i++) {

                    imgWidths[ i] *= shrink;
                    imgHeights[i] *= shrink;
                };
            };

            // // shrink images so they all have the same height
            // var minHeight = imgHeights.reduce(function(a, b) { return a < b ? a : b; });
            // for (var i = 0; i < images.length; i++) {

            //     var width  = imgWidths[ i];
            //     var height = imgHeights[i];

            //     if (height <= minHeight)
            //         continue;

            //     var shrink = 1.0 * minHeight / height;
                
            //     imgWidths[ i] *= shrink;
            //     imgHeights[i] *= shrink; 
            // };

            images.map(function(image, i) {

                var $a   = $("<a class=\"picasa-image-large\"></a>").attr("href", image.url);
                var $img = $("<img/>", {
                    src    : image.url,
                    width  : imgWidths[ i],
                    height : imgHeights[i]
                });

                $a.append($img)

                $el.append($a).find('a.picasa-image-large').slimbox({
                    loop: true,
                    resizeDuration: 1,
                    imageFadeDuration: 1
                });
            });
        });
    });
});
