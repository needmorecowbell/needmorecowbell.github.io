#!/usr/bin/env python3
"""
End-to-end integration tests for the Obsidian to Hugo publishing pipeline.

These tests verify that the complete conversion workflow produces correct Hugo output,
covering the full pipeline from parsing Obsidian notes to generating Hugo-compatible
markdown files.
"""

import sys
import tempfile
import shutil
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from obsidian_parser import parse_obsidian_note, parse_frontmatter, has_publish_flag
from frontmatter_transformer import transform_to_hugo, generate_slug
from syntax_converter import convert_wikilinks, convert_embedded_images, convert_embedded_media
from content_router import determine_content_type, get_hugo_section_path
from hugo_writer import (
    format_frontmatter,
    write_hugo_post,
    write_hugo_post_routed,
    preview_hugo_post,
    get_output_path,
)

# Import fixtures helpers
from tests.fixtures import get_fixture_path, read_fixture


class TestFullPipelineBasicPost(unittest.TestCase):
    """End-to-end tests for converting a basic publishable post."""

    def setUp(self):
        """Create a temporary directory for Hugo output."""
        self.temp_dir = tempfile.mkdtemp()
        self.hugo_root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_basic_post_full_pipeline(self):
        """Test the complete pipeline for a basic blog post."""
        # Step 1: Parse the Obsidian note
        fixture_path = get_fixture_path('basic_publishable_post.md')
        frontmatter, body = parse_obsidian_note(fixture_path)

        # Verify parsing
        self.assertEqual(frontmatter['title'], 'My First Blog Post')
        self.assertIs(frontmatter['publish'], True)
        self.assertTrue(has_publish_flag(frontmatter))

        # Step 2: Transform frontmatter to Hugo format
        hugo_frontmatter = transform_to_hugo(frontmatter, body)

        # Verify transformation (publish field should be removed)
        self.assertEqual(hugo_frontmatter['title'], 'My First Blog Post')
        self.assertNotIn('publish', hugo_frontmatter)
        self.assertEqual(hugo_frontmatter['draft'], False)
        self.assertEqual(hugo_frontmatter['tags'], ['python', 'testing', 'automation'])

        # Step 3: Convert body syntax
        converted_body = convert_wikilinks(body)
        converted_body = convert_embedded_images(converted_body)
        converted_body = convert_embedded_media(converted_body)

        # Body should remain unchanged (no wikilinks/embeds in basic post)
        self.assertIn('# My First Blog Post', converted_body)
        self.assertIn('def hello_world():', converted_body)

        # Step 4: Determine content type and output path
        content_type = determine_content_type(hugo_frontmatter)
        self.assertEqual(content_type, 'post')  # Default for tutorials/programming

        output_path = get_output_path(
            '2024-01-15-my-first-blog-post.md',
            content_type,
            self.hugo_root
        )
        self.assertTrue(str(output_path).endswith('content/english/post/2024-01-15-my-first-blog-post.md'))

        # Step 5: Write the Hugo post
        result_path = write_hugo_post(
            hugo_frontmatter,
            converted_body,
            output_path
        )

        # Verify the file was written
        self.assertTrue(result_path.exists())
        content = result_path.read_text()

        # Verify frontmatter
        self.assertIn('---', content)
        self.assertIn('title: My First Blog Post', content)
        self.assertIn('draft: false', content)

        # Verify body
        self.assertIn('# My First Blog Post', content)
        self.assertIn('```python', content)
        self.assertIn('def hello_world():', content)

    def test_basic_post_slug_generation(self):
        """Test slug generation for filenames."""
        # Various title formats
        self.assertEqual(generate_slug('My First Blog Post'), 'my-first-blog-post')
        self.assertEqual(generate_slug('Hello World!'), 'hello-world')
        self.assertEqual(generate_slug('Post with "Quotes"'), 'post-with-quotes')

        # With date prefix
        self.assertEqual(
            generate_slug('My First Blog Post', '2024-01-15'),
            '2024-01-15-my-first-blog-post'
        )

    def test_preview_without_writing(self):
        """Test generating a preview without writing to disk."""
        fixture_path = get_fixture_path('basic_publishable_post.md')
        frontmatter, body = parse_obsidian_note(fixture_path)
        hugo_frontmatter = transform_to_hugo(frontmatter, body)

        preview = preview_hugo_post(hugo_frontmatter, body)

        # Should have proper structure
        self.assertTrue(preview.startswith('---'))
        self.assertIn('title: My First Blog Post', preview)
        self.assertIn('---\n\n', preview)  # Empty line after frontmatter
        self.assertIn('# My First Blog Post', preview)
        self.assertTrue(preview.endswith('\n'))


class TestFullPipelineWithWikilinks(unittest.TestCase):
    """End-to-end tests for converting posts with wikilinks."""

    def setUp(self):
        """Create a temporary directory for Hugo output."""
        self.temp_dir = tempfile.mkdtemp()
        self.hugo_root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_wikilink_conversion_pipeline(self):
        """Test converting a post with various wikilink formats."""
        fixture_path = get_fixture_path('post_with_wikilinks.md')
        frontmatter, body = parse_obsidian_note(fixture_path)

        # Transform and convert
        hugo_frontmatter = transform_to_hugo(frontmatter, body)
        converted_body = convert_wikilinks(body)
        converted_body = convert_embedded_images(converted_body)

        # Verify wikilink conversions
        # Simple: [[Other Post]] -> [Other Post](/post/other-post/)
        self.assertIn('[Other Post](/post/other-post/)', converted_body)
        self.assertIn('[Related Article](/post/related-article/)', converted_body)

        # Aliased: [[My Long Page Name|this page]] -> [this page](/post/my-long-page-name/)
        self.assertIn('[this page](/post/my-long-page-name/)', converted_body)
        self.assertIn('[docs](/post/technical-documentation/)', converted_body)

        # Multiple in one line
        self.assertIn('[Page One](/post/page-one/)', converted_body)
        self.assertIn('[Page Two](/post/page-two/)', converted_body)
        self.assertIn('[Page Three](/post/page-three/)', converted_body)

        # Links in lists
        self.assertIn('- First item: [Link One](/post/link-one/)', converted_body)

        # Links in blockquotes
        self.assertIn('> As mentioned in [Important Reference](/post/important-reference/)', converted_body)

        # Embedded images should NOT be converted to wikilinks
        # They should be converted to s3cdn format
        self.assertNotIn('[[photo.jpg]]', converted_body)
        self.assertIn('![photo]({{<s3cdn>}}/photo.jpg)', converted_body)

        # Write and verify output
        output_path = self.hugo_root / 'content/english/post/test-wikilinks.md'
        write_hugo_post(hugo_frontmatter, converted_body, output_path)

        self.assertTrue(output_path.exists())
        content = output_path.read_text()
        self.assertIn('[Other Post](/post/other-post/)', content)

    def test_wikilink_special_characters(self):
        """Test wikilinks with special characters are converted correctly."""
        fixture_path = get_fixture_path('post_with_wikilinks.md')
        frontmatter, body = parse_obsidian_note(fixture_path)
        converted_body = convert_wikilinks(body)

        # Links with special chars should be slugified
        self.assertIn("[What's New in 2024?](/post/whats-new-in-2024/)", converted_body)
        self.assertIn('[Q&A Session](/post/qa-session/)', converted_body)
        self.assertIn('[C++ Programming](/post/c-programming/)', converted_body)


class TestFullPipelineWithMedia(unittest.TestCase):
    """End-to-end tests for converting posts with embedded media."""

    def setUp(self):
        """Create a temporary directory for Hugo output."""
        self.temp_dir = tempfile.mkdtemp()
        self.hugo_root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_embedded_media_pipeline(self):
        """Test converting a post with various embedded media types."""
        fixture_path = get_fixture_path('post_with_embedded_media.md')
        frontmatter, body = parse_obsidian_note(fixture_path)

        # Transform and convert
        hugo_frontmatter = transform_to_hugo(frontmatter, body)
        converted_body = convert_wikilinks(body)
        converted_body = convert_embedded_images(converted_body)
        converted_body = convert_embedded_media(converted_body)

        # Verify image conversions
        self.assertIn('![sunset]({{<s3cdn>}}/photos/sunset.jpg)', converted_body)
        self.assertIn('![beach panorama]({{<s3cdn>}}/2024/05/vacation/beach-panorama.png)', converted_body)
        self.assertIn('![logo]({{<s3cdn>}}/graphics/logo.svg)', converted_body)
        self.assertIn('![loading]({{<s3cdn>}}/animations/loading.gif)', converted_body)
        self.assertIn('![hero image]({{<s3cdn>}}/optimized/hero-image.webp)', converted_body)

        # Verify video conversions
        self.assertIn('<video controls><source src="{{<s3cdn>}}/videos/demo.mp4" type="video/mp4"></video>', converted_body)
        self.assertIn('<video controls><source src="{{<s3cdn>}}/clips/example.webm" type="video/webm"></video>', converted_body)
        self.assertIn('<video controls><source src="{{<s3cdn>}}/recordings/presentation.mov" type="video/quicktime"></video>', converted_body)

        # Verify audio conversions
        self.assertIn('<audio controls><source src="{{<s3cdn>}}/audio/podcast-episode-42.mp3" type="audio/mpeg"></audio>', converted_body)
        self.assertIn('<audio controls><source src="{{<s3cdn>}}/music/ambient-track.wav" type="audio/wav"></audio>', converted_body)
        self.assertIn('<audio controls><source src="{{<s3cdn>}}/recordings/voice-note.m4a" type="audio/mp4"></audio>', converted_body)

        # Write and verify output
        output_path = self.hugo_root / 'content/english/post/multimedia-post.md'
        write_hugo_post(hugo_frontmatter, converted_body, output_path)

        self.assertTrue(output_path.exists())
        content = output_path.read_text()
        self.assertIn('{{<s3cdn>}}', content)
        self.assertIn('<video controls>', content)
        self.assertIn('<audio controls>', content)

    def test_media_with_s3cdn_url(self):
        """Test converting media with a direct S3CDN URL instead of shortcode."""
        fixture_path = get_fixture_path('post_with_embedded_media.md')
        frontmatter, body = parse_obsidian_note(fixture_path)

        s3cdn_url = 'https://s3cdn.example.com/assets'
        converted_body = convert_embedded_images(body, s3cdn_base_url=s3cdn_url)
        converted_body = convert_embedded_media(converted_body, s3cdn_base_url=s3cdn_url)

        # Should use the actual URL instead of shortcode
        self.assertIn('![sunset](https://s3cdn.example.com/assets/photos/sunset.jpg)', converted_body)
        self.assertIn('<video controls><source src="https://s3cdn.example.com/assets/videos/demo.mp4"', converted_body)
        self.assertIn('<audio controls><source src="https://s3cdn.example.com/assets/audio/podcast-episode-42.mp3"', converted_body)


class TestFullPipelineContentTypes(unittest.TestCase):
    """End-to-end tests for different content types (post, project, photography)."""

    def setUp(self):
        """Create a temporary directory for Hugo output."""
        self.temp_dir = tempfile.mkdtemp()
        self.hugo_root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_photography_content_type_pipeline(self):
        """Test converting a photography-type post to the correct section."""
        fixture_path = get_fixture_path('photography_content_type.md')
        frontmatter, body = parse_obsidian_note(fixture_path)

        # Verify content type is detected
        content_type = determine_content_type(frontmatter)
        self.assertEqual(content_type, 'photography')

        # Transform frontmatter
        hugo_frontmatter = transform_to_hugo(frontmatter, body, content_type=content_type)
        self.assertEqual(hugo_frontmatter['content_type'], 'photography')
        self.assertIn('location', hugo_frontmatter)
        self.assertEqual(hugo_frontmatter['location'], 'Santa Monica, CA')

        # Convert body
        converted_body = convert_wikilinks(body)
        converted_body = convert_embedded_images(converted_body)

        # Verify section path
        section_path = get_hugo_section_path(content_type)
        self.assertEqual(section_path, 'content/english/photography')

        # Write using routed function
        slug = generate_slug(hugo_frontmatter['title'], '2024-08-20')
        result_path = write_hugo_post_routed(
            hugo_frontmatter,
            converted_body,
            f'{slug}.md',
            hugo_root=self.hugo_root
        )

        # Verify file is in correct location
        self.assertIn('content/english/photography', str(result_path))
        self.assertTrue(result_path.exists())

        # Verify content
        content = result_path.read_text()
        self.assertIn('content_type: photography', content)
        # Location is quoted due to containing a comma
        self.assertIn('location:', content)
        self.assertIn('Santa Monica', content)

    def test_project_content_type_pipeline(self):
        """Test converting a project-type post to the correct section."""
        fixture_path = get_fixture_path('project_content_type.md')
        frontmatter, body = parse_obsidian_note(fixture_path)

        # Verify content type is detected
        content_type = determine_content_type(frontmatter)
        self.assertEqual(content_type, 'project')

        # Transform frontmatter
        hugo_frontmatter = transform_to_hugo(frontmatter, body, content_type=content_type)
        self.assertEqual(hugo_frontmatter['content_type'], 'project')

        # Convert body
        converted_body = convert_wikilinks(body)
        converted_body = convert_embedded_images(converted_body)
        converted_body = convert_embedded_media(converted_body)

        # Verify section path
        section_path = get_hugo_section_path(content_type)
        self.assertEqual(section_path, 'content/english/projects')

        # Verify video embed in project
        self.assertIn('<video controls><source src="{{<s3cdn>}}/projects/home-dashboard/demo.mp4"', converted_body)

        # Write using routed function
        slug = generate_slug(hugo_frontmatter['title'], '2024-09-10')
        result_path = write_hugo_post_routed(
            hugo_frontmatter,
            converted_body,
            f'{slug}.md',
            hugo_root=self.hugo_root
        )

        # Verify file is in correct location
        self.assertIn('content/english/projects', str(result_path))
        self.assertTrue(result_path.exists())

    def test_content_type_inferred_from_tags(self):
        """Test that content type is correctly inferred from tags when not explicit."""
        # Test with woodworking tag (should infer project)
        frontmatter = {
            'title': 'My Woodworking Project',
            'tags': ['woodworking', 'diy', 'furniture'],
            'date': '2024-01-01'
        }
        content_type = determine_content_type(frontmatter)
        self.assertEqual(content_type, 'project')

        # Test with photography tag (should infer photography)
        frontmatter = {
            'title': 'Beach Photos',
            'tags': ['photography', 'landscape'],
            'date': '2024-01-01'
        }
        content_type = determine_content_type(frontmatter)
        self.assertEqual(content_type, 'photography')

        # Test with programming tags (should default to post)
        frontmatter = {
            'title': 'Python Tutorial',
            'tags': ['python', 'programming'],
            'date': '2024-01-01'
        }
        content_type = determine_content_type(frontmatter)
        self.assertEqual(content_type, 'post')


class TestFullPipelineEdgeCases(unittest.TestCase):
    """End-to-end tests for edge cases and special scenarios."""

    def setUp(self):
        """Create a temporary directory for Hugo output."""
        self.temp_dir = tempfile.mkdtemp()
        self.hugo_root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_unicode_content_pipeline(self):
        """Test handling of Unicode content through the pipeline."""
        fixture_path = get_fixture_path('unicode_content.md')
        frontmatter, body = parse_obsidian_note(fixture_path)

        # Transform and convert
        hugo_frontmatter = transform_to_hugo(frontmatter, body)
        converted_body = convert_wikilinks(body)

        # Write
        output_path = self.hugo_root / 'content/english/post/unicode-test.md'
        write_hugo_post(hugo_frontmatter, converted_body, output_path)

        # Read back and verify Unicode preserved
        content = output_path.read_text(encoding='utf-8')
        # Verify key sections from the unicode fixture are present
        self.assertIn('Unicode Test Post', content)
        self.assertIn('Japanese', content)
        self.assertIn('Accented Characters', content)
        self.assertIn('Emoji', content)
        self.assertIn('Mathematical Symbols', content)

    def test_empty_frontmatter_pipeline(self):
        """Test handling posts with empty frontmatter."""
        fixture_path = get_fixture_path('empty_frontmatter.md')
        frontmatter, body = parse_obsidian_note(fixture_path)

        # Frontmatter should be empty dict
        self.assertEqual(frontmatter, {})

        # Transform should still work with defaults
        hugo_frontmatter = transform_to_hugo(frontmatter, body)

        # Should have required fields with defaults
        self.assertIn('title', hugo_frontmatter)
        self.assertIn('date', hugo_frontmatter)
        self.assertEqual(hugo_frontmatter['draft'], False)
        self.assertEqual(hugo_frontmatter['tags'], [])

    def test_title_from_h1_heading(self):
        """Test extracting title from H1 when not in frontmatter."""
        fixture_path = get_fixture_path('title_from_h1.md')
        frontmatter, body = parse_obsidian_note(fixture_path)

        # Transform with body to extract title
        hugo_frontmatter = transform_to_hugo(frontmatter, body)

        # Title should be extracted from body H1
        self.assertEqual(hugo_frontmatter['title'], 'This Title Comes From the H1 Heading')

    def test_comma_separated_tags(self):
        """Test handling comma-separated tags string."""
        fixture_path = get_fixture_path('comma_separated_tags.md')
        frontmatter, body = parse_obsidian_note(fixture_path)

        hugo_frontmatter = transform_to_hugo(frontmatter, body)

        # Tags should be normalized to list
        self.assertIsInstance(hugo_frontmatter['tags'], list)
        self.assertIn('python', hugo_frontmatter['tags'])
        self.assertIn('testing', hugo_frontmatter['tags'])

    def test_draft_post_not_published(self):
        """Test that draft posts have draft: true in Hugo frontmatter."""
        content = """---
title: Draft Post
publish: true
draft: true
tags:
  - test
---

This is a draft.
"""
        frontmatter, body = parse_frontmatter(content)
        hugo_frontmatter = transform_to_hugo(frontmatter, body)

        # Should preserve draft status
        self.assertEqual(hugo_frontmatter['draft'], True)
        # But publish flag should be removed
        self.assertNotIn('publish', hugo_frontmatter)

    def test_no_body_content(self):
        """Test handling posts with only frontmatter."""
        fixture_path = get_fixture_path('no_body_content.md')
        frontmatter, body = parse_obsidian_note(fixture_path)

        hugo_frontmatter = transform_to_hugo(frontmatter, body)
        converted_body = convert_wikilinks(body)

        # Write should work with empty/minimal body
        output_path = self.hugo_root / 'content/english/post/no-body.md'
        write_hugo_post(hugo_frontmatter, converted_body, output_path)

        self.assertTrue(output_path.exists())


class TestPipelineWithMediaUrlMap(unittest.TestCase):
    """Tests for conversion with media URL mapping (simulating uploaded media)."""

    def test_media_url_map_priority(self):
        """Test that media_url_map takes priority over s3cdn shortcode."""
        content = """---
title: Test
---

![[photos/sunset.jpg]]
![[videos/demo.mp4]]
"""
        frontmatter, body = parse_frontmatter(content)

        # Simulate uploaded media URLs
        media_url_map = {
            'photos/sunset.jpg': 'https://minio.example.com/bucket/photos/sunset.jpg',
        }

        converted = convert_embedded_images(body, media_url_map=media_url_map)
        converted = convert_embedded_media(converted, media_url_map=media_url_map)

        # Image should use the mapped URL
        self.assertIn('![sunset](https://minio.example.com/bucket/photos/sunset.jpg)', converted)

        # Video without mapping should use shortcode
        self.assertIn('{{<s3cdn>}}/videos/demo.mp4', converted)


class TestRoutedWriting(unittest.TestCase):
    """Tests for write_hugo_post_routed which combines routing and writing."""

    def setUp(self):
        """Create a temporary directory for Hugo output."""
        self.temp_dir = tempfile.mkdtemp()
        self.hugo_root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_routed_writing_creates_directories(self):
        """Test that routed writing creates necessary directories."""
        hugo_frontmatter = {
            'title': 'Test Post',
            'date': '2024-01-15',
            'draft': False,
            'tags': ['test'],
        }
        body = '# Test\n\nContent here.'

        # Directory should not exist yet
        expected_dir = self.hugo_root / 'content/english/post'
        self.assertFalse(expected_dir.exists())

        result_path = write_hugo_post_routed(
            hugo_frontmatter,
            body,
            'test-post.md',
            hugo_root=self.hugo_root
        )

        # Directory and file should now exist
        self.assertTrue(expected_dir.exists())
        self.assertTrue(result_path.exists())

    def test_routed_writing_explicit_content_type(self):
        """Test routed writing with explicit content type override."""
        hugo_frontmatter = {
            'title': 'My Project',
            'date': '2024-01-15',
            'draft': False,
            'tags': ['programming'],  # Would default to 'post'
        }
        body = '# Project\n\nProject content.'

        result_path = write_hugo_post_routed(
            hugo_frontmatter,
            body,
            'my-project.md',
            hugo_root=self.hugo_root,
            content_type='project'  # Explicit override
        )

        # Should be in projects directory
        self.assertIn('content/english/projects', str(result_path))


class TestCompleteWorkflow(unittest.TestCase):
    """Integration tests simulating the complete publishing workflow."""

    def setUp(self):
        """Create temporary directories for vault and Hugo site."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir) / 'vault'
        self.hugo_root = Path(self.temp_dir) / 'hugo'
        self.vault_path.mkdir()
        self.hugo_root.mkdir()

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir)

    def _create_vault_note(self, relative_path: str, content: str):
        """Helper to create a note in the vault."""
        file_path = self.vault_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        return file_path

    def test_complete_workflow_single_post(self):
        """Test complete workflow: find publishable note, convert, write to Hugo."""
        # Create a publishable note in the vault
        note_content = """---
title: Complete Workflow Test
date: 2024-03-15
publish: true
tags:
  - testing
  - workflow
author: Test Author
---

# Complete Workflow Test

This post tests the [[complete workflow]] from vault to Hugo.

Here's an image: ![[test/image.jpg]]

And a video: ![[demo.mp4]]
"""
        self._create_vault_note('Blog/workflow-test.md', note_content)

        # Step 1: Find publishable notes (simulating find_publishable_notes)
        from obsidian_parser import find_publishable_notes
        publishable = find_publishable_notes(self.vault_path)
        self.assertEqual(len(publishable), 1)

        note = publishable[0]
        frontmatter = note['frontmatter']
        body = note['body']

        # Step 2: Transform frontmatter
        hugo_frontmatter = transform_to_hugo(frontmatter, body)
        self.assertNotIn('publish', hugo_frontmatter)
        self.assertEqual(hugo_frontmatter['author'], 'Test Author')

        # Step 3: Convert syntax
        converted_body = convert_wikilinks(body)
        converted_body = convert_embedded_images(converted_body)
        converted_body = convert_embedded_media(converted_body)

        # Verify conversions
        self.assertIn('[complete workflow](/post/complete-workflow/)', converted_body)
        self.assertIn('{{<s3cdn>}}/test/image.jpg', converted_body)
        self.assertIn('<video controls>', converted_body)

        # Step 4: Determine routing
        content_type = determine_content_type(hugo_frontmatter)
        self.assertEqual(content_type, 'post')

        # Step 5: Generate filename
        slug = generate_slug(hugo_frontmatter['title'], '2024-03-15')
        filename = f'{slug}.md'
        self.assertEqual(filename, '2024-03-15-complete-workflow-test.md')

        # Step 6: Write to Hugo
        result_path = write_hugo_post_routed(
            hugo_frontmatter,
            converted_body,
            filename,
            hugo_root=self.hugo_root
        )

        # Verify final output
        self.assertTrue(result_path.exists())
        final_content = result_path.read_text()

        # Verify all transformations in final output
        self.assertIn('title: Complete Workflow Test', final_content)
        self.assertIn('author: Test Author', final_content)
        self.assertNotIn('publish:', final_content)
        self.assertIn('[complete workflow](/post/complete-workflow/)', final_content)
        self.assertIn('{{<s3cdn>}}', final_content)

    def test_workflow_multiple_content_types(self):
        """Test workflow with multiple content types going to different sections."""
        # Create notes with different content types
        post_content = """---
title: Regular Post
date: 2024-01-01
publish: true
tags: [programming]
---

A regular blog post.
"""
        project_content = """---
title: DIY Project
date: 2024-01-02
publish: true
content_type: project
tags: [woodworking]
---

A project post.
"""
        photo_content = """---
title: Beach Photos
date: 2024-01-03
publish: true
content_type: photography
tags: [travel]
---

Some photos.
"""
        self._create_vault_note('Blog/post.md', post_content)
        self._create_vault_note('Projects/project.md', project_content)
        self._create_vault_note('Photos/beach.md', photo_content)

        # Process all publishable notes
        from obsidian_parser import find_publishable_notes
        publishable = find_publishable_notes(self.vault_path)
        self.assertEqual(len(publishable), 3)

        results = {}
        for note in publishable:
            frontmatter = note['frontmatter']
            body = note['body']
            hugo_fm = transform_to_hugo(frontmatter, body)
            content_type = determine_content_type(hugo_fm)
            converted = convert_wikilinks(body)

            slug = generate_slug(hugo_fm['title'], hugo_fm['date'])
            path = write_hugo_post_routed(
                hugo_fm,
                converted,
                f'{slug}.md',
                hugo_root=self.hugo_root
            )
            results[content_type] = path

        # Verify each went to correct section
        self.assertIn('content/english/post', str(results['post']))
        self.assertIn('content/english/projects', str(results['project']))
        self.assertIn('content/english/photography', str(results['photography']))

        # Verify all files exist
        for path in results.values():
            self.assertTrue(path.exists())


class TestFormatFrontmatter(unittest.TestCase):
    """Tests for Hugo frontmatter formatting."""

    def test_format_frontmatter_field_order(self):
        """Test that frontmatter fields are in expected order."""
        frontmatter = {
            'toc': True,
            'title': 'Test',
            'tags': ['a', 'b'],
            'date': '2024-01-15',
            'draft': False,
            'custom_field': 'value',
        }

        formatted = format_frontmatter(frontmatter)
        lines = formatted.split('\n')

        # Find positions
        title_pos = next(i for i, l in enumerate(lines) if l.startswith('title:'))
        date_pos = next(i for i, l in enumerate(lines) if l.startswith('date:'))
        draft_pos = next(i for i, l in enumerate(lines) if l.startswith('draft:'))
        tags_pos = next(i for i, l in enumerate(lines) if l.startswith('tags:'))
        toc_pos = next(i for i, l in enumerate(lines) if l.startswith('toc:'))

        # Preferred order: title < date < draft < tags < toc
        self.assertLess(title_pos, date_pos)
        self.assertLess(date_pos, draft_pos)
        self.assertLess(draft_pos, tags_pos)
        self.assertLess(tags_pos, toc_pos)

    def test_format_frontmatter_special_characters(self):
        """Test frontmatter formatting with special characters."""
        frontmatter = {
            'title': 'A title with: colons and "quotes"',
            'description': 'Contains # hash and * asterisk',
        }

        formatted = format_frontmatter(frontmatter)

        # Should be properly quoted
        self.assertIn('title: "A title with: colons and', formatted)
        self.assertIn('description: "Contains # hash', formatted)

    def test_format_frontmatter_lists(self):
        """Test frontmatter formatting with lists."""
        frontmatter = {
            'tags': ['python', 'testing', 'hugo'],
            'categories': [],
        }

        formatted = format_frontmatter(frontmatter)

        # Non-empty list
        self.assertIn('tags: [python, testing, hugo]', formatted)
        # Empty list
        self.assertIn('categories: []', formatted)


if __name__ == '__main__':
    unittest.main(verbosity=2)
