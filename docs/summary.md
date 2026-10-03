# The ecosystem at a glance

<div class="grid" markdown>

```vegalite
{
  "title": {
    "text": "Projects by status",
    "subtitle": "in the website, then status, then age"
  },
  "data": {
    "url": "assets/summary_status.json"
  },
  "encoding": {
    "theta": {
      "field": "count",
      "type": "quantitative",
      "stack": true
    },
    "order": {
      "field": "order",
      "type": "quantitative"
    },
    "color": {
      "field": "label",
      "type": "nominal",
      "sort": null,
      "title": null
    },
    "href": {
      "field": "url",
      "type": "nominal"
    },
    "tooltip": [
      {
        "field": "label",
        "type": "nominal",
        "title": " "
      },
      {
        "field": "count",
        "type": "quantitative",
        "title": "projects"
      },
      {
        "field": "share",
        "type": "quantitative",
        "title": "share",
        "format": ".1%"
      }
    ]
  },
  "layer": [
    {
      "transform": [
        {
          "filter": "datum.ring == 1"
        }
      ],
      "mark": {
        "type": "arc",
        "radius": 0,
        "radius2": 45,
        "stroke": "white"
      }
    },
    {
      "transform": [
        {
          "filter": "datum.ring == 1"
        }
      ],
      "mark": {
        "type": "text",
        "radius": 22.5,
        "fontSize": 10
      },
      "encoding": {
        "text": {
          "field": "share",
          "type": "quantitative",
          "format": ".0%"
        },
        "color": {
          "value": "white"
        },
        "opacity": {
          "condition": {
            "test": "datum.share >= 0.06",
            "value": 1
          },
          "value": 0
        }
      }
    },
    {
      "transform": [
        {
          "filter": "datum.ring == 2"
        }
      ],
      "mark": {
        "type": "arc",
        "radius": 48,
        "radius2": 78,
        "stroke": "white"
      }
    },
    {
      "transform": [
        {
          "filter": "datum.ring == 2"
        }
      ],
      "mark": {
        "type": "text",
        "radius": 63.0,
        "fontSize": 10
      },
      "encoding": {
        "text": {
          "field": "share",
          "type": "quantitative",
          "format": ".0%"
        },
        "color": {
          "value": "white"
        },
        "opacity": {
          "condition": {
            "test": "datum.share >= 0.06",
            "value": 1
          },
          "value": 0
        }
      }
    },
    {
      "transform": [
        {
          "filter": "datum.ring == 3"
        }
      ],
      "mark": {
        "type": "arc",
        "radius": 81,
        "radius2": 108,
        "stroke": "white"
      }
    },
    {
      "transform": [
        {
          "filter": "datum.ring == 3"
        }
      ],
      "mark": {
        "type": "text",
        "radius": 94.5,
        "fontSize": 10
      },
      "encoding": {
        "text": {
          "field": "share",
          "type": "quantitative",
          "format": ".0%"
        },
        "color": {
          "value": "white"
        },
        "opacity": {
          "condition": {
            "test": "datum.share >= 0.06",
            "value": 1
          },
          "value": 0
        }
      }
    }
  ],
  "height": 260,
  "view": {
    "stroke": null
  }
}
```

```vegalite
{
  "title": {
    "text": "Members by maturity",
    "subtitle": "support promised, then maturity declared"
  },
  "data": {
    "url": "assets/summary_maturity.json"
  },
  "encoding": {
    "theta": {
      "field": "count",
      "type": "quantitative",
      "stack": true
    },
    "order": {
      "field": "order",
      "type": "quantitative"
    },
    "color": {
      "field": "label",
      "type": "nominal",
      "sort": null,
      "title": null
    },
    "href": {
      "field": "url",
      "type": "nominal"
    },
    "tooltip": [
      {
        "field": "label",
        "type": "nominal",
        "title": " "
      },
      {
        "field": "count",
        "type": "quantitative",
        "title": "members"
      },
      {
        "field": "share",
        "type": "quantitative",
        "title": "share",
        "format": ".1%"
      }
    ]
  },
  "layer": [
    {
      "transform": [
        {
          "filter": "datum.ring == 1"
        }
      ],
      "mark": {
        "type": "arc",
        "radius": 0,
        "radius2": 60,
        "stroke": "white"
      }
    },
    {
      "transform": [
        {
          "filter": "datum.ring == 1"
        }
      ],
      "mark": {
        "type": "text",
        "radius": 30.0,
        "fontSize": 10
      },
      "encoding": {
        "text": {
          "field": "share",
          "type": "quantitative",
          "format": ".0%"
        },
        "color": {
          "value": "white"
        },
        "opacity": {
          "condition": {
            "test": "datum.share >= 0.06",
            "value": 1
          },
          "value": 0
        }
      }
    },
    {
      "transform": [
        {
          "filter": "datum.ring == 2"
        }
      ],
      "mark": {
        "type": "arc",
        "radius": 63,
        "radius2": 108,
        "stroke": "white"
      }
    },
    {
      "transform": [
        {
          "filter": "datum.ring == 2"
        }
      ],
      "mark": {
        "type": "text",
        "radius": 85.5,
        "fontSize": 10
      },
      "encoding": {
        "text": {
          "field": "share",
          "type": "quantitative",
          "format": ".0%"
        },
        "color": {
          "value": "white"
        },
        "opacity": {
          "condition": {
            "test": "datum.share >= 0.06",
            "value": 1
          },
          "value": 0
        }
      }
    }
  ],
  "height": 260,
  "view": {
    "stroke": null
  }
}
```

```vegalite
{
  "title": {
    "text": "Where a member's code comes from",
    "subtitle": "published or not, then where from"
  },
  "data": {
    "url": "assets/summary_packaging.json"
  },
  "encoding": {
    "theta": {
      "field": "count",
      "type": "quantitative",
      "stack": true
    },
    "order": {
      "field": "order",
      "type": "quantitative"
    },
    "color": {
      "field": "label",
      "type": "nominal",
      "sort": null,
      "title": null
    },
    "href": {
      "field": "url",
      "type": "nominal"
    },
    "tooltip": [
      {
        "field": "label",
        "type": "nominal",
        "title": " "
      },
      {
        "field": "count",
        "type": "quantitative",
        "title": "members"
      },
      {
        "field": "share",
        "type": "quantitative",
        "title": "share",
        "format": ".1%"
      }
    ]
  },
  "layer": [
    {
      "transform": [
        {
          "filter": "datum.ring == 1"
        }
      ],
      "mark": {
        "type": "arc",
        "radius": 0,
        "radius2": 60,
        "stroke": "white"
      }
    },
    {
      "transform": [
        {
          "filter": "datum.ring == 1"
        }
      ],
      "mark": {
        "type": "text",
        "radius": 30.0,
        "fontSize": 10
      },
      "encoding": {
        "text": {
          "field": "share",
          "type": "quantitative",
          "format": ".0%"
        },
        "color": {
          "value": "white"
        },
        "opacity": {
          "condition": {
            "test": "datum.share >= 0.06",
            "value": 1
          },
          "value": 0
        }
      }
    },
    {
      "transform": [
        {
          "filter": "datum.ring == 2"
        }
      ],
      "mark": {
        "type": "arc",
        "radius": 63,
        "radius2": 108,
        "stroke": "white"
      }
    },
    {
      "transform": [
        {
          "filter": "datum.ring == 2"
        }
      ],
      "mark": {
        "type": "text",
        "radius": 85.5,
        "fontSize": 10
      },
      "encoding": {
        "text": {
          "field": "share",
          "type": "quantitative",
          "format": ".0%"
        },
        "color": {
          "value": "white"
        },
        "opacity": {
          "condition": {
            "test": "datum.share >= 0.06",
            "value": 1
          },
          "value": 0
        }
      }
    }
  ],
  "height": 260,
  "view": {
    "stroke": null
  }
}
```

```vegalite
{
  "title": {
    "text": "Member repositories by year created",
    "subtitle": [
      "by github.created_at, the repository's own age",
      "stacked by the maturity declared"
    ]
  },
  "data": {
    "url": "assets/summary_years.json"
  },
  "height": 200,
  "mark": {
    "type": "bar"
  },
  "encoding": {
    "x": {
      "field": "year",
      "type": "ordinal",
      "title": null,
      "axis": {
        "labelAngle": 0
      }
    },
    "y": {
      "field": "count",
      "type": "quantitative",
      "title": "repositories",
      "stack": true
    },
    "tooltip": [
      {
        "field": "year",
        "type": "ordinal",
        "title": "created in"
      },
      {
        "field": "maturity",
        "type": "nominal",
        "title": "maturity"
      },
      {
        "field": "count",
        "type": "quantitative",
        "title": "repositories"
      },
      {
        "field": "share",
        "type": "quantitative",
        "title": "share",
        "format": ".1%"
      }
    ],
    "color": {
      "field": "maturity",
      "type": "nominal",
      "sort": null,
      "title": null
    },
    "href": {
      "field": "url",
      "type": "nominal"
    }
  }
}
```

</div>

# Active projects

{{ read_csv('docs/assets/active_projects.csv') }}

# Active PyPI packages

{{ read_csv('docs/assets/active_pypi.csv') }}

# Active pip-installable repositories

Distributions that are declared in a repository but not published to a package registry.

{{ read_csv('docs/assets/pip_source.csv') }}

# Active crates

{{ read_csv('docs/assets/active_crates.csv') }}

# Active cargo-installable repositories

Crates that are declared in a repository but not published to crates.io. A project depends on
one of these through its git URL.

{{ read_csv('docs/assets/cargo_source.csv') }}


