API Reference
=============

The API reference provides detailed descriptions of eElib's classes and methods. 
This is taken from the implementations of the models, which can be taken from the 
*public Gitlab-Repository <https://gitlab.com/elenia1/elenia-energy-library>*.

.. toctree::
   :titlesonly:
   :maxdepth: 2

   {% for page in pages %}
   {% if page.top_level_object and page.display %}
   {{ page.include_path }}
   {% endif %}
   {% endfor %}
