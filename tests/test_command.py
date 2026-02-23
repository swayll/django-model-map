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

    def test_depth_argument(self):
        """Test if --depth argument works correctly."""
        out = StringIO()
        call_command('modelmap', 'tests', '--depth', '2', stdout=out)
        data = json.loads(out.getvalue())

        post_data = data['tests.Post']

        # Level 1
        self.assertIn('author', post_data['select_related_fields'])
        # Level 2
        self.assertIn('author__user', post_data['select_related_fields'])

        # Test snippet
        snippet = post_data['queryset_snippet']
        self.assertIn("'author'", snippet)
        self.assertIn("'author__user'", snippet)

    def test_nested_prefetch(self):
        """Test if nested prefetch relations are correctly identified."""
        out = StringIO()
        call_command('modelmap', 'tests', '--depth', '2', stdout=out)
        data = json.loads(out.getvalue())

        post_data = data['tests.Post']

        # Post -> comments (prefetch)
        # Comment -> post (select, but since it's under prefetch, it becomes prefetch)
        self.assertIn('comments', post_data['prefetch_related_fields'])
        self.assertIn('comments__post', post_data['prefetch_related_fields'])

    def test_depth_three(self):
        """Test if 3rd level nesting works."""
        out = StringIO()
        call_command('modelmap', 'tests', '--depth', '3', stdout=out)
        data = json.loads(out.getvalue())

        post_data = data['tests.Post']

        # Post -> author -> post_set -> author
        self.assertIn('author__post_set__author', post_data['prefetch_related_fields'])
