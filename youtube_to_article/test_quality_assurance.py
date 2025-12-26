"""Tests for Quality Assurance Agent."""

import pytest
from agents.quality_assurance import QualityAssuranceAgent
from models.schemas import (
    Article,
    ArticleSection,
    ContentAnalysis,
    Quote,
    SectionOutline,
    SEOPackage,
    SocialPosts,
)


@pytest.fixture
def qa_agent():
    """Create a QA agent instance."""
    return QualityAssuranceAgent()


@pytest.fixture
def sample_article():
    """Create a sample article for testing."""
    return Article(
        headline="Understanding Artificial Intelligence in 2024",
        introduction="Artificial Intelligence has become a cornerstone of modern technology. This article explores the latest developments and applications of AI in various industries.",
        sections=[
            ArticleSection(
                heading="Current Applications of AI",
                content="AI is revolutionizing industries across the board. From healthcare to finance, machine learning algorithms are being deployed to improve efficiency and accuracy. Healthcare providers use AI for diagnostic imaging, drug discovery, and personalized medicine. Financial institutions leverage AI for fraud detection and algorithmic trading.",
                word_count=100
            ),
            ArticleSection(
                heading="Machine Learning Advancements",
                content="Recent breakthroughs in machine learning have pushed the boundaries of what's possible. Deep learning models now achieve human-level performance on many tasks. Transfer learning and fine-tuning techniques allow developers to build sophisticated applications with limited data. The emergence of transformer-based models has revolutionized natural language processing.",
                word_count=90
            ),
            ArticleSection(
                heading="Ethical Considerations",
                content="As AI becomes more prevalent, ethical concerns have come to the forefront. Issues of bias in AI models, data privacy, and algorithmic transparency are critical challenges. Organizations must ensure that their AI systems are fair, accountable, and transparent. Governments are implementing regulations to govern AI development and deployment.",
                word_count=85
            ),
            ArticleSection(
                heading="Future Prospects",
                content="The future of AI looks promising with continued research and development. Quantum computing may unlock new capabilities for AI systems. Artificial General Intelligence remains a long-term goal for researchers. We can expect to see more integration of AI in everyday applications and services.",
                word_count=75
            ),
        ],
        conclusion="Artificial Intelligence is undoubtedly the technology of our time. From improving efficiency to solving complex problems, AI continues to shape our world. As we move forward, addressing ethical considerations and ensuring responsible deployment will be crucial.",
        markdown="# Understanding Artificial Intelligence in 2024\n\nArtificial Intelligence has become a cornerstone of modern technology...",
        word_count=350
    )


@pytest.fixture
def sample_analysis():
    """Create a sample content analysis."""
    return ContentAnalysis(
        main_topic="Artificial Intelligence and its impact on modern industries",
        subtopics=[
            "Machine Learning Applications",
            "Deep Learning Models",
            "Ethical Considerations in AI",
            "Future of AI Technology"
        ],
        key_quotes=[
            Quote(
                text="AI is transforming how we work and live",
                timestamp=120.5,
                context="Speaker discussing AI impact"
            ),
            Quote(
                text="Ethics must be a priority in AI development",
                timestamp=450.3,
                context="Discussion on responsible AI"
            )
        ],
        data_points=["50% of enterprises use AI", "AI market expected to grow 38% annually"],
        suggested_sections=[
            SectionOutline(title="Applications", description="Current AI applications"),
            SectionOutline(title="Advancements", description="Recent breakthroughs"),
            SectionOutline(title="Ethics", description="Ethical considerations"),
            SectionOutline(title="Future", description="Future prospects")
        ],
        target_audience="Tech professionals and business leaders",
        tone="Informative and professional",
        estimated_reading_time=12
    )


@pytest.fixture
def sample_seo():
    """Create a sample SEO package."""
    return SEOPackage(
        meta_title="AI in 2024: Applications, Ethics, and Future Prospects",
        meta_description="Explore the latest developments in artificial intelligence, including applications, ethical considerations, and future prospects for 2024.",
        slug="ai-applications-ethics-future-2024",
        primary_keyword="artificial intelligence 2024",
        secondary_keywords=["machine learning", "AI ethics", "deep learning", "AI applications"],
        schema_markup={
            "headline": "AI in 2024: Applications, Ethics, and Future Prospects",
            "description": "Comprehensive guide to AI developments in 2024",
            "author": "AI Expert",
            "datePublished": "2024-01-15"
        },
        open_graph={
            "og:title": "AI in 2024: Applications, Ethics, and Future Prospects",
            "og:description": "Explore the latest developments in artificial intelligence",
            "og:type": "article",
            "og:image": "https://example.com/image.jpg"
        },
        twitter_card={
            "twitter:card": "summary_large_image",
            "twitter:title": "AI in 2024",
            "twitter:description": "Latest developments in artificial intelligence"
        },
        social_posts=SocialPosts(
            twitter="Discover the latest breakthroughs in AI and machine learning for 2024. From applications to ethics, explore what's shaping our future. #AI #MachineLearning",
            linkedin="An in-depth look at artificial intelligence in 2024: current applications, ethical considerations, and what the future holds for AI technology.",
            facebook="Learn about the latest developments in artificial intelligence and how it's transforming industries worldwide."
        ),
        internal_link_suggestions=["machine learning guide", "AI ethics framework", "deep learning tutorial"]
    )


class TestStructureValidation:
    """Test article structure validation."""

    def test_valid_structure(self, qa_agent, sample_article):
        """Test validation of a well-formed article."""
        check = qa_agent.check_article_structure(sample_article)
        assert check.has_headline
        assert check.has_introduction
        assert check.has_sections
        assert check.has_conclusion
        assert check.min_word_count_met
        assert check.sections_have_content
        assert check.proper_formatting

    def test_missing_headline(self, qa_agent):
        """Test detection of missing headline."""
        article = Article(
            headline="",
            introduction="Some intro",
            sections=[ArticleSection(heading="Section", content="Content", word_count=50)],
            conclusion="Conclusion",
            markdown="# Article",
            word_count=100
        )
        check = qa_agent.check_article_structure(article)
        assert not check.has_headline

    def test_low_word_count(self, qa_agent):
        """Test detection of low word count."""
        article = Article(
            headline="Title",
            introduction="Short",
            sections=[ArticleSection(heading="Section", content="Content", word_count=30)],
            conclusion="End",
            markdown="# Title",
            word_count=50
        )
        check = qa_agent.check_article_structure(article)
        assert not check.min_word_count_met


class TestReadabilityScoring:
    """Test readability scoring."""

    def test_readability_calculation(self, qa_agent, sample_article):
        """Test readability score calculation."""
        score = qa_agent._calculate_readability_score(sample_article.markdown)
        assert 0 <= score <= 100
        # Readability score should be a number
        assert isinstance(score, (int, float))

    def test_readability_with_complex_text(self, qa_agent):
        """Test readability with complex text."""
        complex_text = "The multifaceted phenomenological manifestations of post-heuristic computational methodologies engender substantive epistemological considerations."
        score = qa_agent._calculate_readability_score(complex_text)
        assert 0 <= score <= 100
        # Complex text should have lower readability
        assert score < 50

    def test_readability_with_simple_text(self, qa_agent):
        """Test readability with simple text."""
        simple_text = "AI is good. It helps people. It can do many things. Things are better now."
        score = qa_agent._calculate_readability_score(simple_text)
        assert 0 <= score <= 100


class TestContentQualityScoring:
    """Test content quality scoring."""

    def test_content_quality_scoring(self, qa_agent, sample_article, sample_analysis):
        """Test comprehensive content quality scoring."""
        score = qa_agent.score_content_quality(sample_article, sample_analysis)
        assert 0 <= score.readability_score <= 100
        assert 0 <= score.coherence_score <= 100
        assert 0 <= score.completeness_score <= 100
        assert 0 <= score.relevance_score <= 100
        assert 0 <= score.uniqueness_score <= 100
        assert 0 <= score.average_score <= 100

    def test_completeness_with_good_article(self, qa_agent, sample_article):
        """Test completeness scoring with well-structured article."""
        score = qa_agent._calculate_completeness_score(sample_article)
        # Well-structured article with good word count should score high
        assert score > 60

    def test_relevance_with_relevant_content(self, qa_agent, sample_article, sample_analysis):
        """Test relevance scoring with relevant content."""
        score = qa_agent._calculate_relevance_score(sample_article, sample_analysis)
        # Relevance score should be between 0-100
        assert 0 <= score <= 100


class TestSEOQualityScoring:
    """Test SEO quality scoring."""

    def test_seo_quality_scoring(self, qa_agent, sample_seo, sample_article):
        """Test comprehensive SEO quality scoring."""
        score = qa_agent.score_seo_quality(sample_seo, sample_article)
        assert 0 <= score.keyword_optimization <= 100
        assert 0 <= score.meta_tag_quality <= 100
        assert 0 <= score.slug_quality <= 100
        assert 0 <= score.schema_markup_quality <= 100
        assert 0 <= score.social_media_optimization <= 100
        assert 0 <= score.average_score <= 100

    def test_meta_tag_quality(self, qa_agent, sample_seo):
        """Test meta tag quality scoring."""
        score = qa_agent._score_meta_tags(sample_seo)
        # Sample has well-formatted meta tags
        assert score >= 80

    def test_slug_quality(self, qa_agent, sample_seo):
        """Test slug quality scoring."""
        score = qa_agent._score_slug(sample_seo)
        # Sample slug is well-formatted
        assert score > 50


class TestRecommendationGeneration:
    """Test recommendation generation."""

    def test_recommendations_for_low_quality(self, qa_agent):
        """Test that recommendations are generated for low-quality content."""
        # Create a low-quality article
        article = Article(
            headline="Title",
            introduction="Short intro",
            sections=[ArticleSection(heading="A", content="Short content", word_count=30)],
            conclusion="Conclusion",
            markdown="# Title",
            word_count=80
        )
        analysis = ContentAnalysis(
            main_topic="Test topic",
            subtopics=["Sub1", "Sub2"],
            key_quotes=[],
            data_points=[],
            suggested_sections=[SectionOutline(title="A", description="A")],
            target_audience="All",
            tone="Neutral",
            estimated_reading_time=5
        )
        seo = SEOPackage(
            meta_title="T",
            meta_description="D",
            slug="slug",
            primary_keyword="test",
            secondary_keywords=[],
            schema_markup={},
            open_graph={},
            twitter_card={},
            social_posts=SocialPosts(twitter="", linkedin=""),
            internal_link_suggestions=[]
        )

        structure = qa_agent.check_article_structure(article)
        content = qa_agent.score_content_quality(article, analysis)
        seo_score = qa_agent.score_seo_quality(seo, article)

        recommendations = qa_agent.generate_recommendations(structure, content, seo_score, article)

        # Low-quality article should generate recommendations
        assert len(recommendations) > 0

    def test_no_recommendations_for_high_quality(self, qa_agent, sample_article, sample_analysis, sample_seo):
        """Test that high-quality content generates few recommendations."""
        structure = qa_agent.check_article_structure(sample_article)
        content = qa_agent.score_content_quality(sample_article, sample_analysis)
        seo_score = qa_agent.score_seo_quality(sample_seo, sample_article)

        recommendations = qa_agent.generate_recommendations(structure, content, seo_score, sample_article)

        # High-quality article should generate few or no critical recommendations
        critical = [r for r in recommendations if r.severity == "critical"]
        assert len(critical) == 0


class TestQualityAssessment:
    """Test overall quality assessment."""

    def test_quality_assessment(self, qa_agent, sample_article, sample_analysis, sample_seo):
        """Test comprehensive quality assessment."""
        assessment = qa_agent.assess_quality(sample_article, sample_analysis, sample_seo)

        assert 0 <= assessment.overall_score <= 100
        assert assessment.quality_rating in ["excellent", "good", "fair", "poor"]
        assert isinstance(assessment.recommendations, list)
        assert assessment.content_quality is not None
        assert assessment.seo_quality is not None
        assert assessment.structure_check is not None

    def test_quality_rating_excellent(self, qa_agent, sample_article, sample_analysis, sample_seo):
        """Test quality rating determination."""
        assessment = qa_agent.assess_quality(sample_article, sample_analysis, sample_seo)

        # Sample should get a valid quality rating
        assert assessment.quality_rating in ["excellent", "good", "fair", "poor"]
        # Score should match rating
        if assessment.overall_score >= 85:
            assert assessment.quality_rating == "excellent"
        elif assessment.overall_score >= 70:
            assert assessment.quality_rating == "good"

    def test_quality_rating_categories(self, qa_agent, sample_article, sample_analysis, sample_seo):
        """Test that quality rating falls into correct categories."""
        assessment = qa_agent.assess_quality(sample_article, sample_analysis, sample_seo)

        if assessment.overall_score >= 85:
            assert assessment.quality_rating == "excellent"
        elif assessment.overall_score >= 70:
            assert assessment.quality_rating == "good"
        elif assessment.overall_score >= 50:
            assert assessment.quality_rating == "fair"
        else:
            assert assessment.quality_rating == "poor"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
