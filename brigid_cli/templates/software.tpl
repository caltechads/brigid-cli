
{{ obj.name|color(fg='cyan', bold=True) }}:
  id          :     {{ obj.id|color(fg='white') }}
  machine_name:     {{ obj.machine_name|color(fg='white') }}
  description :     {{ obj.description|color(fg='white') }}
  created     :     {{ obj.created.strftime("%b %d, %Y %I:%M:%S %p")|color(fg='white') }}
  modified    :     {{ obj.modified.strftime("%b %d, %Y %I:%M:%S %p")|color(fg='white') }}
{% filter color(fg='green') %}  Authors:{% endfilter %}
{% for author in obj.authors %}    {% if author['notes'] %}{{ author["fullname"] }} <{{ author["email"] }}> [{{author["notes"]}}]{% else %}{{ author["fullname"] }} <{{ author["email"] }}>{% endif %}
{% endfor %}
{%- filter color(fg='green') %}  Git repository:{% endfilter %}
    repo_url :     {{ obj.git_repo_url|color(fg='white') }}
    created  :     {{ obj.repo_created.strftime("%b %d, %Y %I:%M:%S %p")|color(fg='white') }}
    modified :     {{ obj.repo_modified.strftime("%b %d, %Y %I:%M:%S %p")|color(fg='white') }}
{% filter color(fg='green') %}  Related URLs: {% endfilter %}
    Docs     :     {{ obj.trello_board_url|color(fg='white') }}
    Trello   :     {{ obj.documentation_url|color(fg='white') }}
    Code drop:     {{ obj.artifact_repo_url|color(fg='white') }}
