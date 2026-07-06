import json
from typing import Any

from django.core.management.base import BaseCommand

from django_model_map import get_model_map


class Command(BaseCommand):
    help = 'Generates a JSON/YAML map of model relationships for query optimization'

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            'app_label', nargs='?', type=str, help='Application name (optional, use -a/--app)'
        )
        parser.add_argument(
            '-a', '--app', type=str, help='Application name (named alternative to positional)'
        )
        parser.add_argument('-o', '--output', type=str, help='File path to save the result')
        parser.add_argument(
            '-d',
            '--depth',
            type=int,
            default=1,
            help='Maximum depth of nesting for relations (default: 1)',
        )
        parser.add_argument(
            '-e',
            '--exclude',
            action='append',
            default=None,
            help='Exclude a model (app.Model) or entire app (app). Repeatable.',
        )
        parser.add_argument(
            '-f',
            '--format',
            type=str,
            default='json',
            choices=['json', 'yaml'],
            help='Output format: json or yaml (default: json)',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        app_label = options.get('app') or options.get('app_label')
        output_file = options.get('output')
        max_depth = options.get('depth')
        exclude = options.get('exclude')
        fmt = options.get('format')

        models_map = get_model_map(app_label=app_label, depth=max_depth, exclude=exclude)

        if fmt == 'yaml':
            try:
                import yaml
            except ImportError:
                self.stderr.write(
                    self.style.ERROR(
                        'PyYAML is required for YAML output. '
                        'Install with: pip install django-model-map[yaml]'
                    )
                )
                return
            output_data = yaml.dump(models_map, allow_unicode=True, sort_keys=False)
        else:
            output_data = json.dumps(models_map, indent=4, ensure_ascii=False)

        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(output_data)
                self.stdout.write(self.style.SUCCESS(f'Saved to file: {output_file}'))
            except OSError as e:
                self.stderr.write(self.style.ERROR(f'File write error: {e}'))
        else:
            self.stdout.write(output_data)
