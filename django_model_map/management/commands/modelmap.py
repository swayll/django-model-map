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

    def handle(self, *args, **options):
        app_label = options.get('app_label')

        models_map = {}

        # We get a list of models (either all or a specific application)
        if app_label:
            models = apps.get_app_config(app_label).get_models()
        else:
            models = apps.get_models()

        for model in models:
            model_name = f"{model._meta.app_label}.{model.__name__}"

            # Classification lists
            select_candidates = []   # ForeignKey (forward), OneToOne
            prefetch_candidates = [] # ManyToMany, Reverse ForeignKey (XXX_set)

            # Iterating through ALL fields, including feedbacks (get_fields() sees everything)
            for field in model._meta.get_fields():

                # We ignore the usual fields, we are only interested in connections.
                if not field.is_relation:
                    continue

                # We get the name of the attribute through which we access the connection.
                # For direct fields, this is field.name (for example, 'author')
                # For the reverse, this is get_accessor_name() (for example, 'author_set' or related_name)
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

                # We define the type of connection and the target model
                target_model = field.related_model._meta.label if field.related_model else "Generic"
                is_self = field.related_model == model

                info = {
                    "field_name": name,
                    "target_model": target_model,
                    "is_recursive": is_self
                }

                # Separation logic select vs prefetch

                # 1. Many-to-One (Reverse) or Many-to-Many -> PREFETCH
                if field.many_to_many or (field.one_to_many):
                    prefetch_candidates.append(info)

                # 2. Many-to-One (Forward/ForeignKey) or One-to-One -> SELECT
                # (field.many_to_one means that THIS model has a FK to another one)
                elif field.many_to_one or field.one_to_one:
                    select_candidates.append(info)

            models_map[model_name] = {
                "select_related (JOIN)": select_candidates,
                "prefetch_related (2nd Query)": prefetch_candidates
            }

        # Output in JSON
        self.stdout.write(json.dumps(models_map, indent=4, ensure_ascii=False))
