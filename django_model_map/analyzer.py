from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import models

if TYPE_CHECKING:
    pass


def discover_relations(
    model: type[models.Model],
    max_depth: int = 1,
    current_depth: int = 1,
    prefix: str = '',
    is_pure_select: bool = True,
) -> tuple[list[dict], list[dict]]:
    select_candidates: list[dict] = []
    prefetch_candidates: list[dict] = []

    if current_depth > max_depth:
        return select_candidates, prefetch_candidates

    for field in model._meta.get_fields():
        if not field.is_relation:
            continue

        try:
            if field.auto_created and not field.concrete:
                name = field.get_accessor_name()
                if not name:
                    continue
            else:
                name = field.name
        except Exception:
            continue

        target_model = field.related_model
        if target_model is None:
            continue
        target_model_label = target_model._meta.label
        is_self = target_model == model
        full_name = f'{prefix}{name}'

        info: dict[str, Any] = {
            'field_name': full_name,
            'target_model': target_model_label,
            'is_recursive': is_self,
        }

        if field.many_to_many or field.one_to_many:
            prefetch_candidates.append(info)
            is_field_pure_select = False
        elif field.many_to_one or field.one_to_one:
            if is_pure_select:
                select_candidates.append(info)
                is_field_pure_select = True
            else:
                prefetch_candidates.append(info)
                is_field_pure_select = False
        else:
            continue

        if current_depth < max_depth and target_model:
            s, p = discover_relations(
                target_model, max_depth, current_depth + 1, f'{full_name}__', is_field_pure_select
            )
            select_candidates.extend(s)
            prefetch_candidates.extend(p)

    from django.contrib.contenttypes.fields import GenericForeignKey

    for field in model._meta.private_fields:
        if isinstance(field, GenericForeignKey):
            info = {
                'field_name': field.name,
                'target_model': 'Generic',
                'is_recursive': False,
                'type': 'generic',
            }
            prefetch_candidates.append(info)

    return select_candidates, prefetch_candidates


def build_snippet(model: type[models.Model], select: list[dict], prefetch: list[dict]) -> str:
    select_names = [f"'{x['field_name']}'" for x in select]
    prefetch_names = [f"'{x['field_name']}'" for x in prefetch if x.get('type') != 'generic']

    snippet = f'{model.__name__}.objects'
    if select_names:
        snippet += f'.select_related({", ".join(select_names)})'
    if prefetch_names:
        snippet += f'.prefetch_related({", ".join(prefetch_names)})'
    if not select_names and not prefetch_names:
        snippet += '.all()'
    return snippet
