import json
from io import StringIO
from django.core.management import call_command
from django.test import TestCase

class ModelMapCommandTests(TestCase):
    def test_output_structure(self):
        """We check that the command returns valid JSON and the correct structure."""
        out = StringIO()
        call_command('modelmap', 'tests', stdout=out)

        raw_output = out.getvalue()
        data = json.loads(raw_output)

        post_key = 'tests.Post'
        self.assertIn(post_key, data)
        post_data = data[post_key]

        self.assertIn('author', post_data['select_related_fields'])
        self.assertIn('parent', post_data['select_related_fields'])

        self.assertIn('tags', post_data['prefetch_related_fields'])
        self.assertIn('comments', post_data['prefetch_related_fields'])

    def test_snippet_generation(self):
        """We check that the snippet of the code is generated correctly."""
        out = StringIO()
        call_command('modelmap', 'tests', stdout=out)
        data = json.loads(out.getvalue())

        snippet = data['tests.Post']['queryset_snippet']

        self.assertIn("Post.objects", snippet)
        self.assertIn(".select_related(", snippet)
        self.assertIn(".prefetch_related(", snippet)
        self.assertIn("'author'", snippet)
        self.assertIn("'tags'", snippet)
