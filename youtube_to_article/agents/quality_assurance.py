"""Quality Assurance Agent - Validates and scores generated content."""

import logging
import re
from typing import List, Tuple
from models.schemas import (
    Article,
    SEOPackage,
    ContentAnalysis,
    ContentQualityScore,
    SEOQualityScore,
    ContentPolicyScore,
    StructureCheck,
    QualityAssessment,
    QualityRecommendation,
)

logger = logging.getLogger(__name__)


class QualityAssuranceAgent:
    """Comprehensive quality checking and scoring agent."""

    # Minimum quality thresholds
    MIN_WORD_COUNT = 200
    MIN_SECTION_WORD_COUNT = 50
    MIN_HEADLINE_LENGTH = 10
    MIN_INTRODUCTION_LENGTH = 100
    MIN_CONCLUSION_LENGTH = 100

    # Readability thresholds (Flesch Reading Ease)
    # 90-100: Very Easy, 80-89: Easy, 70-79: Fairly Easy, 60-69: Standard,
    # 50-59: Fairly Difficult, 30-49: Difficult, 0-29: Very Difficult
    READABILITY_TARGET = 60  # Aim for "Standard" difficulty

    def __init__(self):
        """Initialize the QA agent."""
        logger.info("Quality Assurance Agent initialized")

    # ========================================================================
    # Structure Validation
    # ========================================================================

    def check_article_structure(self, article: Article) -> StructureCheck:
        """Validate article structure."""
        checks = {
            "has_headline": len(article.headline.strip()) >= self.MIN_HEADLINE_LENGTH,
            "has_introduction": len(article.introduction.strip()) >= self.MIN_INTRODUCTION_LENGTH,
            "has_sections": len(article.sections) > 0,
            "has_conclusion": len(article.conclusion.strip()) >= self.MIN_CONCLUSION_LENGTH,
            "min_word_count_met": article.word_count >= self.MIN_WORD_COUNT,
            "sections_have_content": all(
                len(s.content.strip()) >= self.MIN_SECTION_WORD_COUNT for s in article.sections
            ),
            "proper_formatting": self._check_markdown_formatting(article.markdown),
        }

        passed = sum(1 for v in checks.values() if v)
        total = len(checks)

        return StructureCheck(
            has_headline=checks["has_headline"],
            has_introduction=checks["has_introduction"],
            has_sections=checks["has_sections"],
            has_conclusion=checks["has_conclusion"],
            min_word_count_met=checks["min_word_count_met"],
            sections_have_content=checks["sections_have_content"],
            proper_formatting=checks["proper_formatting"],
            all_checks_passed=all(checks.values()),
            passed_checks=passed,
            total_checks=total,
        )

    def _check_markdown_formatting(self, markdown: str) -> bool:
        """Check if markdown has proper formatting."""
        # Check for proper heading hierarchy
        has_headings = bool(re.search(r'^#+\s', markdown, re.MULTILINE))
        # Check for proper paragraph spacing
        has_paragraphs = bool(re.search(r'\n\n', markdown))
        # Check for proper list formatting
        has_lists = bool(re.search(r'^\s*[\*\-\+]\s', markdown, re.MULTILINE))

        # At least headings and paragraphs should be present
        return has_headings and has_paragraphs

    # ========================================================================
    # Content Quality Scoring
    # ========================================================================

    def score_content_quality(
        self, article: Article, analysis: ContentAnalysis
    ) -> ContentQualityScore:
        """Score content quality across multiple dimensions."""
        readability = self._calculate_readability_score(article.markdown)
        coherence = self._calculate_coherence_score(article)
        completeness = self._calculate_completeness_score(article)
        relevance = self._calculate_relevance_score(article, analysis)
        uniqueness = self._calculate_uniqueness_score(article)

        average = (readability + coherence + completeness + relevance + uniqueness) / 5

        return ContentQualityScore(
            readability_score=readability,
            coherence_score=coherence,
            completeness_score=completeness,
            relevance_score=relevance,
            uniqueness_score=uniqueness,
            average_score=average,
        )

    def _calculate_readability_score(self, text: str) -> float:
        """Calculate readability score using Flesch Reading Ease approximation."""
        # Remove markdown formatting for analysis
        clean_text = re.sub(r'[#*_\[\]\(\)~`]', '', text)
        sentences = re.split(r'[.!?]+', clean_text)
        words = clean_text.split()

        if not sentences or not words:
            return 50.0

        num_sentences = len([s for s in sentences if s.strip()])
        num_words = len(words)
        num_syllables = self._estimate_syllables(clean_text)

        if num_sentences == 0 or num_words == 0:
            return 50.0

        # Flesch Reading Ease formula
        try:
            score = (
                206.835
                - (1.015 * (num_words / num_sentences))
                - (84.6 * (num_syllables / num_words))
            )
            # Clamp to 0-100
            return max(0, min(100, score))
        except ZeroDivisionError:
            return 50.0

    def _estimate_syllables(self, text: str) -> int:
        """Estimate syllable count in text."""
        text = text.lower()
        syllable_count = 0
        vowels = 'aeiouy'
        previous_was_vowel = False

        for char in text:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Adjust for silent e
        if text.endswith('e'):
            syllable_count -= 1

        # Adjust for le
        if text.endswith('le'):
            syllable_count += 1

        return max(1, syllable_count)

    def _calculate_coherence_score(self, article: Article) -> float:
        """Score how well sections flow together."""
        if not article.sections:
            return 50.0

        # Check for proper transitions between sections
        transition_words = {
            'however', 'therefore', 'moreover', 'furthermore', 'additionally',
            'consequently', 'meanwhile', 'similarly', 'contrast', 'example',
            'specifically', 'likewise', 'otherwise', 'instead', 'yet', 'also'
        }

        full_text = (
            article.introduction + ' ' +
            ' '.join(s.content for s in article.sections) + ' ' +
            article.conclusion
        ).lower()

        # Count transition words
        transition_count = sum(1 for word in transition_words if word in full_text)

        # Check section count (reasonable number indicates good structure)
        section_count = len(article.sections)
        structure_score = min(100, (section_count * 15))

        # Combine metrics
        coherence = (transition_count * 5) + structure_score
        return min(100, coherence / 2)

    def _calculate_completeness_score(self, article: Article) -> float:
        """Score article completeness."""
        score = 0.0

        # Word count (target 300-1000 words for good completeness)
        if article.word_count >= 300:
            score += 30
        elif article.word_count >= 200:
            score += 20
        else:
            score += 10

        # Section count (target 4-6 sections)
        section_count = len(article.sections)
        if 4 <= section_count <= 6:
            score += 30
        elif section_count >= 3:
            score += 20
        else:
            score += 10

        # Introduction quality
        intro_length = len(article.introduction)
        if intro_length >= 200:
            score += 15
        elif intro_length >= 100:
            score += 10
        else:
            score += 5

        # Conclusion quality
        conclusion_length = len(article.conclusion)
        if conclusion_length >= 200:
            score += 15
        elif conclusion_length >= 100:
            score += 10
        else:
            score += 5

        # All sections have meaningful content
        if all(len(s.content) >= 100 for s in article.sections):
            score += 10

        return min(100, score)

    def _calculate_relevance_score(self, article: Article, analysis: ContentAnalysis) -> float:
        """Score how relevant content is to main topic."""
        main_topic = analysis.main_topic.lower()
        subtopics = [s.lower() for s in analysis.subtopics]
        article_text = (
            article.headline + ' ' +
            article.introduction + ' ' +
            ' '.join(s.content for s in article.sections) + ' ' +
            article.conclusion
        ).lower()

        score = 0.0

        # Check if main topic appears in article
        if main_topic in article_text:
            score += 50

        # Check for subtopics in article
        subtopic_matches = sum(1 for subtopic in subtopics if subtopic in article_text)
        score += (subtopic_matches / len(subtopics) * 50) if subtopics else 0

        return min(100, score)

    def _calculate_uniqueness_score(self, article: Article) -> float:
        """Score content uniqueness (basic plagiarism check)."""
        text = (
            article.headline + ' ' +
            article.introduction + ' ' +
            ' '.join(s.content for s in article.sections) + ' ' +
            article.conclusion
        ).lower()

        # Check for common boilerplate phrases
        boilerplate_phrases = [
            'in this article', 'in this post', 'this article will',
            'we will discuss', 'let us explore', 'there are several',
            'in conclusion', 'to summarize', 'final thoughts'
        ]

        boilerplate_count = sum(1 for phrase in boilerplate_phrases if phrase in text)

        # Check for actual content beyond boilerplate
        # Higher unique content = higher score
        boilerplate_percentage = (boilerplate_count / len(boilerplate_phrases)) * 100
        uniqueness = 100 - boilerplate_percentage

        return max(50, uniqueness)  # Minimum 50 for some baseline

    # ========================================================================
    # SEO Quality Scoring
    # ========================================================================

    def score_seo_quality(self, seo: SEOPackage, article: Article) -> SEOQualityScore:
        """Score SEO quality."""
        keyword_opt = self._score_keyword_optimization(seo, article)
        meta_quality = self._score_meta_tags(seo)
        slug_quality = self._score_slug(seo)
        schema_quality = self._score_schema_markup(seo)
        social_quality = self._score_social_optimization(seo)

        average = (keyword_opt + meta_quality + slug_quality + schema_quality + social_quality) / 5

        return SEOQualityScore(
            keyword_optimization=keyword_opt,
            meta_tag_quality=meta_quality,
            slug_quality=slug_quality,
            schema_markup_quality=schema_quality,
            social_media_optimization=social_quality,
            average_score=average,
        )

    def _score_keyword_optimization(self, seo: SEOPackage, article: Article) -> float:
        """Score keyword placement and optimization."""
        score = 0.0
        article_text = (
            article.headline + ' ' +
            article.introduction + ' ' +
            ' '.join(s.content for s in article.sections)
        ).lower()

        # Check primary keyword presence
        primary_keyword = seo.primary_keyword.lower()
        if primary_keyword in article_text:
            score += 50

        # Check secondary keyword presence
        secondary_matches = sum(1 for kw in seo.secondary_keywords if kw.lower() in article_text)
        score += (secondary_matches / len(seo.secondary_keywords) * 50) if seo.secondary_keywords else 0

        return min(100, score)

    def _score_meta_tags(self, seo: SEOPackage) -> float:
        """Score meta tag quality."""
        score = 0.0

        # Meta title length (50-60 chars is optimal)
        title_length = len(seo.meta_title)
        if 50 <= title_length <= 60:
            score += 50
        elif 40 <= title_length <= 70:
            score += 40
        else:
            score += 20

        # Meta description length (150-160 chars is optimal)
        desc_length = len(seo.meta_description)
        if 150 <= desc_length <= 160:
            score += 50
        elif 130 <= desc_length <= 170:
            score += 40
        else:
            score += 20

        return min(100, score)

    def _score_slug(self, seo: SEOPackage) -> float:
        """Score slug quality."""
        score = 50.0  # Base score
        slug = seo.slug.lower()

        # Check for hyphens
        if '-' in slug:
            score += 20

        # Check for keyword relevance
        if len(slug) <= 75 and len(slug) >= 5:  # Optimal slug length
            score += 20

        # Check for no underscores or special characters
        if not re.search(r'[_@#$%]', slug):
            score += 10

        return min(100, score)

    def _score_schema_markup(self, seo: SEOPackage) -> float:
        """Score schema markup completeness."""
        score = 0.0
        schema = seo.schema_markup

        # Check for required fields
        required_fields = ['headline', 'description', 'author', 'datePublished']
        present_fields = sum(1 for field in required_fields if field in schema)
        score += (present_fields / len(required_fields)) * 70

        # Check for optional fields
        optional_fields = ['image', 'articleBody', 'keywords']
        present_optional = sum(1 for field in optional_fields if field in schema)
        score += (present_optional / len(optional_fields)) * 30

        return min(100, score)

    def _score_social_optimization(self, seo: SEOPackage) -> float:
        """Score social media metadata optimization."""
        score = 0.0

        # Check Open Graph tags
        og = seo.open_graph
        og_required = ['og:title', 'og:description', 'og:type']
        og_present = sum(1 for field in og_required if field in og)
        score += (og_present / len(og_required)) * 50

        # Check Twitter Card
        twitter = seo.twitter_card
        twitter_required = ['twitter:card', 'twitter:title', 'twitter:description']
        twitter_present = sum(1 for field in twitter_required if field in twitter)
        score += (twitter_present / len(twitter_required)) * 50

        return min(100, score)

    # ========================================================================
    # Policy Compliance Scoring
    # ========================================================================

    def score_policy_compliance(
        self,
        article: Article,
        analysis: ContentAnalysis,
    ) -> ContentPolicyScore:
        """
        Score content for policy compliance and quality.
        Note: This is a basic algorithmic check; for production use,
        integrate with the ContentFilterAgent for comprehensive filtering.
        """
        article_text = (
            article.headline + ' ' +
            article.introduction + ' ' +
            ' '.join(s.content for s in article.sections) + ' ' +
            article.conclusion
        ).lower()

        # Initialize all scores to 100 (compliant by default)
        profanity_score = self._check_profanity_free(article_text)
        violence_score = self._check_violence_free(article_text)
        harassment_score = self._check_harassment_free(article_text)
        hate_speech_score = self._check_hate_speech_free(article_text)

        # Promotional and sponsor checks (based on analysis flags)
        promotional_score = self._score_promotional_content(analysis)
        sponsor_score = self._score_sponsor_transparency(analysis)

        # Misinformation check
        misinformation_score = self._check_misinformation_free(article_text)

        # Calculate overall compliance
        all_scores = [
            profanity_score,
            violence_score,
            harassment_score,
            hate_speech_score,
            promotional_score,
            sponsor_score,
            misinformation_score,
        ]
        overall_compliance = sum(all_scores) / len(all_scores)

        # Determine policy rating
        if overall_compliance >= 95:
            rating = "compliant"
        elif overall_compliance >= 80:
            rating = "warning"
        elif overall_compliance >= 50:
            rating = "flagged"
        else:
            rating = "blocked"

        return ContentPolicyScore(
            profanity_free_score=profanity_score,
            violence_free_score=violence_score,
            harassment_free_score=harassment_score,
            hate_speech_free_score=hate_speech_score,
            promotional_content_score=promotional_score,
            sponsor_transparency_score=sponsor_score,
            misinformation_free_score=misinformation_score,
            overall_policy_compliance=overall_compliance,
            policy_rating=rating,  # type: ignore
        )

    def _check_profanity_free(self, text: str) -> float:
        """Check for profanity in text (0-100 score)."""
        # Simple profanity patterns
        patterns = [
            r'\b(?:f[u\*]ck|shit|ass(?:hole)?|damn|crap)\b',
            r'\b(?:bitch|bastard|arsehole)\b',
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return 70.0  # Found profanity, reduce score
        return 100.0

    def _check_violence_free(self, text: str) -> float:
        """Check for violence references (0-100 score)."""
        patterns = [
            r'\b(?:kill|murder|assault|attack|stabbing|shooting)\b',
            r'graphic(?:ally)? (?:violent|graphic)',
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return 75.0
        return 100.0

    def _check_harassment_free(self, text: str) -> float:
        """Check for harassment language (0-100 score)."""
        patterns = [
            r'should (?:die|be killed|burn|hang)',
            r'\b(?:hate|loser|dumb|stupid)\s+(?:all\s+)?(?:people|them)',
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return 70.0
        return 100.0

    def _check_hate_speech_free(self, text: str) -> float:
        """Check for hate speech (0-100 score)."""
        # This is a basic check; real hate speech detection requires ML models
        # For now, we rely on basic patterns
        patterns = [
            r'\[hate speech patterns would go here\]',  # Placeholder for sensitive patterns
        ]
        return 100.0

    def _score_promotional_content(self, analysis: ContentAnalysis) -> float:
        """Score how well promotional content is handled."""
        # Check if there are promotional flags in content_flags
        promotional_flags = [f for f in analysis.content_flags if 'promotional' in f.lower()]
        if promotional_flags:
            # Content has promotional elements but they should be disclosed
            return 80.0
        return 100.0

    def _score_sponsor_transparency(self, analysis: ContentAnalysis) -> float:
        """Score sponsor disclosure transparency."""
        # Check if sponsor flags are present
        sponsor_flags = [f for f in analysis.content_flags if 'sponsor' in f.lower()]
        if sponsor_flags:
            # Sponsors mentioned but check if disclosed
            # In real implementation, check for disclosure statements
            return 85.0
        return 100.0

    def _check_misinformation_free(self, text: str) -> float:
        """Check for misinformation indicators (0-100 score)."""
        patterns = [
            r'miracle (?:cure|solution)',
            r'(?:guaranteed|proven) to cure',
            r'this one weird trick',
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return 75.0
        return 100.0

    # ========================================================================
    # Recommendations Generation
    # ========================================================================

    def generate_recommendations(
        self,
        structure: StructureCheck,
        content_quality: ContentQualityScore,
        seo_quality: SEOQualityScore,
        article: Article,
    ) -> List[QualityRecommendation]:
        """Generate improvement recommendations."""
        recommendations = []

        # Structure recommendations
        if not structure.has_headline:
            recommendations.append(QualityRecommendation(
                category="structure",
                severity="critical",
                message="Article headline is missing or too short",
                action="Add a compelling headline (minimum 10 characters)"
            ))

        if not structure.has_introduction:
            recommendations.append(QualityRecommendation(
                category="structure",
                severity="critical",
                message="Introduction is missing or too short",
                action="Add an introduction section (minimum 100 characters)"
            ))

        if not structure.has_sections:
            recommendations.append(QualityRecommendation(
                category="structure",
                severity="critical",
                message="Article lacks body sections",
                action="Add at least 3-4 main content sections"
            ))

        if not structure.has_conclusion:
            recommendations.append(QualityRecommendation(
                category="structure",
                severity="critical",
                message="Conclusion is missing or too short",
                action="Add a conclusion section (minimum 100 characters)"
            ))

        if not structure.min_word_count_met:
            recommendations.append(QualityRecommendation(
                category="structure",
                severity="warning",
                message=f"Article word count ({article.word_count}) is below minimum ({self.MIN_WORD_COUNT})",
                action="Expand sections with more detailed information"
            ))

        if not structure.sections_have_content:
            recommendations.append(QualityRecommendation(
                category="content",
                severity="warning",
                message="Some sections lack sufficient content",
                action="Ensure each section has at least 50 words of meaningful content"
            ))

        if not structure.proper_formatting:
            recommendations.append(QualityRecommendation(
                category="structure",
                severity="info",
                message="Markdown formatting could be improved",
                action="Ensure proper heading hierarchy and paragraph spacing"
            ))

        # Content quality recommendations
        if content_quality.readability_score < 50:
            recommendations.append(QualityRecommendation(
                category="style",
                severity="warning",
                message=f"Readability score is low ({content_quality.readability_score:.0f})",
                action="Use shorter sentences and simpler vocabulary"
            ))

        if content_quality.coherence_score < 60:
            recommendations.append(QualityRecommendation(
                category="content",
                severity="warning",
                message=f"Content coherence score is low ({content_quality.coherence_score:.0f})",
                action="Add transition words between sections for better flow"
            ))

        if content_quality.relevance_score < 70:
            recommendations.append(QualityRecommendation(
                category="content",
                severity="warning",
                message=f"Content relevance to main topic is low ({content_quality.relevance_score:.0f})",
                action="Ensure content directly addresses the main topic and subtopics"
            ))

        if content_quality.uniqueness_score < 60:
            recommendations.append(QualityRecommendation(
                category="content",
                severity="info",
                message=f"Content uniqueness score is moderate ({content_quality.uniqueness_score:.0f})",
                action="Add original insights, examples, and analysis"
            ))

        # SEO recommendations
        if seo_quality.keyword_optimization < 70:
            recommendations.append(QualityRecommendation(
                category="seo",
                severity="warning",
                message=f"Keyword optimization score is low ({seo_quality.keyword_optimization:.0f})",
                action="Ensure primary and secondary keywords appear naturally throughout the article"
            ))

        if seo_quality.meta_tag_quality < 70:
            recommendations.append(QualityRecommendation(
                category="seo",
                severity="warning",
                message=f"Meta tag quality score is low ({seo_quality.meta_tag_quality:.0f})",
                action="Optimize meta title (50-60 chars) and description (150-160 chars)"
            ))

        if seo_quality.schema_markup_quality < 80:
            recommendations.append(QualityRecommendation(
                category="seo",
                severity="info",
                message=f"Schema markup could be more complete ({seo_quality.schema_markup_quality:.0f})",
                action="Add more optional schema.org fields (image, articleBody, keywords)"
            ))

        if seo_quality.social_media_optimization < 80:
            recommendations.append(QualityRecommendation(
                category="seo",
                severity="info",
                message=f"Social media optimization could be improved ({seo_quality.social_media_optimization:.0f})",
                action="Ensure all Open Graph and Twitter Card tags are present"
            ))

        return recommendations

    # ========================================================================
    # Overall Assessment
    # ========================================================================

    def assess_quality(
        self,
        article: Article,
        analysis: ContentAnalysis,
        seo: SEOPackage,
    ) -> QualityAssessment:
        """Perform comprehensive quality assessment."""
        logger.info("Starting quality assessment...")

        # Check structure
        structure = self.check_article_structure(article)

        # Score content quality
        content_quality = self.score_content_quality(article, analysis)

        # Score SEO quality
        seo_quality = self.score_seo_quality(seo, article)

        # Score policy compliance
        policy_compliance = self.score_policy_compliance(article, analysis)

        # Calculate overall score (weighted average)
        # Reduce overall score if policy compliance is low
        policy_weight = 0.1
        content_weight = 0.5 - (policy_weight / 2)
        seo_weight = 0.3 - (policy_weight / 2)
        structure_weight = 0.2

        overall_score = (
            content_quality.average_score * content_weight +
            seo_quality.average_score * seo_weight +
            (structure.passed_checks / structure.total_checks * 100) * structure_weight +
            policy_compliance.overall_policy_compliance * policy_weight
        )

        # Determine quality rating
        if overall_score >= 85:
            rating = "excellent"
        elif overall_score >= 70:
            rating = "good"
        elif overall_score >= 50:
            rating = "fair"
        else:
            rating = "poor"

        # Generate recommendations
        recommendations = self.generate_recommendations(
            structure, content_quality, seo_quality, article
        )

        # Add policy compliance recommendations if needed
        if policy_compliance.policy_rating != "compliant":
            recommendations.append(QualityRecommendation(
                category="content",
                severity="warning" if policy_compliance.policy_rating == "warning" else "critical",
                message=f"Policy compliance rating: {policy_compliance.policy_rating.upper()}",
                action="Review content for policy violations and adjust as necessary"
            ))

        assessment = QualityAssessment(
            content_quality=content_quality,
            seo_quality=seo_quality,
            structure_check=structure,
            policy_compliance=policy_compliance,
            overall_score=overall_score,
            quality_rating=rating,
            recommendations=recommendations,
        )

        logger.info(f"Quality assessment complete: {rating.upper()} ({overall_score:.1f}/100)")
        logger.info(f"Policy compliance: {policy_compliance.policy_rating.upper()} ({policy_compliance.overall_policy_compliance:.1f}/100)")
        return assessment
