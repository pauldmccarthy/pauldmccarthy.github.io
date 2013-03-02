$(function() {

  $(".picasa-gallery").each(function(_i, el) {

    var $el      = $(el);
    var user_id  = $el.attr("user_id");
    var album_id = $el.attr("album_id");

    var image_cmp = function(img1, img2) {
      var i1n = img1.title.slice(0, img1.title.lastIndexOf('.'));
      var i2n = img2.title.slice(0, img2.title.lastIndexOf('.'));
      return parseInt(i1n) - parseInt(i2n);
    };

    $el.picasaGallery(user_id, album_id, function(images) {
      $ul = $('<ul class="picasa-album"></ul>');

      images.sort(image_cmp);

      $.each(images, function(i, img) {
        var $li  = $('<li class="picasa-image"></li>'),
            $a   = $('<a class="picasa-image-large"></a>').attr('href', img.url),
            $img = $('<img class="picasa-image-thumb" />').attr('src', img.thumbs[1].url);
        if (!/\.(jpg|png|gif)$/i.test(img.title)) {
          $a.attr('title', img.title);
        }
        $a.append($img); $li.append($a); $ul.append($li);
      });
      $el.append($ul).find('a.picasa-image-large').slimbox({
        loop: true,
        resizeDuration: 1,
        imageFadeDuration: 1
      });
    });
  });
});
