---
layout: nil
title : Atom Feed (wrapped for jsonp)
---
atom_jsonp([
  {% for post in site.posts limit:4 %}
  {
    link:"{{ site.production_url }}{{ post.id }}",
    title:"{{ post.title }}",
    content:"{{ post.content | strip_newlines | xml_escape }}"
  },
  {% endfor %}
  {
    link:"{{ site.production_url }}{{ site.posts[4].id }}",
    title:"{{ site.posts[4].title }}",
    content:"{{ site.posts[4].content | strip_newlines | xml_escape }}"
  }
]);
