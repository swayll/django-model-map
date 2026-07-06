__version__ = '0.4.0'

from django.apps import apps as django_apps

from .analyzer import build_snippet, discover_relations


def get_model_map(app_label=None, depth=1, exclude=None):
    if app_label:
        django_models = django_apps.get_app_config(app_label).get_models()
    else:
        django_models = django_apps.get_models()

    if exclude:
        exclude_set = set(exclude)
        if app_label:
            django_models = [
                m for m in django_models if f'{m._meta.app_label}.{m.__name__}' not in exclude_set
            ]
        else:
            django_models = [
                m
                for m in django_models
                if f'{m._meta.app_label}.{m.__name__}' not in exclude_set
                and m._meta.app_label not in exclude_set
            ]

    models_map = {}
    for model in django_models:
        model_name = f'{model._meta.app_label}.{model.__name__}'
        select, prefetch = discover_relations(model, max_depth=depth)

        models_map[model_name] = {
            'queryset_snippet': build_snippet(model, select, prefetch),
            'select_related_fields': [x['field_name'] for x in select],
            'prefetch_related_fields': [x['field_name'] for x in prefetch],
            'details': {
                'select_related': select,
                'prefetch_related': prefetch,
            },
        }

    return models_map
