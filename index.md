---
title: paul mccarthy
layout: page
---
{% include JB/setup %}

I'm an Australian living in the UK. I work as a software engineer, and enjoy a range of outdoor activities. I occasionally write accounts of what I've been up to in my spare time:

<ul class="posts">
  {% for post in site.posts limit:5 %}
    <li><span>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url }}">{{ post.title }}</a></li>
  {% endfor %}

  <li><span><a href="{{ BASE_PATH }}/archive.html">more...</a></span></li>
</ul>
