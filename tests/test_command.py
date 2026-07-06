import json
import os
import tempfile
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

        self.assertIn('Post.objects', snippet)
        self.assertIn('.select_related(', snippet)
        self.assertIn('.prefetch_related(', snippet)
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

    def test_output_file(self):
        """Test that -o/--output writes JSON to a file."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            call_command('modelmap', 'tests', '--output', tmp_path)
            with open(tmp_path) as f:
                data = json.load(f)
            self.assertIn('tests.Post', data)
        finally:
            os.unlink(tmp_path)

    def test_all_apps(self):
        """Test that calling without app_label returns all apps' models."""
        out = StringIO()
        call_command('modelmap', stdout=out)
        data = json.loads(out.getvalue())
        self.assertIn('tests.Post', data)

    def test_no_relations(self):
        """Test model with no relation fields produces empty lists and .all()."""
        out = StringIO()
        call_command('modelmap', 'tests', stdout=out)
        data = json.loads(out.getvalue())

        solo_key = 'tests.SoloModel'
        self.assertIn(solo_key, data)
        solo = data[solo_key]
        self.assertEqual(solo['select_related_fields'], [])
        self.assertEqual(solo['prefetch_related_fields'], [])
        self.assertTrue(solo['queryset_snippet'].endswith('.all()'))

    def test_related_name_plus(self):
        """Test that related_name='+' does not appear in reverse relations."""
        out = StringIO()
        call_command('modelmap', 'tests', stdout=out)
        data = json.loads(out.getvalue())

        post_data = data['tests.Post']
        all_fields = post_data['select_related_fields'] + post_data['prefetch_related_fields']
        self.assertNotIn('hiddenpost_set', all_fields)
        self.assertNotIn('hiddenpost', all_fields)

    def test_generic_relation(self):
        """Test that GenericForeignKey appears with type 'generic'."""
        out = StringIO()
        call_command('modelmap', 'tests', stdout=out)
        data = json.loads(out.getvalue())

        article_data = data['tests.Article']
        gfk_found = False
        for item in article_data['details']['prefetch_related']:
            if item['field_name'] == 'content_object':
                self.assertEqual(item['type'], 'generic')
                gfk_found = True
        self.assertTrue(gfk_found, 'GenericForeignKey content_object not found')

        snippet = article_data['queryset_snippet']
        self.assertNotIn('content_object', snippet)

    def test_yaml_output(self):
        """Test --format yaml produces valid YAML."""
        try:
            import yaml
        except ImportError:
            self.skipTest('PyYAML not installed')

        out = StringIO()
        call_command('modelmap', 'tests', '--format', 'yaml', stdout=out)
        data = yaml.safe_load(out.getvalue())
        self.assertIn('tests.Post', data)

    def test_exclude_model(self):
        """Test --exclude removes a specific model from output."""
        out = StringIO()
        call_command('modelmap', 'tests', '--exclude', 'tests.SoloModel', stdout=out)
        data = json.loads(out.getvalue())
        self.assertNotIn('tests.SoloModel', data)
        self.assertIn('tests.Post', data)

    def test_app_flag(self):
        """Test --app works the same as positional app_label."""
        out_pos = StringIO()
        out_named = StringIO()
        call_command('modelmap', 'tests', stdout=out_pos)
        call_command('modelmap', '--app', 'tests', stdout=out_named)
        self.assertEqual(out_pos.getvalue(), out_named.getvalue())
