"""Content filtering agent for policy compliance and quality checks."""
import re
from typing import List, Dict, Tuple
from youtube_to_article.models.schemas import (
    TranscriptResult,
    ContentFilterResult,
    ContentPolicyFlag,
)


class ContentFilterAgent:
    """
    Comprehensive content filtering system with multiple detection layers:
    - Profanity detection
    - Sponsor and promotional content detection
    - Quality heuristics (misinformation, spam indicators)
    - Violence and harassment detection
    """

    def __init__(self):
        """Initialize the content filter with detection patterns."""
        self.profanity_patterns = self._init_profanity_patterns()
        self.sponsor_keywords = self._init_sponsor_keywords()
        self.promotional_indicators = self._init_promotional_indicators()
        self.misinformation_patterns = self._init_misinformation_patterns()
        self.violence_patterns = self._init_violence_patterns()

    def filter_transcript(self, transcript: TranscriptResult) -> ContentFilterResult:
        """
        Analyze transcript for policy violations and content issues.

        Args:
            transcript: The transcript result to filter

        Returns:
            ContentFilterResult with all detected flags and scores
        """
        text = transcript.transcript.lower()
        flags: List[ContentPolicyFlag] = []

        # Run all detection layers
        flags.extend(self._detect_profanity(text))
        flags.extend(self._detect_violence(text))
        flags.extend(self._detect_harassment(text))
        sponsor_flags, sponsor_mentions = self._detect_sponsors(text)
        flags.extend(sponsor_flags)
        flags.extend(self._detect_misinformation(text))
        flags.extend(self._detect_spam(text))

        # Calculate promotional score
        promo_score, promo_flags = self._calculate_promotional_score(text)
        flags.extend(promo_flags)

        # Determine overall compliance status
        critical_flags = [f for f in flags if f.severity == "critical"]
        high_flags = [f for f in flags if f.severity == "high"]

        if critical_flags:
            compliance_status = "blocked"
        elif high_flags:
            compliance_status = "flagged"
        elif flags:
            compliance_status = "warning"
        else:
            compliance_status = "compliant"

        # Generate summary
        summary = self._generate_summary(flags, promo_score, sponsor_mentions)

        return ContentFilterResult(
            flags=flags,
            has_critical_issues=len(critical_flags) > 0,
            overall_compliance=compliance_status,  # type: ignore
            summary=summary,
            is_sponsor_content=len(sponsor_mentions) > 0,
            sponsor_mentions=sponsor_mentions,
            promotional_score=promo_score,
            quality_issues=self._identify_quality_issues(flags),
        )

    def _init_profanity_patterns(self) -> List[Tuple[str, str]]:
        """
        Initialize profanity detection patterns.
        Returns list of (pattern, description) tuples.
        """
        return [
            # Explicit profanity (common patterns)
            (r"\b(?:f[u\*]ck|shit|ass(?:hole)?|damn|crap)\b", "Strong profanity detected"),
            (r"\b(?:bitch|bastard|arsehole)\b", "Moderate profanity detected"),
            (r"\b(?:hell|piss(?:ed)?)\b", "Mild profanity detected"),
            # Slurs and offensive terms (basic detection)
            (r"(?i)\b(?:retard|stupid|idiot|moron)\b", "Offensive language detected"),
        ]

    def _init_sponsor_keywords(self) -> Dict[str, int]:
        """
        Initialize sponsor and brand mention keywords.
        Returns dict of {keyword: priority} for matching.
        """
        return {
            # Common sponsor/brand keywords
            "sponsored": 3,
            "sponsor": 3,
            "ad": 2,
            "advertisement": 3,
            "partner": 2,
            "partnership": 2,
            "affiliate": 2,
            "affiliate link": 3,
            "discount code": 2,
            "promo code": 2,
            "use code": 2,
            "promotion": 1,
            "click link below": 2,
            "buy now": 1,
            "shop now": 1,
            "purchase": 1,
            "brand": 1,
            "product placement": 3,
            "in collaboration with": 2,
            "brought to you by": 3,
            "this video is brought": 3,
        }

    def _init_promotional_indicators(self) -> List[str]:
        """Initialize patterns for detecting promotional content."""
        return [
            r"(?i)buy|purchase|order|get yours|limited time|special offer",
            r"(?i)exclusive|only|today|now|don't miss|act now",
            r"(?i)save money|discount|sale|coupon|promo",
            r"(?i)free (shipping|delivery|trial|sample)",
            r"(?i)\$\d+|discount|% off|free offer",
        ]

    def _init_misinformation_patterns(self) -> List[Tuple[str, str]]:
        """Initialize patterns for detecting potential misinformation."""
        return [
            (r"(?i)no scientific evidence|scientifically unproven|false claim", "Disputed claim acknowledged"),
            (r"(?i)conspiracy|illuminati|cover.?up|hidden truth", "Conspiracy theory language"),
            (r"(?i)cure(?:s|d)? (?:cancer|diabetes|autism|covid)", "Unverified medical claims"),
            (r"(?i)miracle|guaranteed cure|secret formula", "Dubious health claims"),
            (r"(?i)this one weird trick|doctors hate this", "Clickbait health language"),
        ]

    def _init_violence_patterns(self) -> List[Tuple[str, str]]:
        """Initialize patterns for detecting violence references."""
        return [
            (r"(?i)\bkill\b.*\b(?:person|people|victim|them)\b", "Violence reference"),
            (r"(?i)\b(?:murder|assault|attack|stabbing|shooting)\b", "Violence terminology"),
            (r"(?i)\b(?:rape|sexual assault)\b", "Sexual violence reference"),
            (r"(?i)graphic(?:ally)? (?:violent|graphic)|brutal", "Explicit violence description"),
        ]

    def _detect_profanity(self, text: str) -> List[ContentPolicyFlag]:
        """Detect profanity in text."""
        flags = []
        for pattern, description in self.profanity_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                snippet = match.group()[:50]
                flags.append(
                    ContentPolicyFlag(
                        category="profanity",
                        severity="high",
                        text=snippet,
                        message=description,
                        confidence=0.95,
                        position=self._get_text_position(text, match.start()),
                    )
                )
        return flags

    def _detect_violence(self, text: str) -> List[ContentPolicyFlag]:
        """Detect violence references in text."""
        flags = []
        for pattern, description in self.violence_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                snippet = match.group()[:50]
                flags.append(
                    ContentPolicyFlag(
                        category="violence",
                        severity="high",
                        text=snippet,
                        message=description,
                        confidence=0.85,
                        position=self._get_text_position(text, match.start()),
                    )
                )
        return flags

    def _detect_harassment(self, text: str) -> List[ContentPolicyFlag]:
        """Detect harassment and hate speech patterns."""
        flags = []
        harassment_patterns = [
            (r"(?i)\b(?:hate|stupid|dumb|loser)\s+(?:all\s+)?(?:people|them|you|women|men)\b", "Derogatory language"),
            (r"(?i)should (?:die|be killed|burn|hang)", "Threatening language"),
        ]

        for pattern, description in harassment_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                snippet = match.group()[:50]
                flags.append(
                    ContentPolicyFlag(
                        category="harassment",
                        severity="high",
                        text=snippet,
                        message=description,
                        confidence=0.80,
                        position=self._get_text_position(text, match.start()),
                    )
                )
        return flags

    def _detect_sponsors(self, text: str) -> Tuple[List[ContentPolicyFlag], List[str]]:
        """
        Detect sponsor mentions and promotional content.
        Returns (flags, sponsor_mentions).
        """
        flags = []
        sponsors = []

        for keyword, priority in self.sponsor_keywords.items():
            pattern = rf"(?i)\b{re.escape(keyword)}\b"
            matches = list(re.finditer(pattern, text))

            if matches:
                sponsors.append(keyword)
                # Only flag if high priority (not just generic terms like "brand")
                if priority >= 2 and len(matches) <= 3:  # Don't flag excessive mentions
                    for match in matches[:1]:  # Only flag first mention
                        snippet = text[max(0, match.start()-20):min(len(text), match.end()+20)]
                        flags.append(
                            ContentPolicyFlag(
                                category="sponsor",
                                severity="low",
                                text=keyword,
                                message=f"Sponsor/promotional keyword: '{keyword}' mentioned",
                                confidence=0.9 if priority == 3 else 0.7,
                                position=self._get_text_position(text, match.start()),
                            )
                        )

        return flags, sponsors

    def _detect_misinformation(self, text: str) -> List[ContentPolicyFlag]:
        """Detect potential misinformation indicators."""
        flags = []
        for pattern, description in self.misinformation_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                snippet = match.group()[:50]
                flags.append(
                    ContentPolicyFlag(
                        category="misinformation",
                        severity="medium",
                        text=snippet,
                        message=description,
                        confidence=0.75,
                        position=self._get_text_position(text, match.start()),
                    )
                )
        return flags

    def _detect_spam(self, text: str) -> List[ContentPolicyFlag]:
        """Detect spam indicators."""
        flags = []

        # Multiple calls-to-action
        cta_patterns = [
            r"(?i)click (?:the )?link",
            r"(?i)subscribe|like|comment|share",
            r"(?i)hit the notification bell",
            r"(?i)follow (?:me|us)",
        ]

        cta_count = sum(len(re.findall(pattern, text)) for pattern in cta_patterns)

        # Excessive CTAs (more than 10) indicate spam-like behavior
        if cta_count > 10:
            flags.append(
                ContentPolicyFlag(
                    category="spam",
                    severity="low",
                    text="Multiple CTAs",
                    message=f"Excessive calls-to-action detected ({cta_count} mentions) - indicates promotional content",
                    confidence=0.8,
                )
            )

        return flags

    def _calculate_promotional_score(self, text: str) -> Tuple[float, List[ContentPolicyFlag]]:
        """
        Calculate promotional content score (0-1).
        Returns (score, flags).
        """
        flags = []
        indicators_found = 0
        total_indicators = len(self.promotional_indicators)

        for indicator in self.promotional_indicators:
            if re.search(indicator, text):
                indicators_found += 1

        # Calculate score: 0 = not promotional, 1 = highly promotional
        promo_score = min(1.0, indicators_found / max(1, total_indicators * 0.5))

        if promo_score > 0.6:
            flags.append(
                ContentPolicyFlag(
                    category="promotional",
                    severity="low",
                    text=f"Promotional score: {promo_score:.2f}",
                    message="Content contains multiple promotional indicators",
                    confidence=0.85,
                )
            )

        return promo_score, flags

    def _identify_quality_issues(self, flags: List[ContentPolicyFlag]) -> List[str]:
        """Extract quality issues from flags."""
        quality_issues = []

        # Categorize flags by severity
        for flag in flags:
            if flag.severity in ["critical", "high"]:
                quality_issues.append(f"{flag.category.replace('_', ' ').title()}: {flag.message}")

        return quality_issues

    def _generate_summary(
        self, flags: List[ContentPolicyFlag], promo_score: float, sponsors: List[str]
    ) -> str:
        """Generate a human-readable summary of filtering results."""
        if not flags and promo_score <= 0.3 and not sponsors:
            return "Content passed all policy checks. No issues detected."

        parts = []

        # Count by category
        categories = {}
        for flag in flags:
            categories[flag.category] = categories.get(flag.category, 0) + 1

        if categories:
            category_str = ", ".join(f"{count} {cat}" for cat, count in categories.items())
            parts.append(f"Issues detected: {category_str}")

        if promo_score > 0.4:
            parts.append(f"Promotional content score: {promo_score:.1%}")

        if sponsors:
            parts.append(f"Sponsor mentions: {', '.join(sponsors[:3])}")

        return " | ".join(parts) if parts else "Content review completed."

    def _get_text_position(self, text: str, char_index: int) -> str:
        """
        Get human-readable position in text (e.g., 'paragraph 2', 'word 45').
        """
        # Find which paragraph
        paragraphs = text.split("\n")
        char_count = 0
        for para_idx, para in enumerate(paragraphs):
            char_count += len(para) + 1  # +1 for newline
            if char_count > char_index:
                return f"paragraph {para_idx + 1}"

        return f"word {len(text[:char_index].split()) + 1}"
