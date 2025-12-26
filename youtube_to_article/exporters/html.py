"""HTML format exporter."""
import html
from pathlib import Path
from typing import Optional
from markdown import markdown as md_to_html
from youtube_to_article.models.schemas import FinalOutput
from .base import BaseExporter


class HTMLExporter(BaseExporter):
    """Export articles in HTML format."""

    @property
    def file_extension(self) -> str:
        """Return file extension."""
        return "html"

    def export(self, final_output: FinalOutput, filename: Optional[str] = None) -> Path:
        """Export to HTML format.

        Args:
            final_output: Pipeline output.
            filename: Optional custom filename.

        Returns:
            Path to exported file.
        """
        filename = filename or self.get_default_filename(final_output)
        output_path = self.get_output_path(filename)

        # Build HTML content
        content = self._build_html(final_output)

        # Write to file
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def _build_html(self, final_output: FinalOutput) -> str:
        """Build HTML content from pipeline output.

        Args:
            final_output: Pipeline output.

        Returns:
            Formatted HTML string.
        """
        article = final_output.article
        seo = final_output.seo
        video = final_output.source_video

        # Convert markdown sections to HTML
        intro_html = md_to_html(article.introduction)
        sections_html = ""
        for section in article.sections:
            sections_html += f"<h2>{html.escape(section.heading)}</h2>\n"
            sections_html += md_to_html(section.content) + "\n"

        conclusion_html = md_to_html(article.conclusion)

        # Build HTML document
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(article.headline)}</title>
    {self._build_meta_tags(seo)}
    <style>
        {self._build_css()}
    </style>
</head>
<body>
    <article>
        <header>
            <h1>{html.escape(article.headline)}</h1>
            <div class="article-meta">
                <span class="source">Source: <a href="{html.escape(video.url)}" target="_blank">{html.escape(video.title)}</a></span>
                <span class="channel">Channel: {html.escape(video.channel)}</span>
                <span class="generated">Generated: {final_output.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</span>
            </div>
        </header>

        <section class="introduction">
            {intro_html}
        </section>

        <main>
            {sections_html}
        </main>

        <section class="conclusion">
            <h2>Conclusion</h2>
            {conclusion_html}
        </section>

        {self._build_metadata_section(final_output)}
    </article>
</body>
</html>"""

        return html_content

    def _build_meta_tags(self, seo) -> str:
        """Build meta tags from SEO package.

        Args:
            seo: SEO package.

        Returns:
            Meta tags HTML string.
        """
        if not seo:
            return ""

        tags = f"""<meta name="description" content="{html.escape(seo.meta_description)}">
    <meta name="keywords" content="{html.escape(', '.join([seo.primary_keyword] + seo.secondary_keywords))}">
    <meta property="og:title" content="{html.escape(seo.open_graph.get('title', ''))}">
    <meta property="og:description" content="{html.escape(seo.open_graph.get('description', ''))}">
    <meta name="twitter:title" content="{html.escape(seo.twitter_card.get('title', ''))}">
    <meta name="twitter:description" content="{html.escape(seo.twitter_card.get('description', ''))}">"""

        return tags

    def _build_metadata_section(self, final_output: FinalOutput) -> str:
        """Build metadata section if available.

        Args:
            final_output: Pipeline output.

        Returns:
            Metadata section HTML.
        """
        if not final_output.seo:
            return ""

        seo = final_output.seo
        keywords = ", ".join([seo.primary_keyword] + seo.secondary_keywords)

        return f"""<footer class="metadata">
            <h3>Article Metadata</h3>
            <dl>
                <dt>Slug</dt>
                <dd>{html.escape(seo.slug)}</dd>
                <dt>Primary Keyword</dt>
                <dd>{html.escape(seo.primary_keyword)}</dd>
                <dt>Keywords</dt>
                <dd>{html.escape(keywords)}</dd>
                <dt>Reading Time</dt>
                <dd>{final_output.article.word_count // 200} minutes</dd>
            </dl>
        </footer>"""

    def _build_css(self) -> str:
        """Build CSS styles.

        Returns:
            CSS string.
        """
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f9f9f9;
            padding: 20px;
        }

        article {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        header {
            border-bottom: 2px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 15px;
            color: #1a1a1a;
        }

        h2 {
            font-size: 1.8em;
            margin-top: 30px;
            margin-bottom: 15px;
            color: #333;
            border-left: 4px solid #007bff;
            padding-left: 15px;
        }

        h3 {
            font-size: 1.3em;
            margin-top: 20px;
            margin-bottom: 10px;
            color: #555;
        }

        p {
            margin-bottom: 15px;
            text-align: justify;
        }

        a {
            color: #007bff;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }

        pre {
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 15px 0;
            border-left: 4px solid #007bff;
        }

        blockquote {
            border-left: 4px solid #ddd;
            padding-left: 20px;
            margin: 20px 0;
            color: #666;
            font-style: italic;
        }

        .article-meta {
            font-size: 0.9em;
            color: #666;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }

        .article-meta span {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .introduction {
            font-size: 1.1em;
            margin-bottom: 30px;
            padding: 15px;
            background-color: #f0f7ff;
            border-radius: 5px;
        }

        main {
            margin: 30px 0;
        }

        .conclusion {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #007bff;
        }

        footer.metadata {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #eee;
            font-size: 0.9em;
            color: #666;
        }

        footer.metadata dl {
            display: grid;
            grid-template-columns: 150px 1fr;
            gap: 15px;
        }

        footer.metadata dt {
            font-weight: bold;
            color: #333;
        }

        footer.metadata dd {
            color: #666;
        }

        @media (max-width: 768px) {
            article {
                padding: 20px;
            }

            h1 {
                font-size: 1.8em;
            }

            h2 {
                font-size: 1.4em;
            }

            .article-meta {
                flex-direction: column;
                gap: 8px;
            }
        }
        """
