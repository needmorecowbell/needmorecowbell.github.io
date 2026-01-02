#!/usr/bin/env python3
"""
Tests for the hugo_writer module.

Uses unittest (standard library) for compatibility.
"""

import os
import tempfile
import unittest
from pathlib import Path

from hugo_writer import (
    write_hugo_post,
    write_hugo_post_routed,
    get_output_path,
    preview_hugo_post,
    format_frontmatter,
    _format_field,
    _quote_if_needed
)


class TestQuoteIfNeeded(unittest.TestCase):
    """Tests for the _quote_if_needed helper function."""

    def test_simple_string_no_quotes(self):
        """Test that simple strings don't get quoted."""
        result = _quote_if_needed('simple')
        self.assertEqual(result, 'simple')

    def test_empty_string_gets_quotes(self):
        """Test that empty strings get quoted."""
        result = _quote_if_needed('')
        self.assertEqual(result, '""')

    def test_string_with_colon_gets_quoted(self):
        """Test that strings with colons get quoted."""
        result = _quote_if_needed('Title: Subtitle')
        self.assertEqual(result, '"Title: Subtitle"')

    def test_string_with_hash_gets_quoted(self):
        """Test that strings with hash get quoted."""
        result = _quote_if_needed('My #1 Post')
        self.assertEqual(result, '"My #1 Post"')

    def test_string_with_brackets_gets_quoted(self):
        """Test that strings with brackets get quoted."""
        result = _quote_if_needed('[Updated]')
        self.assertEqual(result, '"[Updated]"')

    def test_string_with_leading_space_gets_quoted(self):
        """Test that strings with leading whitespace get quoted."""
        result = _quote_if_needed(' leading space')
        self.assertEqual(result, '" leading space"')

    def test_string_with_trailing_space_gets_quoted(self):
        """Test that strings with trailing whitespace get quoted."""
        result = _quote_if_needed('trailing space ')
        self.assertEqual(result, '"trailing space "')

    def test_boolean_words_get_quoted(self):
        """Test that boolean-like words get quoted."""
        self.assertEqual(_quote_if_needed('true'), '"true"')
        self.assertEqual(_quote_if_needed('false'), '"false"')
        self.assertEqual(_quote_if_needed('yes'), '"yes"')
        self.assertEqual(_quote_if_needed('no'), '"no"')

    def test_null_words_get_quoted(self):
        """Test that null-like words get quoted."""
        self.assertEqual(_quote_if_needed('null'), '"null"')
        self.assertEqual(_quote_if_needed('none'), '"none"')

    def test_numbers_as_strings_get_quoted(self):
        """Test that number-like strings get quoted."""
        self.assertEqual(_quote_if_needed('123'), '"123"')
        self.assertEqual(_quote_if_needed('3.14'), '"3.14"')

    def test_existing_quotes_get_escaped(self):
        """Test that existing double quotes in strings get escaped."""
        result = _quote_if_needed('Say "Hello"')
        self.assertEqual(result, '"Say \\"Hello\\""')

    def test_single_word_no_quotes(self):
        """Test that single words without special chars don't get quoted."""
        result = _quote_if_needed('python')
        self.assertEqual(result, 'python')


class TestFormatField(unittest.TestCase):
    """Tests for the _format_field helper function."""

    def test_string_field(self):
        """Test formatting a string field."""
        result = _format_field('title', 'My Post')
        self.assertEqual(result, 'title: My Post')

    def test_string_field_with_special_chars(self):
        """Test formatting a string field with special characters."""
        result = _format_field('title', 'My Post: An Adventure')
        self.assertEqual(result, 'title: "My Post: An Adventure"')

    def test_boolean_true(self):
        """Test formatting a boolean true field."""
        result = _format_field('draft', True)
        self.assertEqual(result, 'draft: true')

    def test_boolean_false(self):
        """Test formatting a boolean false field."""
        result = _format_field('draft', False)
        self.assertEqual(result, 'draft: false')

    def test_integer_field(self):
        """Test formatting an integer field."""
        result = _format_field('weight', 10)
        self.assertEqual(result, 'weight: 10')

    def test_empty_list(self):
        """Test formatting an empty list."""
        result = _format_field('tags', [])
        self.assertEqual(result, 'tags: []')

    def test_list_of_strings(self):
        """Test formatting a list of strings."""
        result = _format_field('tags', ['python', 'hugo', 'blog'])
        self.assertEqual(result, 'tags: [python, hugo, blog]')

    def test_list_with_special_chars(self):
        """Test formatting a list with special characters in items."""
        result = _format_field('tags', ['C++', 'C#'])
        # C# has a # that requires quoting
        self.assertIn('"C#"', result)

    def test_none_value(self):
        """Test formatting a None value."""
        result = _format_field('description', None)
        self.assertEqual(result, 'description:')


class TestFormatFrontmatter(unittest.TestCase):
    """Tests for the format_frontmatter function."""

    def test_empty_frontmatter(self):
        """Test formatting empty frontmatter."""
        result = format_frontmatter({})
        self.assertEqual(result, '---\n---')

    def test_simple_frontmatter(self):
        """Test formatting simple frontmatter."""
        frontmatter = {'title': 'My Post'}
        result = format_frontmatter(frontmatter)
        self.assertIn('---', result)
        self.assertIn('title: My Post', result)

    def test_frontmatter_field_order(self):
        """Test that frontmatter fields are in preferred order."""
        frontmatter = {
            'tags': ['test'],
            'title': 'My Post',
            'date': '2024-01-15',
            'draft': False
        }
        result = format_frontmatter(frontmatter)
        lines = result.split('\n')
        # Find positions of fields
        title_pos = next(i for i, l in enumerate(lines) if 'title:' in l)
        date_pos = next(i for i, l in enumerate(lines) if 'date:' in l)
        draft_pos = next(i for i, l in enumerate(lines) if 'draft:' in l)
        tags_pos = next(i for i, l in enumerate(lines) if 'tags:' in l)
        # Verify order: title < date < draft < tags
        self.assertLess(title_pos, date_pos)
        self.assertLess(date_pos, draft_pos)
        self.assertLess(draft_pos, tags_pos)

    def test_frontmatter_with_all_common_fields(self):
        """Test formatting frontmatter with all common Hugo fields."""
        frontmatter = {
            'title': 'My Amazing Post',
            'subtitle': 'A subtitle',
            'author': 'Adam Musciano',
            'date': '2024-01-15',
            'draft': False,
            'description': 'A description of my post',
            'headerimg': '/img/header.jpg',
            'tags': ['python', 'hugo'],
            'categories': ['tech'],
            'series': ['tutorial']
        }
        result = format_frontmatter(frontmatter)
        self.assertIn('title: My Amazing Post', result)
        self.assertIn('subtitle: A subtitle', result)
        self.assertIn('author: Adam Musciano', result)
        self.assertIn('date: 2024-01-15', result)
        self.assertIn('draft: false', result)
        self.assertIn('description: A description of my post', result)
        # headerimg contains a path, verify the content is there
        self.assertIn('headerimg:', result)
        self.assertIn('/img/header.jpg', result)
        self.assertIn('tags: [python, hugo]', result)
        self.assertIn('categories: [tech]', result)
        self.assertIn('series: [tutorial]', result)

    def test_custom_fields_preserved(self):
        """Test that custom/unknown fields are included."""
        frontmatter = {
            'title': 'Test',
            'custom_field': 'custom_value'
        }
        result = format_frontmatter(frontmatter)
        self.assertIn('custom_field: custom_value', result)


class TestPreviewHugoPost(unittest.TestCase):
    """Tests for the preview_hugo_post function."""

    def test_simple_preview(self):
        """Test generating a simple preview."""
        frontmatter = {'title': 'My Post', 'date': '2024-01-15'}
        body = 'This is my post content.'
        result = preview_hugo_post(frontmatter, body)
        self.assertIn('---', result)
        self.assertIn('title: My Post', result)
        self.assertIn('This is my post content.', result)

    def test_preview_has_newlines(self):
        """Test that preview has proper newline structure."""
        frontmatter = {'title': 'Test'}
        body = 'Content'
        result = preview_hugo_post(frontmatter, body)
        # Should have two newlines between frontmatter and body
        self.assertIn('---\n\nContent', result)

    def test_preview_ends_with_newline(self):
        """Test that preview ends with a newline."""
        frontmatter = {'title': 'Test'}
        body = 'Content'
        result = preview_hugo_post(frontmatter, body)
        self.assertTrue(result.endswith('\n'))

    def test_preview_empty_body(self):
        """Test preview with empty body."""
        frontmatter = {'title': 'Test'}
        result = preview_hugo_post(frontmatter, '')
        self.assertIn('---', result)
        self.assertIn('title: Test', result)

    def test_preview_none_body(self):
        """Test preview with None body is handled."""
        frontmatter = {'title': 'Test'}
        # Body defaults to empty string if falsy
        result = preview_hugo_post(frontmatter, None)
        self.assertIn('---', result)

    def test_preview_strips_leading_newlines_from_body(self):
        """Test that leading newlines are stripped from body."""
        frontmatter = {'title': 'Test'}
        body = '\n\n\nContent starts here'
        result = preview_hugo_post(frontmatter, body)
        # Should have exactly two newlines after --- before Content
        self.assertIn('---\n\nContent starts here', result)


class TestWriteHugoPost(unittest.TestCase):
    """Tests for the write_hugo_post function."""

    def setUp(self):
        """Create a temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_write_simple_post(self):
        """Test writing a simple Hugo post."""
        frontmatter = {
            'title': 'My Test Post',
            'date': '2024-01-15',
            'draft': False,
            'tags': ['test']
        }
        body = 'This is the body content.\n\nWith multiple paragraphs.'
        output_path = Path(self.temp_dir) / 'test-post.md'

        result = write_hugo_post(frontmatter, body, output_path)

        self.assertEqual(result, output_path)
        self.assertTrue(output_path.exists())

        content = output_path.read_text()
        self.assertIn('---', content)
        self.assertIn('title: My Test Post', content)
        self.assertIn('This is the body content.', content)

    def test_write_creates_directories(self):
        """Test that write_hugo_post creates parent directories."""
        frontmatter = {'title': 'Test'}
        body = 'Content'
        output_path = Path(self.temp_dir) / 'nested' / 'dirs' / 'post.md'

        result = write_hugo_post(frontmatter, body, output_path)

        self.assertTrue(output_path.exists())
        self.assertTrue(output_path.parent.exists())

    def test_write_adds_md_extension(self):
        """Test that .md extension is added if missing."""
        frontmatter = {'title': 'Test'}
        body = 'Content'
        output_path = Path(self.temp_dir) / 'test-post'

        result = write_hugo_post(frontmatter, body, output_path)

        self.assertTrue(str(result).endswith('.md'))
        self.assertTrue(result.exists())

    def test_write_preserves_md_extension(self):
        """Test that existing .md extension is preserved."""
        frontmatter = {'title': 'Test'}
        body = 'Content'
        output_path = Path(self.temp_dir) / 'test-post.md'

        result = write_hugo_post(frontmatter, body, output_path)

        self.assertEqual(result.name, 'test-post.md')

    def test_write_file_ends_with_newline(self):
        """Test that written file ends with newline."""
        frontmatter = {'title': 'Test'}
        body = 'Content'
        output_path = Path(self.temp_dir) / 'test.md'

        write_hugo_post(frontmatter, body, output_path)

        content = output_path.read_text()
        self.assertTrue(content.endswith('\n'))

    def test_write_with_create_dirs_false(self):
        """Test that OSError is raised when create_dirs=False and dir missing."""
        frontmatter = {'title': 'Test'}
        body = 'Content'
        output_path = Path(self.temp_dir) / 'nonexistent' / 'post.md'

        with self.assertRaises(OSError):
            write_hugo_post(frontmatter, body, output_path, create_dirs=False)

    def test_write_overwrites_existing_file(self):
        """Test that existing file is overwritten."""
        frontmatter1 = {'title': 'Original'}
        frontmatter2 = {'title': 'Updated'}
        body = 'Content'
        output_path = Path(self.temp_dir) / 'test.md'

        write_hugo_post(frontmatter1, body, output_path)
        write_hugo_post(frontmatter2, body, output_path)

        content = output_path.read_text()
        self.assertIn('title: Updated', content)
        self.assertNotIn('title: Original', content)

    def test_write_returns_path(self):
        """Test that write returns the output path."""
        frontmatter = {'title': 'Test'}
        body = 'Content'
        output_path = Path(self.temp_dir) / 'test.md'

        result = write_hugo_post(frontmatter, body, output_path)

        self.assertIsInstance(result, Path)
        self.assertEqual(result, output_path)

    def test_write_utf8_content(self):
        """Test writing UTF-8 content."""
        frontmatter = {'title': 'Café Résumé'}
        body = 'Unicode content: 日本語 العربية 中文'
        output_path = Path(self.temp_dir) / 'unicode.md'

        write_hugo_post(frontmatter, body, output_path)

        content = output_path.read_text(encoding='utf-8')
        self.assertIn('Café Résumé', content)
        self.assertIn('日本語', content)


class TestWriteHugoPostIntegration(unittest.TestCase):
    """Integration tests for complete Hugo post writing workflow."""

    def setUp(self):
        """Create a temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_blog_post_workflow(self):
        """Test writing a complete blog post like existing Hugo posts."""
        frontmatter = {
            'layout': 'post',
            'title': 'Clear Your Terminal in Style',
            'headerimg': '/img/post-bg-09.png',
            'date': '2020-03-04',
            'draft': False,
            'tags': ['linux', 'terminal', 'tips']
        }
        body = """If you're someone like me who habitually clears their terminal, sometimes you want a little excitement in your life.

## Percent Chance for command to run

This post revolves around the idea of giving a command a percent chance of running.

```bash
[ $[$RANDOM % 10] = 0 ] && do_this || do_that
```

This gives roughly a 1 in 10 chance of do_this running."""

        output_path = Path(self.temp_dir) / '2020-03-04-clear-your-terminal-in-style.md'

        write_hugo_post(frontmatter, body, output_path)

        content = output_path.read_text()

        # Verify structure
        self.assertTrue(content.startswith('---\n'))
        self.assertIn('\n---\n\n', content)

        # Verify frontmatter fields
        self.assertIn('layout: post', content)
        self.assertIn('title: Clear Your Terminal in Style', content)
        # headerimg has a path, verify the key and value separately
        self.assertIn('headerimg:', content)
        self.assertIn('/img/post-bg-09.png', content)
        self.assertIn('date: 2020-03-04', content)
        self.assertIn('draft: false', content)
        self.assertIn('tags: [linux, terminal, tips]', content)

        # Verify body content
        self.assertIn('## Percent Chance for command to run', content)
        self.assertIn('```bash', content)

    def test_post_with_special_title(self):
        """Test writing a post with special characters in title."""
        frontmatter = {
            'title': "Let's Learn About YARA: Part 1",
            'date': '2024-01-15',
            'draft': False,
            'tags': ['security', 'malware']
        }
        body = 'Content about YARA rules.'
        output_path = Path(self.temp_dir) / 'yara-post.md'

        write_hugo_post(frontmatter, body, output_path)

        content = output_path.read_text()
        # Title should be quoted due to special characters
        self.assertIn('title: "Let\'s Learn About YARA: Part 1"', content)


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and error handling."""

    def setUp(self):
        """Create a temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_empty_frontmatter_and_body(self):
        """Test writing with empty frontmatter and body."""
        output_path = Path(self.temp_dir) / 'empty.md'

        write_hugo_post({}, '', output_path)

        content = output_path.read_text()
        self.assertEqual(content, '---\n---\n\n')

    def test_frontmatter_with_nested_structures(self):
        """Test handling of nested structures (which should be serialized)."""
        frontmatter = {
            'title': 'Test',
            'aliases': ['/old-url/', '/another-old-url/']
        }
        body = 'Content'
        output_path = Path(self.temp_dir) / 'aliases.md'

        write_hugo_post(frontmatter, body, output_path)

        content = output_path.read_text()
        # Aliases contain slashes which are special YAML chars, so they get quoted
        self.assertIn('aliases:', content)
        self.assertIn('/old-url/', content)
        self.assertIn('/another-old-url/', content)

    def test_body_with_frontmatter_like_content(self):
        """Test body that contains --- which could confuse parsers."""
        frontmatter = {'title': 'Test'}
        body = 'Here is some code:\n\n---\nThis looks like frontmatter but is in body\n---\n'
        output_path = Path(self.temp_dir) / 'tricky.md'

        write_hugo_post(frontmatter, body, output_path)

        content = output_path.read_text()
        # The first --- and second --- should be frontmatter delimiters
        # The ones in body should be preserved as-is
        lines = content.split('\n')
        self.assertEqual(lines[0], '---')


class TestGetOutputPath(unittest.TestCase):
    """Tests for the get_output_path function."""

    def test_post_content_type(self):
        """Test that post content type routes to post directory."""
        path = get_output_path('my-post.md', 'post', Path('/hugo'))
        self.assertEqual(path, Path('/hugo/content/english/post/my-post.md'))

    def test_project_content_type(self):
        """Test that project content type routes to projects directory."""
        path = get_output_path('my-project.md', 'project', Path('/hugo'))
        self.assertEqual(path, Path('/hugo/content/english/projects/my-project.md'))

    def test_photography_content_type(self):
        """Test that photography content type routes to photography directory."""
        path = get_output_path('my-photos.md', 'photography', Path('/hugo'))
        self.assertEqual(path, Path('/hugo/content/english/photography/my-photos.md'))

    def test_adds_md_extension(self):
        """Test that .md extension is added if missing."""
        path = get_output_path('my-post', 'post', Path('/hugo'))
        self.assertEqual(path.suffix, '.md')
        self.assertEqual(path.name, 'my-post.md')

    def test_preserves_md_extension(self):
        """Test that existing .md extension is preserved."""
        path = get_output_path('my-post.md', 'post', Path('/hugo'))
        self.assertEqual(path.name, 'my-post.md')

    def test_invalid_content_type_raises(self):
        """Test that invalid content type raises ValueError."""
        with self.assertRaises(ValueError):
            get_output_path('my-post.md', 'invalid', Path('/hugo'))

    def test_default_hugo_root(self):
        """Test that hugo_root defaults to current directory."""
        path = get_output_path('test.md', 'post')
        self.assertIn('content/english/post/test.md', str(path))

    def test_relative_hugo_root(self):
        """Test with relative hugo root path."""
        path = get_output_path('test.md', 'post', Path('.'))
        self.assertEqual(str(path), 'content/english/post/test.md')


class TestWriteHugoPostRouted(unittest.TestCase):
    """Tests for the write_hugo_post_routed function."""

    def setUp(self):
        """Create a temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_routes_to_post_by_default(self):
        """Test that content routes to post by default when no tags."""
        frontmatter = {'title': 'My Post', 'date': '2024-01-15'}
        body = 'Content here.'

        result = write_hugo_post_routed(
            frontmatter, body, 'test-post.md',
            hugo_root=Path(self.temp_dir)
        )

        expected = Path(self.temp_dir) / 'content/english/post/test-post.md'
        self.assertEqual(result, expected)
        self.assertTrue(result.exists())

    def test_routes_to_project_from_tags(self):
        """Test that content with project tag routes to projects."""
        frontmatter = {'title': 'My Project', 'tags': ['woodworking', 'diy']}
        body = 'Project content.'

        result = write_hugo_post_routed(
            frontmatter, body, 'test-project.md',
            hugo_root=Path(self.temp_dir)
        )

        expected = Path(self.temp_dir) / 'content/english/projects/test-project.md'
        self.assertEqual(result, expected)
        self.assertTrue(result.exists())

    def test_routes_to_photography_from_tags(self):
        """Test that content with photography tag routes to photography."""
        frontmatter = {'title': 'My Photos', 'tags': ['travel', 'photography']}
        body = 'Photo gallery content.'

        result = write_hugo_post_routed(
            frontmatter, body, 'test-photos.md',
            hugo_root=Path(self.temp_dir)
        )

        expected = Path(self.temp_dir) / 'content/english/photography/test-photos.md'
        self.assertEqual(result, expected)
        self.assertTrue(result.exists())

    def test_explicit_content_type_overrides_tags(self):
        """Test that explicit content_type parameter overrides tag inference."""
        frontmatter = {'title': 'Mixed Content', 'tags': ['photography']}
        body = 'Content.'

        result = write_hugo_post_routed(
            frontmatter, body, 'test-override.md',
            hugo_root=Path(self.temp_dir),
            content_type='post'
        )

        expected = Path(self.temp_dir) / 'content/english/post/test-override.md'
        self.assertEqual(result, expected)

    def test_explicit_content_type_in_frontmatter(self):
        """Test that explicit content_type in frontmatter is respected."""
        frontmatter = {
            'title': 'Project Post',
            'content_type': 'project',
            'tags': ['random']
        }
        body = 'Content.'

        result = write_hugo_post_routed(
            frontmatter, body, 'test-explicit.md',
            hugo_root=Path(self.temp_dir)
        )

        expected = Path(self.temp_dir) / 'content/english/projects/test-explicit.md'
        self.assertEqual(result, expected)

    def test_creates_directories(self):
        """Test that write_hugo_post_routed creates necessary directories."""
        frontmatter = {'title': 'Test'}
        body = 'Content.'

        result = write_hugo_post_routed(
            frontmatter, body, 'deep-test.md',
            hugo_root=Path(self.temp_dir)
        )

        self.assertTrue(result.exists())
        self.assertTrue(result.parent.exists())

    def test_file_content_is_valid(self):
        """Test that the written file has valid Hugo format."""
        frontmatter = {'title': 'Valid Post', 'draft': False}
        body = 'This is the body.'

        result = write_hugo_post_routed(
            frontmatter, body, 'valid-test.md',
            hugo_root=Path(self.temp_dir)
        )

        content = result.read_text()
        self.assertTrue(content.startswith('---\n'))
        self.assertIn('title: Valid Post', content)
        self.assertIn('This is the body.', content)

    def test_adds_md_extension(self):
        """Test that .md extension is added if missing."""
        frontmatter = {'title': 'Test'}
        body = 'Content.'

        result = write_hugo_post_routed(
            frontmatter, body, 'no-extension',
            hugo_root=Path(self.temp_dir)
        )

        self.assertEqual(result.suffix, '.md')

    def test_invalid_explicit_content_type(self):
        """Test that invalid explicit content_type raises ValueError."""
        frontmatter = {'title': 'Test'}
        body = 'Content.'

        with self.assertRaises(ValueError):
            write_hugo_post_routed(
                frontmatter, body, 'test.md',
                hugo_root=Path(self.temp_dir),
                content_type='invalid'
            )


class TestContentTypeRoutingIntegration(unittest.TestCase):
    """Integration tests for content-type-based routing."""

    def setUp(self):
        """Create a temporary directory mimicking Hugo structure."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_project_workflow(self):
        """Test complete workflow for a project post."""
        frontmatter = {
            'title': 'Building a Wooden Table',
            'date': '2024-01-15',
            'draft': False,
            'tags': ['woodworking', 'diy', 'furniture'],
            'description': 'A guide to building a wooden table'
        }
        body = """## Introduction

This project covers building a wooden table from scratch.

## Materials

- Wood planks
- Screws
- Wood glue
"""

        result = write_hugo_post_routed(
            frontmatter, body, '2024-01-15-wooden-table.md',
            hugo_root=Path(self.temp_dir)
        )

        # Verify correct routing
        self.assertIn('content/english/projects', str(result))

        # Verify file exists and content is correct
        content = result.read_text()
        self.assertIn('title: Building a Wooden Table', content)
        self.assertIn('## Introduction', content)

    def test_full_photography_workflow(self):
        """Test complete workflow for a photography post."""
        frontmatter = {
            'title': 'Trip to Puerto Morelos',
            'date': '2017-05-20',
            'draft': False,
            'tags': ['travel', 'mexico', 'photography']
        }
        body = """A collection of photos from my trip to Puerto Morelos.

## The Beach

Beautiful turquoise waters.
"""

        result = write_hugo_post_routed(
            frontmatter, body, '2017-05-20-puerto-morelos.md',
            hugo_root=Path(self.temp_dir)
        )

        # Verify correct routing
        self.assertIn('content/english/photography', str(result))

    def test_full_blog_post_workflow(self):
        """Test complete workflow for a regular blog post."""
        frontmatter = {
            'title': 'Tips for Linux Terminal',
            'date': '2024-01-20',
            'draft': False,
            'tags': ['linux', 'terminal', 'tips']
        }
        body = """Here are some tips for using the Linux terminal effectively.

## Tip 1: Aliases

Use aliases to shorten common commands.
"""

        result = write_hugo_post_routed(
            frontmatter, body, '2024-01-20-linux-tips.md',
            hugo_root=Path(self.temp_dir)
        )

        # Verify correct routing (should be post since no project/photo tags)
        self.assertIn('content/english/post', str(result))


if __name__ == '__main__':
    unittest.main()
