# Django Model Map
[![Django CI](https://github.com/swayll/django-model-map/actions/workflows/django.yml/badge.svg)](https://github.com/swayll/django-model-map/actions/workflows/django.yml)
[![PyPI version](https://img.shields.io/pypi/v/django-model-map.svg)](https://pypi.org/project/django-model-map/)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-model-map.svg)](https://pypi.org/project/django-model-map/)
[![License](https://img.shields.io/pypi/l/django-model-map.svg)](https://github.com/swayll/django-model-map/blob/main/LICENSE)

**Stop guessing your query optimizations.**

`django-model-map` is a simple management command that inspects your Django models and outputs a JSON map of relationships. It explicitly categorizes relations into `select_related` and `prefetch_related` candidates, helping you avoid N+1 problems and write optimized QuerySets faster.

## 🚀 Features

- **Automatic Classification**: Distinguishes between `select_related` (ForeignKey, OneToOne) and `prefetch_related` (ManyToMany, Reverse FK).
- **Reverse Relation Discovery**: Finds standard `_set` accessors and custom `related_name` attributes.
- **Recursion Detection**: Identifies self-referencing models.
- **JSON Output**: Easy to read, parse, or integrate into other tools.

## 📦 Installation

Install via pip:

```bash
pip install django-model-map
```
Add it to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'django_model_map',
    ...
]
```

## 🛠 Usage

```bash
# Inspect all installed apps
python manage.py modelmap

# Inspect a specific app
python manage.py modelmap [app_name]

# Save to file for reference using stdout
python manage.py modelmap [app_name] > relations.json
# or export to file with command
python manage.py modelmap [app_name] [--output[-o]] relations.json
```
## 📖 Example Output
For a blog application with `Post`, `User`, `Tag` and `Comment` models:
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
            "select_objects": [
                {
                    "field_name": "author",
                    "target_model": "users.User",
                    "is_recursive": false
                },
                 ...
            ],
            "prefetch_objects": [...]
        }
    }
}
```
## 💡 How it helps
When writing a view, instead of opening `models.py` and mentally parsing the relationships, just look at the output:
- Copy fields from `"queryset_snippet"` -> paste into project.
- Copy fields from `"select_related"` -> paste into `.select_related(...)`.
- Copy fields from `"prefetch_related"` -> paste into `.prefetch_related(...)`.
## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📄 License
[MIT](https://github.com/swayll/django-model-map/tree/main#MIT-1-ov-file)
