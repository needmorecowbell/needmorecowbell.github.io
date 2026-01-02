#!/usr/bin/env python3
"""
Tests for the content_router module.

Uses unittest (standard library) for compatibility.
"""

import unittest
from content_router import (
    determine_content_type,
    infer_content_type_from_tags,
    get_hugo_section_path,
    PROJECT_TAGS,
    PHOTOGRAPHY_TAGS,
    DEFAULT_CONTENT_TYPE,
    _normalize_tags_for_matching,
)


class TestDetermineContentType(unittest.TestCase):
    """Tests for the determine_content_type function."""

    def test_explicit_post_type(self):
        """Test explicit content_type='post' is used."""
        frontmatter = {
            'title': 'My Post',
            'content_type': 'post'
        }
        result = determine_content_type(frontmatter)
        self.assertEqual(result, 'post')

    def test_explicit_project_type(self):
        """Test explicit content_type='project' is used."""
        frontmatter = {
            'title': 'My Project',
            'content_type': 'project'
        }
        result = determine_content_type(frontmatter)
        self.assertEqual(result, 'project')

    def test_explicit_photography_type(self):
        """Test explicit content_type='photography' is used."""
        frontmatter = {
            'title': 'My Photos',
            'content_type': 'photography'
        }
        result = determine_content_type(frontmatter)
        self.assertEqual(result, 'photography')

    def test_explicit_type_overrides_tag_inference(self):
        """Test that explicit content_type takes precedence over tags."""
        frontmatter = {
            'title': 'Mixed Content',
            'content_type': 'post',
            'tags': ['project', 'woodworking']  # Would infer 'project'
        }
        result = determine_content_type(frontmatter)
        self.assertEqual(result, 'post')

    def test_explicit_type_case_insensitive(self):
        """Test that explicit content_type is case-insensitive."""
        frontmatter = {
            'title': 'Test',
            'content_type': 'PROJECT'
        }
        result = determine_content_type(frontmatter)
        self.assertEqual(result, 'project')

    def test_infer_project_from_tags(self):
        """Test inferring 'project' content type from tags."""
        frontmatter = {
            'title': 'My Build',
            'tags': ['woodworking', 'furniture']
        }
        result = determine_content_type(frontmatter)
        self.assertEqual(result, 'project')

    def test_infer_photography_from_tags(self):
        """Test inferring 'photography' content type from tags."""
        frontmatter = {
            'title': 'Summer Trip',
            'tags': ['travel', 'vacation']
        }
        result = determine_content_type(frontmatter)
        self.assertEqual(result, 'photography')

    def test_default_to_post(self):
        """Test defaulting to 'post' when no explicit type or matching tags."""
        frontmatter = {
            'title': 'Random Post',
            'tags': ['python', 'coding']
        }
        result = determine_content_type(frontmatter)
        self.assertEqual(result, 'post')

    def test_empty_frontmatter_defaults_to_post(self):
        """Test that empty frontmatter defaults to 'post'."""
        result = determine_content_type({})
        self.assertEqual(result, 'post')

    def test_no_tags_defaults_to_post(self):
        """Test that frontmatter without tags defaults to 'post'."""
        frontmatter = {
            'title': 'Test Post'
        }
        result = determine_content_type(frontmatter)
        self.assertEqual(result, 'post')

    def test_invalid_explicit_type_infers_from_tags(self):
        """Test that invalid content_type falls back to tag inference."""
        frontmatter = {
            'title': 'Test',
            'content_type': 'invalid_type',
            'tags': ['project']
        }
        result = determine_content_type(frontmatter)
        self.assertEqual(result, 'project')

    def test_invalid_explicit_type_no_tags_defaults_to_post(self):
        """Test that invalid content_type without matching tags defaults to post."""
        frontmatter = {
            'title': 'Test',
            'content_type': 'invalid_type',
            'tags': ['random', 'tags']
        }
        result = determine_content_type(frontmatter)
        self.assertEqual(result, 'post')

    def test_explicit_only_mode(self):
        """Test explicit_only mode ignores tag inference."""
        frontmatter = {
            'title': 'My Build',
            'tags': ['project', 'woodworking']  # Would normally infer 'project'
        }
        result = determine_content_type(frontmatter, explicit_only=True)
        self.assertEqual(result, 'post')

    def test_explicit_only_with_valid_content_type(self):
        """Test explicit_only mode still uses valid content_type."""
        frontmatter = {
            'title': 'My Project',
            'content_type': 'project',
            'tags': ['photography']  # Would conflict if inferred
        }
        result = determine_content_type(frontmatter, explicit_only=True)
        self.assertEqual(result, 'project')


class TestInferContentTypeFromTags(unittest.TestCase):
    """Tests for the infer_content_type_from_tags function."""

    def test_project_tag(self):
        """Test that 'project' tag infers project type."""
        result = infer_content_type_from_tags(['project'])
        self.assertEqual(result, 'project')

    def test_projects_tag(self):
        """Test that 'projects' tag infers project type."""
        result = infer_content_type_from_tags(['projects'])
        self.assertEqual(result, 'project')

    def test_woodworking_tag(self):
        """Test that 'woodworking' tag infers project type."""
        result = infer_content_type_from_tags(['woodworking'])
        self.assertEqual(result, 'project')

    def test_diy_tag(self):
        """Test that 'diy' tag infers project type."""
        result = infer_content_type_from_tags(['diy'])
        self.assertEqual(result, 'project')

    def test_maker_tag(self):
        """Test that 'maker' tag infers project type."""
        result = infer_content_type_from_tags(['maker'])
        self.assertEqual(result, 'project')

    def test_build_tag(self):
        """Test that 'build' tag infers project type."""
        result = infer_content_type_from_tags(['build'])
        self.assertEqual(result, 'project')

    def test_craft_tag(self):
        """Test that 'craft' tag infers project type."""
        result = infer_content_type_from_tags(['craft'])
        self.assertEqual(result, 'project')

    def test_crafts_tag(self):
        """Test that 'crafts' tag infers project type."""
        result = infer_content_type_from_tags(['crafts'])
        self.assertEqual(result, 'project')

    def test_photography_tag(self):
        """Test that 'photography' tag infers photography type."""
        result = infer_content_type_from_tags(['photography'])
        self.assertEqual(result, 'photography')

    def test_photos_tag(self):
        """Test that 'photos' tag infers photography type."""
        result = infer_content_type_from_tags(['photos'])
        self.assertEqual(result, 'photography')

    def test_photo_tag(self):
        """Test that 'photo' tag infers photography type."""
        result = infer_content_type_from_tags(['photo'])
        self.assertEqual(result, 'photography')

    def test_travel_tag(self):
        """Test that 'travel' tag infers photography type."""
        result = infer_content_type_from_tags(['travel'])
        self.assertEqual(result, 'photography')

    def test_trip_tag(self):
        """Test that 'trip' tag infers photography type."""
        result = infer_content_type_from_tags(['trip'])
        self.assertEqual(result, 'photography')

    def test_gallery_tag(self):
        """Test that 'gallery' tag infers photography type."""
        result = infer_content_type_from_tags(['gallery'])
        self.assertEqual(result, 'photography')

    def test_case_insensitive(self):
        """Test that tag matching is case-insensitive."""
        self.assertEqual(infer_content_type_from_tags(['PROJECT']), 'project')
        self.assertEqual(infer_content_type_from_tags(['Photography']), 'photography')
        self.assertEqual(infer_content_type_from_tags(['WOODWORKING']), 'project')

    def test_project_takes_precedence_over_photography(self):
        """Test that project tags take precedence over photography tags."""
        tags = ['photography', 'project']  # Both present
        result = infer_content_type_from_tags(tags)
        self.assertEqual(result, 'project')

    def test_multiple_project_tags(self):
        """Test inference with multiple project tags."""
        tags = ['woodworking', 'diy', 'maker']
        result = infer_content_type_from_tags(tags)
        self.assertEqual(result, 'project')

    def test_no_matching_tags_returns_none(self):
        """Test that non-matching tags return None."""
        tags = ['python', 'coding', 'tutorial']
        result = infer_content_type_from_tags(tags)
        self.assertIsNone(result)

    def test_none_tags_returns_none(self):
        """Test that None tags return None."""
        result = infer_content_type_from_tags(None)
        self.assertIsNone(result)

    def test_empty_list_returns_none(self):
        """Test that empty list returns None."""
        result = infer_content_type_from_tags([])
        self.assertIsNone(result)

    def test_comma_separated_string(self):
        """Test inference from comma-separated tag string."""
        result = infer_content_type_from_tags('woodworking, furniture')
        self.assertEqual(result, 'project')

    def test_single_tag_string(self):
        """Test inference from single tag string."""
        result = infer_content_type_from_tags('travel')
        self.assertEqual(result, 'photography')

    def test_tags_with_whitespace(self):
        """Test that tags with whitespace are properly trimmed."""
        tags = ['  project  ', '\twoodworking\n']
        result = infer_content_type_from_tags(tags)
        self.assertEqual(result, 'project')


class TestNormalizeTagsForMatching(unittest.TestCase):
    """Tests for the _normalize_tags_for_matching helper function."""

    def test_list_of_strings(self):
        """Test normalizing a list of strings."""
        result = _normalize_tags_for_matching(['Python', 'Hugo', 'Blog'])
        self.assertEqual(result, frozenset(['python', 'hugo', 'blog']))

    def test_list_with_whitespace(self):
        """Test that whitespace is trimmed."""
        result = _normalize_tags_for_matching(['  python  ', ' hugo '])
        self.assertEqual(result, frozenset(['python', 'hugo']))

    def test_list_with_empty_strings(self):
        """Test that empty strings are filtered out."""
        result = _normalize_tags_for_matching(['python', '', 'hugo', '   '])
        self.assertEqual(result, frozenset(['python', 'hugo']))

    def test_list_with_none_values(self):
        """Test that None values are filtered out."""
        result = _normalize_tags_for_matching(['python', None, 'hugo'])
        self.assertEqual(result, frozenset(['python', 'hugo']))

    def test_comma_separated_string(self):
        """Test normalizing comma-separated string."""
        result = _normalize_tags_for_matching('python, hugo, blog')
        self.assertEqual(result, frozenset(['python', 'hugo', 'blog']))

    def test_single_tag_string(self):
        """Test normalizing single tag string."""
        result = _normalize_tags_for_matching('python')
        self.assertEqual(result, frozenset(['python']))

    def test_empty_string(self):
        """Test that empty string returns empty frozenset."""
        result = _normalize_tags_for_matching('')
        self.assertEqual(result, frozenset())

    def test_whitespace_only_string(self):
        """Test that whitespace-only string returns empty frozenset."""
        result = _normalize_tags_for_matching('   ')
        self.assertEqual(result, frozenset())

    def test_none_returns_empty(self):
        """Test that None returns empty frozenset."""
        result = _normalize_tags_for_matching(None)
        self.assertEqual(result, frozenset())

    def test_integer_list(self):
        """Test normalizing list with integers."""
        result = _normalize_tags_for_matching([1, 2, 3])
        self.assertEqual(result, frozenset(['1', '2', '3']))


class TestGetHugoSectionPath(unittest.TestCase):
    """Tests for the get_hugo_section_path function."""

    def test_post_section_path(self):
        """Test getting section path for 'post'."""
        result = get_hugo_section_path('post')
        self.assertEqual(result, 'content/english/post')

    def test_project_section_path(self):
        """Test getting section path for 'project'."""
        result = get_hugo_section_path('project')
        self.assertEqual(result, 'content/english/projects')

    def test_photography_section_path(self):
        """Test getting section path for 'photography'."""
        result = get_hugo_section_path('photography')
        self.assertEqual(result, 'content/english/photography')

    def test_invalid_content_type_raises_error(self):
        """Test that invalid content type raises ValueError."""
        with self.assertRaises(ValueError) as context:
            get_hugo_section_path('invalid')
        self.assertIn('invalid', str(context.exception))
        self.assertIn('post', str(context.exception))
        self.assertIn('project', str(context.exception))
        self.assertIn('photography', str(context.exception))

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        with self.assertRaises(ValueError):
            get_hugo_section_path('')

    def test_none_raises_error(self):
        """Test that None raises appropriate error."""
        with self.assertRaises((ValueError, TypeError)):
            get_hugo_section_path(None)


class TestConstants(unittest.TestCase):
    """Tests for module constants."""

    def test_project_tags_is_frozenset(self):
        """Test that PROJECT_TAGS is a frozenset."""
        self.assertIsInstance(PROJECT_TAGS, frozenset)

    def test_photography_tags_is_frozenset(self):
        """Test that PHOTOGRAPHY_TAGS is a frozenset."""
        self.assertIsInstance(PHOTOGRAPHY_TAGS, frozenset)

    def test_default_content_type_is_post(self):
        """Test that DEFAULT_CONTENT_TYPE is 'post'."""
        self.assertEqual(DEFAULT_CONTENT_TYPE, 'post')

    def test_project_tags_contains_expected_values(self):
        """Test that PROJECT_TAGS contains expected values."""
        expected = {'project', 'projects', 'woodworking', 'diy', 'maker', 'build', 'craft', 'crafts'}
        self.assertEqual(PROJECT_TAGS, expected)

    def test_photography_tags_contains_expected_values(self):
        """Test that PHOTOGRAPHY_TAGS contains expected values."""
        expected = {'photography', 'photos', 'photo', 'travel', 'trip', 'gallery'}
        self.assertEqual(PHOTOGRAPHY_TAGS, expected)


class TestIntegration(unittest.TestCase):
    """Integration tests simulating real-world usage."""

    def test_typical_blog_post(self):
        """Test a typical blog post with no special routing."""
        frontmatter = {
            'title': 'How to Use Python',
            'date': '2024-01-15',
            'tags': ['python', 'tutorial', 'coding']
        }
        content_type = determine_content_type(frontmatter)
        section_path = get_hugo_section_path(content_type)
        self.assertEqual(content_type, 'post')
        self.assertEqual(section_path, 'content/english/post')

    def test_woodworking_project(self):
        """Test a woodworking project inferred from tags."""
        frontmatter = {
            'title': 'Building a Bookshelf',
            'date': '2024-02-20',
            'tags': ['woodworking', 'furniture', 'diy']
        }
        content_type = determine_content_type(frontmatter)
        section_path = get_hugo_section_path(content_type)
        self.assertEqual(content_type, 'project')
        self.assertEqual(section_path, 'content/english/projects')

    def test_travel_photography(self):
        """Test travel photography inferred from tags."""
        frontmatter = {
            'title': 'Nova Scotia 2023',
            'date': '2023-08-15',
            'tags': ['travel', 'vacation', 'nature']
        }
        content_type = determine_content_type(frontmatter)
        section_path = get_hugo_section_path(content_type)
        self.assertEqual(content_type, 'photography')
        self.assertEqual(section_path, 'content/english/photography')

    def test_explicit_photography_with_tech_tags(self):
        """Test explicit photography type even with tech tags."""
        frontmatter = {
            'title': 'Camera Tech Review',
            'date': '2024-03-01',
            'content_type': 'photography',
            'tags': ['review', 'tech', 'camera']
        }
        content_type = determine_content_type(frontmatter)
        self.assertEqual(content_type, 'photography')

    def test_maker_project(self):
        """Test a maker project inferred from tags."""
        frontmatter = {
            'title': 'Arduino LED Matrix',
            'date': '2024-04-10',
            'tags': ['maker', 'electronics', 'arduino']
        }
        content_type = determine_content_type(frontmatter)
        self.assertEqual(content_type, 'project')


if __name__ == '__main__':
    unittest.main()
