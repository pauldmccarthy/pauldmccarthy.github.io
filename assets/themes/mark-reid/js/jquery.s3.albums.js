(function($) {

    var local_s3_store = true;

    // Retrieves the album index, passes
    // it to the provided callback.
    $.s3_index = function(bucket, region, album, callback) {

        var indexUrl;

        if (local_s3_store) {
            indexUrl = "http://localhost:8000/" + album  + ".json?callback=?";
        }

        else {
        indexUrl = "http://"         + bucket +
                   ".s3-"            + region +
                   ".amazonaws.com/" + album  + ".json?callback=?";
        }

        $.ajax({
            url           : indexUrl,
            dataType      : "jsonp",
            jsonpCallback : 'jsonp',
            crossDomain   : true,
            success       :  function(index) {
                callback(index);
            }});
    };

    $.s3_image_url = function(bucket,
                              region,
                              album,
                              image,
                              width,
                              height) {

        var imgName = image.substr(0, image.lastIndexOf("."));
        var imgSuf  = image.substr(   image.lastIndexOf("."));
        var imgUrl; 

        if (local_s3_store) {

            imgUrl = "http://localhost:8000/"   + album  +
                     "/"                        + imgName +
                     "_" + width + "_" + height + imgSuf;
        }
        else {  
            imgUrl  = "http://"         + bucket  +
                      ".s3-"            + region  +
                      ".amazonaws.com/" + album   +
                      "/"               + imgName +
                      "_" + width + "_" + height + imgSuf;
        }

        
        return imgUrl;
    };

    $.s3_best_size = function(image, index, maxwidth, maxheight) {
        
        var sizes = index[image];

        // Sort the sizes into decreasing order
        sizes.sort(function(s1, s2) { return s1[0] > s2[0] ? -1 : s1[0] < s2[0] ? 1 : 0});

        var bestw = -1;
        var besth = -1;

        for (var i = 0; i < sizes.length; i++) {

            var w = sizes[i][0];
            var h = sizes[i][1];

            if (w <= maxwidth && h <= maxheight) {
                bestw = w;
                besth = h;
                break;
            }
        }

        // Fall back to the smallest
        // available image
        if (bestw == -1) {
            bestw = sizes[sizes.length - 1][0];
            besth = sizes[sizes.length - 1][1];
        }

        return [bestw, besth];
    };


    // Returns  a url to an appropriately sized 
    // image to the provided callback.
    $.s3_image = function(bucket,
                          region,
                          album,
                          image,
                          index,
                          maxwidth,
                          maxheight) {

        if (!(image in index)) {
            return undefined;
        }

        var bestw;
        var besth;

        [bestw, besth] = $.s3_best_size(image, index, maxwidth, maxheight);
        return $.s3_image_url(bucket, region, album, image, bestw, besth);

    };

    $.s3_gallery = function(bucket, region, album, elemid) {

        $.s3_index(bucket, region, album, function(index) {

            var thumbUrls = $.map(index, function(sizes, image) {
                return $.s3_image(bucket, region, album, image, index, 1, 1);
            });

            var fullUrls = $.map(index, function(sizes, image) {
                return $.s3_image(
                    bucket, region, album, image, index,
                    $(window).width()  - 50,
                    $(window).height() - 50);
            }); 

            var $elem = $(elemid);

            var $ul = $("<ul class=\"s3_gallery_list\"></ul>");

            $.each(thumbUrls, function(i) {

                var thumbUrl = thumbUrls[i];
                var fullUrl  = fullUrls[ i];

                var $li  = $("<il class=\"s3_image_gallery_item\"></li>");
                var $a   = $("<a class=\"s3_image_gallery_link\"></a>");
                var $img = $("<img class=\"s3_image_gallery_thumb\"></img>");

                $a  .attr("href", fullUrl);
                $img.attr("src",  thumbUrl)

                $ul.append($li);
                $li.append($a);
                $a .append($img);
            });

            $elem.append($ul).find('a.s3_image_gallery_link').slimbox({
                loop: true,
                resizeDuration: 1,
                imageFadeDuration: 1
            }); 
        });
    };

    $.s3_strip = function(bucket, region, album, index, elem, images) {
        
        // gaargh, it should be easier to
        // get the visible size of an element.
        // Thanks http://stackoverflow.com/a/26831113
        var visHeight = function($el) {
            var elH = $el.outerHeight(),
                H   = $(window).height(),
                r   = $el[0].getBoundingClientRect(), t=r.top, b=r.bottom;
            return Math.max(0, t>0? Math.min(elH, H-t) : (b<H?b:H));
        }

        var $elem = $(elem);

        var elWidth  = $elem.parent().width();
        var elHeight = visHeight($elem.parent());
        var rowWidth = elWidth;

        var thumbSizes = images.map(function(i) {
            return $.s3_best_size(i, index, rowWidth / images.length, 99999);});

        var thumbWidths  = thumbSizes.map(function(s) { return s[0]; });
        var thumbHeights = thumbSizes.map(function(s) { return s[1]; });
        var thumbUrls    = images.map(function(image, i) {
            return $.s3_image_url(
                bucket,
                region,
                album,
                image,
                thumbWidths[i],
                thumbHeights[i]);
        });
        
        var fullUrls = images.map(function(image) {
            return $.s3_image(
                bucket,
                region,
                album,
                image,
                index,
                $(window).width()  - 50,
                $(window).height() - 50); 
        });

        // Allow space for 2px padding
        // on either side of each image -
        // see screen.css
        rowWidth -= 4 * images.length;

        // resize images so they fit horizontally
        var ttlWidth = thumbWidths.reduce( function(a, b) { return a + b; });

        for (var i = 0; i < images.length; i++) {

            thumbWidths[ i] *= rowWidth / ttlWidth;
            thumbHeights[i] *= rowWidth / ttlWidth;
        };

        thumbUrls.map(function(imgUrl, i) {

            var $a   = $("<a class=\"s3_image_strip_link\"></a>").attr("href", fullUrls[i]);
            var $img = $("<img/>")
                .attr("src",    imgUrl)
                .attr("width",  thumbWidths[i])
                .attr("height", thumbHeights[i]);

            $a.append($img)

            $elem.append($a).find('a.s3_image_strip_link').slimbox({
                loop: true,
                resizeDuration: 1,
                imageFadeDuration: 1
            });
        });
    };
})(jQuery);
