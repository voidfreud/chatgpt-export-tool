"""Tests for filter_pipeline module."""

from chatgpt_export_tool.core.field_selector import FieldSelector
from chatgpt_export_tool.core.filter_pipeline import (
    FilterConfig,
    FilterPipeline,
)
from chatgpt_export_tool.core.metadata_selector import MetadataSelector


class TestFilterConfig:
    """Test FilterConfig dataclass."""

    def test_default_values(self):
        """Test default FilterConfig values."""
        config = FilterConfig()
        assert config.field_spec == "all"
        assert config.include_metadata is None
        assert config.exclude_metadata is None
        assert config.validate is True

    def test_custom_values(self):
        """Test custom FilterConfig values."""
        config = FilterConfig(
            field_spec="include title,author",
            include_metadata=["model_slug"],
            exclude_metadata=["plugin_ids"],
            validate=False,
        )
        assert config.field_spec == "include title,author"
        assert config.include_metadata == ["model_slug"]
        assert config.exclude_metadata == ["plugin_ids"]
        assert config.validate is False


class TestFilterPipeline:
    """Test FilterPipeline class."""

    def test_from_config_default(self):
        """Test creating pipeline with default config."""
        config = FilterConfig()
        pipeline = FilterPipeline.from_config(config)

        assert pipeline.field_selector is not None
        assert isinstance(pipeline.field_selector, FieldSelector)
        assert pipeline.metadata_selector is None

    def test_from_config_with_field_spec(self):
        """Test creating pipeline with field spec."""
        config = FilterConfig(field_spec="include title,author")
        pipeline = FilterPipeline.from_config(config)

        assert pipeline.field_selector is not None
        assert pipeline.applied_filters == ["fields=include title,author"]

    def test_from_config_with_metadata(self):
        """Test creating pipeline with metadata filtering."""
        config = FilterConfig(
            field_spec="all",
            include_metadata=["title", "model_slug"],
        )
        pipeline = FilterPipeline.from_config(config)

        assert pipeline.metadata_selector is not None
        assert isinstance(pipeline.metadata_selector, MetadataSelector)

    def test_from_config_with_exclude_metadata(self):
        """Test creating pipeline with metadata exclusion."""
        config = FilterConfig(
            field_spec="all",
            exclude_metadata=["plugin_ids"],
        )
        pipeline = FilterPipeline.from_config(config)

        assert pipeline.metadata_selector is not None

    def test_filter_single_conversation(self):
        """Test filtering a single conversation."""
        config = FilterConfig(field_spec="include title,create_time")
        pipeline = FilterPipeline.from_config(config)

        conversation = {
            "title": "Test Conversation",
            "create_time": 1234567890,
            "mapping": {"key": "value"},
            "custom_field": "keep this",
        }

        filtered = pipeline.filter(conversation)

        assert "title" in filtered
        assert "create_time" in filtered
        assert "mapping" not in filtered  # Not in include list
        assert "custom_field" not in filtered  # Not in include list

    def test_filter_conversation_exclude_mode(self):
        """Test filtering with exclude mode."""
        config = FilterConfig(field_spec="exclude mapping")
        pipeline = FilterPipeline.from_config(config)

        conversation = {
            "title": "Test",
            "mapping": {"key": "value"},
            "custom_field": "keep this",
        }

        filtered = pipeline.filter(conversation)

        assert "title" in filtered
        assert "mapping" not in filtered  # Explicitly excluded
        assert "custom_field" in filtered  # Not excluded

    def test_filter_many_conversations(self):
        """Test filtering multiple conversations."""
        config = FilterConfig(field_spec="include title")
        pipeline = FilterPipeline.from_config(config)

        conversations = [
            {"title": "Conv 1", "mapping": {}},
            {"title": "Conv 2", "mapping": {}},
        ]

        filtered = pipeline.filter_many(conversations)

        assert len(filtered) == 2
        assert all("title" in c for c in filtered)
        assert all("mapping" not in c for c in filtered)


class TestFilterPipelineIntegration:
    """Integration tests for FilterPipeline with real selectors."""

    def test_pipeline_with_groups_mode(self):
        """Test pipeline with groups mode."""
        config = FilterConfig(field_spec="groups conversation")
        pipeline = FilterPipeline.from_config(config)

        assert pipeline.field_selector is not None
        assert pipeline.applied_filters == ["fields=groups conversation"]

    def test_pipeline_with_validation(self):
        """Test that validation runs when enabled."""
        config = FilterConfig(
            field_spec="include title",
            validate=True,
        )
        pipeline = FilterPipeline.from_config(config)

        # Validation should have run
        assert pipeline.validation is not None

    def test_pipeline_validation_invalid_spec(self):
        """Test that invalid spec is caught by validation."""
        config = FilterConfig(
            field_spec="groups invalid_group_xyz",
            validate=True,
        )
        pipeline = FilterPipeline.from_config(config)

        # Validation should have run and found error
        assert pipeline.validation is not None
        assert pipeline.validation.is_valid is False
