
{{ obj.software['machine_name']|color(fg='cyan', bold=True)}}:{{obj.version|color(fg='cyan', bold=True)}}:
  id          :     {{ obj.id|color(fg='white') }}
  sha         :     {{ obj.sha|color(fg='white') }}
  released_by :     {% if obj.released_by['notes'] %}{{ obj.released_by["fullname"] }} <{{ obj.released_by["email"] }}> [{{obj.released_by["notes"]}}]{% else %}{{ obj.released_by["fullname"] }} <{{ obj.released_by["email"] }}>{% endif %}
  released    :     {{ obj.release_time.strftime("%b %d, %Y %I:%M:%S %p")|color(fg='white') }}
  ===
  created     :     {{ obj.created.strftime("%b %d, %Y %I:%M:%S %p")|color(fg='white') }}
  modified    :     {{ obj.modified.strftime("%b %d, %Y %I:%M:%S %p")|color(fg='white') }}

{% filter color(fg='green') %}  Changelog:{% endfilter %}

{{ obj.changelog|indent(4, True) }}
