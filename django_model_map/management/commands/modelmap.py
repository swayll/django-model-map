import json
from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
    """
    Generates a JSON map of model relationships for query optimization
    """

    help = 'Generates a JSON map of model relationships for query optimization'

    def add_arguments(self, parser):
        parser.add_argument('app_label', nargs='?', type=str, help='Application name (optional)')
        # A new argument to save to a file
        parser.add_argument(
            '-o', '--output',
            type=str,
            help='The path to the file to save the result (for example, app_name_map.json) (optional)'
        )
        parser.add_argument(
            '-d', '--depth',
            type=int,
            default=1,
            help='The maximum depth of nesting for relations (default: 1)'
        )

    def discover_relations(self, model, max_depth, current_depth=1, prefix='', is_pure_select=True):
        select_candidates = []
        prefetch_candidates = []

        if current_depth > max_depth:
            return select_candidates, prefetch_candidates

        for field in model._meta.get_fields():
            if not field.is_relation:
                continue

            try:
                if field.auto_created and not field.concrete:
                    # This is a Reverse relationship
                    name = field.get_accessor_name()
                    # If related_name='+', there is no access, skip
                    if not name:
                        continue
                else:
                    # It's a direct connection. (Forward relation)
                    name = field.name
            except Exception:
                continue

            target_model = field.related_model
            target_model_label = target_model._meta.label if target_model else "Generic"
            is_self = target_model == model

            full_name = f"{prefix}{name}"

            info = {
                "field_name": full_name,
                "target_model": target_model_label,
                "is_recursive": is_self
            }

            # Separation logic select vs prefetch
            is_field_pure_select = False

            # 1. Many-to-One (Reverse) or Many-to-Many -> PREFETCH
            if field.many_to_many or field.one_to_many:
                prefetch_candidates.append(info)
                is_field_pure_select = False

            # 2. Many-to-One (Forward/ForeignKey) or One-to-One -> SELECT (if path is pure select)
            elif field.many_to_one or field.one_to_one:
                if is_pure_select:
                    select_candidates.append(info)
                    is_field_pure_select = True
                else:
                    prefetch_candidates.append(info)
                    is_field_pure_select = False
            else:
                continue

            # Recursive call for nesting
            if current_depth < max_depth and target_model:
                s, p = self.discover_relations(
                    target_model,
                    max_depth,
                    current_depth + 1,
                    f"{full_name}__",
                    is_field_pure_select
                )
                select_candidates.extend(s)
                prefetch_candidates.extend(p)

        return select_candidates, prefetch_candidates

    def handle(self, *args, **options):
        app_label = options.get('app_label')
        output_file = options.get('output')
        max_depth = options.get('depth')

        models_map = {}

        # We get a list of models (either all or a specific application)
        if app_label:
            try:
                models = apps.get_app_config(app_label).get_models()
            except LookupError:
                self.stderr.write(self.style.ERROR(f"The application '{app_label}' was not found."))
                return
        else:
            models = apps.get_models()

        for model in models:
            model_name = f"{model._meta.app_label}.{model.__name__}"

            select_candidates, prefetch_candidates = self.discover_relations(model, max_depth)

            # --- SNIPPET GENERATION ---
            # Creating lists of field names
            select_names = [f"'{x['field_name']}'" for x in select_candidates]
            prefetch_names = [f"'{x['field_name']}'" for x in prefetch_candidates]

            # Collecting a line of code
            snippet = f"{model.__name__}.objects"

            if select_names:
                snippet += f".select_related({', '.join(select_names)})"

            if prefetch_names:
                snippet += f".prefetch_related({', '.join(prefetch_names)})"

            # If there is nothing, add .all()
            if not select_names and not prefetch_names:
                snippet += ".all()"

            # Collecting the final object
            models_map[model_name] = {
                "queryset_snippet": snippet,  # Ready-made code to copy
                "select_related_fields": [x['field_name'] for x in select_candidates],
                "prefetch_related_fields": [x['field_name'] for x in prefetch_candidates],
                "details": { # Detailed information (if you need to figure out the connections)
                    "select_related": select_candidates,
                    "prefetch_related": prefetch_candidates
                }
            }

        # --- SAVE / OUTPUT ---
        json_output = json.dumps(models_map, indent=4, ensure_ascii=False)

        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(json_output)
                self.stdout.write(self.style.SUCCESS(f"Successfully saved to a file: {output_file}"))
            except IOError as e:
                self.stderr.write(self.style.ERROR(f"File recording error: {e}"))
        else:
            self.stdout.write(json_output)
