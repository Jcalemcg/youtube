"""Streamlit UI components for publishing and exporting."""
import streamlit as st
from pathlib import Path
from typing import Optional, Dict, List
from youtube_to_article.models.schemas import FinalOutput
from youtube_to_article.publishing.manager import PublishingManager
from youtube_to_article.publishers.base import PublishConfig, PublishingPlatform


def show_export_section(final_output: FinalOutput, output_dir: Optional[Path] = None):
    """Display export options in Streamlit.

    Args:
        final_output: Complete pipeline output.
        output_dir: Output directory for exports.
    """
    st.header("📥 Export Article")

    manager = PublishingManager(output_dir=output_dir)

    # Export format selection
    st.subheader("Select Export Formats")

    col1, col2 = st.columns(2)

    with col1:
        export_markdown = st.checkbox("📝 Markdown", value=True)
        export_json = st.checkbox("📋 JSON", value=True)

    with col2:
        export_html = st.checkbox("🌐 HTML", value=True)
        export_csv = st.checkbox("📊 CSV", value=False)

    export_formats = []
    if export_markdown:
        export_formats.append("markdown")
    if export_json:
        export_formats.append("json")
    if export_html:
        export_formats.append("html")
    if export_csv:
        export_formats.append("csv")

    if st.button("🚀 Export Now", type="primary"):
        with st.spinner("Exporting article..."):
            try:
                exports = manager.export(final_output, formats=export_formats)

                st.success("✅ Export completed successfully!")

                # Display download buttons
                st.subheader("Download Exported Files")

                cols = st.columns(len(exports))

                for idx, (fmt, filepath) in enumerate(exports.items()):
                    with cols[idx]:
                        with open(filepath, "rb") as f:
                            st.download_button(
                                label=f"Download {fmt.upper()}",
                                data=f.read(),
                                file_name=filepath.name,
                                mime=_get_mime_type(fmt),
                            )

                        st.caption(f"📂 {filepath.name}")

            except Exception as e:
                st.error(f"❌ Export failed: {str(e)}")


def show_publishing_section(final_output: FinalOutput, output_dir: Optional[Path] = None):
    """Display publishing options in Streamlit.

    Args:
        final_output: Complete pipeline output.
        output_dir: Output directory for exports.
    """
    st.header("📤 Publish to Platforms")

    manager = PublishingManager(output_dir=output_dir)

    # Platform selection
    st.subheader("Select Publishing Platforms")

    platforms = st.multiselect(
        "Where would you like to publish?",
        options=["Medium"],
        default=["Medium"],
        help="Select one or more platforms to publish your article",
    )

    if not platforms:
        st.info("ℹ️ Please select at least one platform to publish.")
        return

    # Medium specific settings
    if "Medium" in platforms:
        st.subheader("📰 Medium Settings")

        medium_token = st.text_input(
            "Medium API Token",
            type="password",
            help="Your Medium integration token. Get it from https://medium.com/me/settings",
        )

        col1, col2 = st.columns(2)

        with col1:
            publish_as_draft = st.checkbox("Publish as Draft", value=True)

        with col2:
            notify_subscribers = st.checkbox("Notify Subscribers", value=True)

        tags_input = st.text_input(
            "Tags (comma-separated)",
            value=final_output.seo.primary_keyword if final_output.seo else "",
            help="Add up to 5 tags to your article",
        )

        tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

        canonical_url = st.text_input(
            "Canonical URL (Optional)",
            value=final_output.source_video.url if final_output.source_video else "",
            help="If this article is published elsewhere, provide the original URL",
        )

        if st.button("📤 Publish to Medium", type="primary"):
            if not medium_token:
                st.error("❌ Please provide your Medium API token.")
                return

            with st.spinner("Publishing to Medium..."):
                try:
                    # Register Medium publisher
                    from youtube_to_article.publishers.medium import MediumPublisher

                    medium_publisher = MediumPublisher(medium_token)
                    manager.register_publisher("medium", medium_publisher)

                    # Create config
                    config = PublishConfig(
                        platform=PublishingPlatform.MEDIUM,
                        draft=publish_as_draft,
                        tags=tags,
                        canonical_url=canonical_url if canonical_url else None,
                        notify_subscribers=notify_subscribers,
                    )

                    # Publish
                    result = manager.publish(final_output, "medium", config)

                    if result.url:
                        st.success(f"✅ Published to Medium!")
                        st.info(f"📌 Article URL: [Read on Medium]({result.url})")

                        if publish_as_draft:
                            st.info("📝 Article is saved as draft. Visit Medium to review and publish.")

                        # Show metadata
                        with st.expander("View Publishing Details"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Status", result.status.value)
                                st.metric("Platform", result.platform.value)
                            with col2:
                                st.metric("Published At", result.timestamp.strftime("%Y-%m-%d %H:%M"))
                                if result.article_id:
                                    st.text(f"Article ID: {result.article_id}")

                    else:
                        st.error(f"❌ Publishing failed: {result.error}")

                except Exception as e:
                    st.error(f"❌ Error publishing to Medium: {str(e)}")


def show_publishing_history_section(
    video_id: str, article_slug: str, output_dir: Optional[Path] = None
):
    """Display publishing history.

    Args:
        video_id: Video ID.
        article_slug: Article slug.
        output_dir: Output directory.
    """
    st.header("📋 Publishing History")

    manager = PublishingManager(output_dir=output_dir)
    history = manager.get_publishing_history(video_id, article_slug)

    if not history or not history.results:
        st.info("ℹ️ No publishing history available yet.")
        return

    # Display history
    st.subheader(f"Publishing History for: {article_slug}")

    for idx, result in enumerate(history.results, 1):
        with st.expander(
            f"{idx}. {result.platform.value.upper()} - {result.status.value.upper()}",
            expanded=idx == len(history.results),
        ):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Platform", result.platform.value)
                st.metric("Status", result.status.value)

            with col2:
                st.metric("Published", result.timestamp.strftime("%Y-%m-%d"))
                st.metric("Time", result.timestamp.strftime("%H:%M:%S"))

            with col3:
                if result.url:
                    st.markdown(f"🔗 [View Article]({result.url})")
                if result.error:
                    st.error(f"Error: {result.error}")

            if result.metadata:
                st.caption("Metadata:")
                for key, value in result.metadata.items():
                    st.text(f"{key}: {value}")


def show_statistics_section(output_dir: Optional[Path] = None):
    """Display publishing statistics.

    Args:
        output_dir: Output directory.
    """
    st.header("📊 Publishing Statistics")

    manager = PublishingManager(output_dir=output_dir)
    stats = manager.get_statistics()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Articles", stats["total_articles"])

    with col2:
        st.metric("Total Publishes", stats["total_publishes"])

    with col3:
        success_count = stats["by_status"].get("published", 0)
        st.metric("Published", success_count)

    # Platform breakdown
    if stats["by_platform"]:
        st.subheader("By Platform")
        st.bar_chart(stats["by_platform"])

    # Status breakdown
    if stats["by_status"]:
        st.subheader("By Status")
        st.bar_chart(stats["by_status"])


def _get_mime_type(format: str) -> str:
    """Get MIME type for file format.

    Args:
        format: File format.

    Returns:
        MIME type string.
    """
    mime_types = {
        "markdown": "text/markdown",
        "json": "application/json",
        "html": "text/html",
        "csv": "text/csv",
    }
    return mime_types.get(format, "application/octet-stream")
