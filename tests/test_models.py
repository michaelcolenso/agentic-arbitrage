"""
Tests for core data models.
"""
import pytest
from datetime import datetime

from core.models import (
    Opportunity, Site, PainPoint, DataSource, KeywordOpportunity,
    FragmentationScore, MonetizationPotential,
    OpportunityStatus, SiteStatus
)


class TestOpportunity:
    """Test suite for Opportunity model."""
    
    def test_opportunity_creation(self, sample_opportunity):
        """Test creating an opportunity."""
        assert sample_opportunity.niche == "ev_charger_rebates"
        assert sample_opportunity.status == OpportunityStatus.DISCOVERED
        assert sample_opportunity.pain_velocity == 7.5
        assert sample_opportunity.competition_gap == 0.3
    
    def test_opportunity_id_generation(self, sample_opportunity):
        """Test that opportunities get unique IDs."""
        assert sample_opportunity.id is not None
        assert len(sample_opportunity.id) > 0
    
    def test_validation_score_calculation(self, validated_opportunity):
        """Test validation score calculation."""
        score = validated_opportunity.calculate_validation_score()
        
        # Score should be average of automation and monetization
        expected = (7.5 + 7.0) / 2  # automation_potential + monetization.score
        assert score == pytest.approx(expected, rel=0.1)
    
    def test_validation_score_without_fragmentation(self, sample_opportunity):
        """Test validation score without fragmentation data."""
        score = sample_opportunity.calculate_validation_score()
        assert score == 0.0


class TestSite:
    """Test suite for Site model."""
    
    def test_site_creation(self, sample_site):
        """Test creating a site."""
        assert sample_site.name == "EV Charger Rebates"
        assert sample_site.status == SiteStatus.DEPLOYED
        assert sample_site.page_count == 200
    
    def test_site_id_generation(self, sample_site):
        """Test that sites get unique IDs."""
        assert sample_site.id is not None
        assert len(sample_site.id) > 0
    
    def test_get_latest_metrics(self, sample_site):
        """Test getting latest metrics."""
        # Initially no metrics
        assert sample_site.get_latest_metrics() is None
    
    def test_avg_daily_traffic_no_metrics(self, sample_site):
        """Test average daily traffic with no metrics."""
        assert sample_site.get_avg_daily_traffic() == 0.0


class TestPainPoint:
    """Test suite for PainPoint model."""
    
    def test_pain_point_creation(self, sample_pain_point):
        """Test creating a pain point."""
        assert sample_pain_point.source == "reddit:r/test"
        assert "ev charger" in sample_pain_point.text.lower()
        assert sample_pain_point.sentiment_score < 0  # Negative sentiment
        assert sample_pain_point.engagement == 245


class TestDataSource:
    """Test suite for DataSource model."""
    
    def test_data_source_creation(self, sample_data_source):
        """Test creating a data source."""
        assert sample_data_source.name == "EV Charging Station Rebates Database"
        assert sample_data_source.type == "api"
        assert sample_data_source.quality_score == 8.5
    
    def test_data_source_schema(self, sample_data_source):
        """Test data source schema."""
        assert "fields" in sample_data_source.schema
        assert "state" in sample_data_source.schema["fields"]


class TestKeywordOpportunity:
    """Test suite for KeywordOpportunity model."""
    
    def test_keyword_creation(self, sample_keywords):
        """Test creating keyword opportunities."""
        kw = sample_keywords[0]
        assert kw.keyword == "ev charger rebates"
        assert kw.monthly_volume == 1000
        assert kw.difficulty == 45
        assert kw.cpc == 2.5
    
    def test_keyword_intent(self, sample_keywords):
        """Test keyword intent classification."""
        assert sample_keywords[0].intent == "commercial"
        assert sample_keywords[1].intent == "transactional"


class TestFragmentationScore:
    """Test suite for FragmentationScore model."""
    
    def test_fragmentation_creation(self, sample_fragmentation):
        """Test creating fragmentation score."""
        assert sample_fragmentation.score == 0.3
        assert sample_fragmentation.data_points_found == 150
        assert sample_fragmentation.automation_potential == 7.5
    
    def test_low_fragmentation_good(self):
        """Test that low fragmentation score is good."""
        # Lower score = more fragmented = better opportunity
        low = FragmentationScore(0.1, 100, 3, 0.7, 8.0)
        high = FragmentationScore(0.9, 100, 3, 0.7, 8.0)
        
        assert low.score < high.score


class TestMonetizationPotential:
    """Test suite for MonetizationPotential model."""
    
    def test_monetization_creation(self, sample_monetization):
        """Test creating monetization potential."""
        assert sample_monetization.score == 7.0
        assert len(sample_monetization.affiliate_programs) == 2
        assert sample_monetization.estimated_monthly_revenue == 150.0
    
    def test_revenue_streams(self, sample_monetization):
        """Test revenue stream calculations."""
        assert sample_monetization.lead_gen_potential > 0
        assert sample_monetization.ad_potential > 0
