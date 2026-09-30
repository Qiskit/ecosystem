# Active projects

{{ read_csv('docs/assets/active_projects.csv') }}

# Active PyPI packages

{{ read_csv('docs/assets/active_pypi.csv') }}

# Active pip-installable repositories

Distributions that are declared in a repository but not published to a package registry.

{{ read_csv('docs/assets/pip_source.csv') }}

```vegalite 
{
  "title": "124 Projects",
  "data": {
    "values": [
      {"category": "Members (in website)", "value": 122},
      {"category": "Alumni (removed from website)", "value": 2}
    ]
  },
  "mark": {"type": "arc", "tooltip": true},
  "encoding": {
    "theta": {"field": "value", "type": "quantitative", "stack": "normalize"},
    "color": {"field": "category", "type": "nominal"}
  }
}
```


```vegalite 
{
  "title": "122 Members (in website)",
  "data": {
    "values": [
      {"category": "regular member", "value": 120},
      {"category": "under revision", "value": 1},
      {"category": "Qiskit Project", "value": 1}
    ]
  },
  "mark": {"type": "arc", "tooltip": true},
  "encoding": {
    "theta": {"field": "value", "type": "quantitative", "stack": "normalize"},
    "color": {"field": "category", "type": "nominal"}
  }
}
```

