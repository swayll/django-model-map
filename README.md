# Django Model Map
[![Django CI](https://github.com/swayll/django-model-map/actions/workflows/django.yml/badge.svg)](https://github.com/swayll/django-model-map/actions/workflows/django.yml)
[![PyPI version](https://img.shields.io/pypi/v/django-model-map.svg)](https://pypi.org/project/django-model-map/)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-model-map.svg)](https://pypi.org/project/django-model-map/)
[![License](https://img.shields.io/pypi/l/django-model-map.svg)](https://github.com/swayll/django-model-map/blob/main/LICENSE)

**Stop guessing your query optimizations.**

`django-model-map` is a simple management command that inspects your Django models and outputs a JSON map of relationships. It explicitly categorizes relations into `select_related` and `prefetch_related` candidates, helping you avoid N+1 problems and write optimized QuerySets faster.

## Features

- **Automatic Classification**: Distinguishes between `select_related` (ForeignKey, OneToOne) and `prefetch_related` (ManyToMany, Reverse FK).
- **Deep Inspection**: Supports configurable nesting levels for mapping nested relationships (e.g., `prefetch_related('lvl1__lvl2__lvl3')`).
- **Reverse Relation Discovery**: Finds standard `_set` accessors and custom `related_name` attributes.
- **Recursion Detection**: Identifies self-referencing models.
- **GenericForeignKey**: Detects GFK fields and marks them in the output.
- **JSON / YAML Output**: Easy to read, parse, or integrate into other tools.

## Installation

```bash
pip install django-model-map

# With YAML output support (optional)
pip install django-model-map[yaml]
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'django_model_map',
    ...
]
```

## Usage

### CLI

```bash
# Inspect all installed apps
python manage.py modelmap

# Inspect a specific app
python manage.py modelmap [app_name]

# Named alternative to positional
python manage.py modelmap --app [app_name]

# Specify inspection nesting level (default: 1)
python manage.py modelmap [app_name] --depth 2

# Exclude models or entire apps (repeatable)
python manage.py modelmap --exclude auth.Permission --exclude auth.Group

# Save to file
python manage.py modelmap [app_name] --output relations.json

# YAML output (requires pip install django-model-map[yaml])
python manage.py modelmap [app_name] --format yaml
```

### Python API

```python
from django_model_map import get_model_map

# Inspect a specific app, depth 2, exclude some models
model_map = get_model_map(app_label='myapp', depth=2, exclude=['myapp.OldModel'])

for model_name, data in model_map.items():
    print(data['queryset_snippet'])
```

## Example Output

```json
{
    "blog.Post": {
        "queryset_snippet": "Post.objects.select_related('author', 'category').prefetch_related('tags', 'comments')",
        "select_related_fields": [
            "author",
            "category"
        ],
        "prefetch_related_fields": [
            "tags",
            "comments"
        ],
        "details": {
            "select_related": [
                {
                    "field_name": "author",
                    "target_model": "users.User",
                    "is_recursive": false
                },
                 ...
            ],
            "prefetch_related": [
                {
                    "field_name": "tags",
                    "target_model": "blog.Tag",
                    "is_recursive": false
                },
                {
                    "field_name": "content_object",
                    "target_model": "Generic",
                    "is_recursive": false,
                    "type": "generic"
                },
                ...
            ]
        }
    }
}
```

## How it helps

When writing a view, instead of opening `models.py` and mentally parsing the relationships, just look at the output. With the `--depth` argument, you can automatically discover deeply nested relationships that need optimization:

- Copy fields from `"queryset_snippet"` -> paste into project.
- Copy fields from `"select_related_fields"` -> paste into `.select_related(...)`.
- Copy fields from `"prefetch_related_fields"` -> paste into `.prefetch_related(...)`.

## Contributing

Pull requests are welcome! For major changes, please open an issue first.

## License

[MIT](https://github.com/swayll/django-model-map/blob/main/LICENSE)
