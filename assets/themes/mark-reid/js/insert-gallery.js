$(function() {

  $(".picasa-gallery").each(function(_i, el) {

    var $el      = $(el);
    var user_id  = $el.attr("user_id");
    var album_id = $el.attr("album_id");

    $el.picasaGallery(user_id, album_id, function(images) {
      $ul = $('<ul class="picasa-album"></ul>');
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
