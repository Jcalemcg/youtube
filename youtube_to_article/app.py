"""
YouTube to Article Converter - Streamlit Web UI

Multi-stage workflow with approval checkpoints:
1. Input YouTube URL
2. Transcribe → Review transcript
3. Analyze → Review analysis
4. Generate Article → Edit/approve
5. Generate SEO → Final review
6. Download/Export
"""
import streamlit as st
import logging
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline import create_pipeline
from models.schemas import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# YouTube Theme Colors
YOUTUBE_RED = "#FF0000"
YOUTUBE_DARK = "#282828"
YOUTUBE_LIGHT_GRAY = "#F9F9F9"
YOUTUBE_GRAY = "#909090"

# Page config
st.set_page_config(
    page_title="YouTube to Article Converter",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for YouTube theme
st.markdown(f"""
<style>
    /* Main theme */
    .stApp {{
        background-color: {YOUTUBE_DARK};
    }}

    /* Headers */
    h1, h2, h3 {{
        color: white !important;
    }}

    /* YouTube Red accents */
    .stButton>button {{
        background-color: {YOUTUBE_RED};
        color: white;
        border: none;
        border-radius: 2px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }}

    .stButton>button:hover {{
        background-color: #CC0000;
    }}

    /* Input fields */
    .stTextInput>div>div>input {{
        background-color: #121212;
        color: white;
        border: 1px solid #303030;
    }}

    /* Text areas */
    .stTextArea>div>div>textarea {{
        background-color: #121212;
        color: white;
        border: 1px solid #303030;
    }}

    /* Success/Info boxes */
    .stSuccess {{
        background-color: #0F9D58;
        color: white;
    }}

    /* Progress bar */
    .stProgress > div > div > div > div {{
        background-color: {YOUTUBE_RED};
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: #212121;
    }}

    /* Cards */
    .element-container {{
        color: white;
    }}
</style>
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    """Initialize session state variables."""
    if 'stage' not in st.session_state:
        st.session_state.stage = 0  # 0=input, 1=transcribe, 2=analyze, 3=write, 4=seo, 5=complete
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = None
    if 'transcript' not in st.session_state:
        st.session_state.transcript = None
    if 'analysis' not in st.session_state:
        st.session_state.analysis = None
    if 'article' not in st.session_state:
        st.session_state.article = None
    if 'seo' not in st.session_state:
        st.session_state.seo = None
    if 'youtube_url' not in st.session_state:
        st.session_state.youtube_url = ""


def reset_workflow():
    """Reset workflow to start."""
    st.session_state.stage = 0
    st.session_state.transcript = None
    st.session_state.analysis = None
    st.session_state.article = None
    st.session_state.seo = None
    st.session_state.youtube_url = ""


def show_progress():
    """Show progress indicator."""
    stages = ["📝 Input", "🎤 Transcribe", "🔍 Analyze", "✍️ Write", "🚀 SEO", "✅ Complete"]
    current_stage = st.session_state.stage

    cols = st.columns(len(stages))
    for i, (col, stage_name) in enumerate(zip(cols, stages)):
        with col:
            if i < current_stage:
                st.success(stage_name)
            elif i == current_stage:
                st.info(f"**{stage_name}**")
            else:
                st.text(stage_name)


def stage0_input():
    """Stage 0: YouTube URL Input"""
    st.title("🎥 YouTube to Article Converter")
    st.markdown("---")

    st.markdown("""
    ### Welcome!
    Convert any YouTube video into an SEO-optimized article.

    **How it works:**
    1. 📝 Paste YouTube URL
    2. 🎤 Extract & review transcript
    3. 🔍 Analyze content structure
    4. ✍️ Generate article with AI
    5. 🚀 Add SEO optimization
    6. ✅ Download your article
    """)

    st.markdown("---")

    # URL input
    youtube_url = st.text_input(
        "Enter YouTube Video URL",
        placeholder="https://www.youtube.com/watch?v=...",
        value=st.session_state.youtube_url
    )

    # Example URLs
    with st.expander("📌 Example URLs"):
        st.code("https://www.youtube.com/watch?v=jNQXAC9IVRw")
        st.code("https://youtu.be/dQw4w9WgXcQ")

    col1, col2 = st.columns([3, 1])

    with col1:
        if st.button("🚀 Start Conversion", type="primary"):
            if youtube_url:
                st.session_state.youtube_url = youtube_url
                st.session_state.stage = 1
                st.rerun()
            else:
                st.error("Please enter a YouTube URL")

    with col2:
        force_whisper = st.checkbox("Force Whisper", help="Skip captions, use Whisper transcription")
        st.session_state.force_whisper = force_whisper


def stage1_transcribe():
    """Stage 1: Transcription"""
    st.title("🎤 Stage 1: Transcription")
    show_progress()
    st.markdown("---")

    if st.session_state.transcript is None:
        # Create status containers
        status_container = st.empty()
        progress_container = st.empty()
        preview_container = st.empty()

        try:
            # Initialize pipeline if not already done
            if st.session_state.pipeline is None:
                status_container.info("🔧 Initializing pipeline...")
                st.session_state.pipeline = create_pipeline()
                status_container.success("✓ Pipeline ready")

            # Show what's happening
            status_container.info("🎥 Fetching video metadata...")

            # Run transcription
            transcript = st.session_state.pipeline.stage1_transcribe(
                st.session_state.youtube_url,
                force_whisper=st.session_state.get('force_whisper', False)
            )

            # Show success with actual data
            status_container.success(f"✓ Transcription complete: {len(transcript.segments)} segments extracted!")

            # Show preview of first segments
            with preview_container.container():
                st.subheader("📝 First Segments Preview:")
                for i, segment in enumerate(transcript.segments[:3]):
                    st.markdown(f"**[{segment.start:.1f}s]** {segment.text[:100]}...")
                st.info(f"... and {len(transcript.segments) - 3} more segments")

            st.session_state.transcript = transcript

            import time
            time.sleep(1)  # Let user see the preview
            st.rerun()

        except Exception as e:
            status_container.error(f"❌ Transcription failed: {e}")
            logger.error(f"Transcription error: {e}", exc_info=True)
            if st.button("← Back"):
                reset_workflow()
                st.rerun()
            return

    # Show transcript
    transcript = st.session_state.transcript

    st.success(f"✅ Transcript extracted successfully!")

    # Video info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Video Title", transcript.title)
    with col2:
        st.metric("Channel", transcript.channel)
    with col3:
        st.metric("Duration", f"{transcript.duration_seconds}s")

    st.markdown("---")

    # Transcript preview
    st.subheader("📄 Transcript")
    st.info(f"**Source:** {transcript.source} | **Language:** {transcript.language} | **Segments:** {len(transcript.segments)}")

    # Show full transcript in expandable text area
    st.text_area(
        "Full Transcript",
        transcript.transcript,
        height=300,
        help="Review the transcript before continuing"
    )

    # Show segments
    with st.expander(f"🔍 View {len(transcript.segments)} Segments"):
        for i, segment in enumerate(transcript.segments[:10]):  # Show first 10
            st.markdown(f"**[{segment.start:.1f}s - {segment.end:.1f}s]** {segment.text}")
        if len(transcript.segments) > 10:
            st.info(f"... and {len(transcript.segments) - 10} more segments")

    st.markdown("---")

    # Actions
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("← Back"):
            reset_workflow()
            st.rerun()

    with col2:
        if st.button("✓ Approve & Continue →", type="primary"):
            st.session_state.stage = 2
            st.rerun()


def stage2_analyze():
    """Stage 2: Content Analysis"""
    st.title("🔍 Stage 2: Content Analysis")
    show_progress()
    st.markdown("---")

    if st.session_state.analysis is None:
        # Create status containers
        status_container = st.empty()
        preview_container = st.empty()

        try:
            status_container.info("🤖 AI is analyzing content structure... (using Llama 3.3 70B)")

            # Run analysis
            analysis = st.session_state.pipeline.stage2_analyze(st.session_state.transcript)

            # Show success with snippets
            status_container.success(f"✓ Analysis complete: {len(analysis.subtopics)} topics, {len(analysis.suggested_sections)} sections identified!")

            # Show preview
            with preview_container.container():
                st.subheader("🎯 AI Detected:")
                st.markdown(f"**Main Topic:** {analysis.main_topic}")
                st.markdown(f"**Key Subtopics:**")
                for subtopic in analysis.subtopics[:3]:
                    st.markdown(f"- {subtopic}")
                if len(analysis.subtopics) > 3:
                    st.info(f"... and {len(analysis.subtopics) - 3} more")

            st.session_state.analysis = analysis

            import time
            time.sleep(1.5)  # Let user see the preview
            st.rerun()

        except Exception as e:
            status_container.error(f"❌ Analysis failed: {e}")
            logger.error(f"Analysis error: {e}", exc_info=True)
            if st.button("← Back"):
                st.session_state.stage = 1
                st.rerun()
            return

    # Show analysis
    analysis = st.session_state.analysis

    st.success("✅ Content analysis complete!")

    # Key metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Subtopics Found", len(analysis.subtopics))
    with col2:
        st.metric("Suggested Sections", len(analysis.suggested_sections))

    st.markdown("---")

    # Main topic
    st.subheader("📌 Main Topic")
    st.info(analysis.main_topic)

    # Subtopics
    st.subheader("🎯 Key Subtopics")
    for i, subtopic in enumerate(analysis.subtopics, 1):
        st.markdown(f"{i}. {subtopic}")

    # Suggested sections
    st.subheader("📑 Suggested Article Structure")
    for section in analysis.suggested_sections:
        with st.expander(f"📄 {section.title}"):
            st.write(section.description)
            if section.start_time:
                st.caption(f"⏱️ {section.start_time}s - {section.end_time}s")

    # Key quotes
    if analysis.key_quotes:
        with st.expander(f"💬 Key Quotes ({len(analysis.key_quotes)})"):
            for quote in analysis.key_quotes:
                st.markdown(f"> \"{quote.text}\" *[{quote.timestamp}s]*")

    st.markdown("---")

    # Actions
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back"):
            st.session_state.stage = 1
            st.session_state.analysis = None
            st.rerun()

    with col2:
        if st.button("✓ Approve & Generate Article →", type="primary"):
            st.session_state.stage = 3
            st.rerun()


def stage3_write():
    """Stage 3: Article Generation"""
    st.title("✍️ Stage 3: Article Generation")
    show_progress()
    st.markdown("---")

    if st.session_state.article is None:
        # Create status containers
        status_container = st.empty()
        progress_bar = st.empty()
        preview_container = st.empty()

        try:
            status_container.info("✍️ AI is writing your article... (using Llama 3.3 70B)")
            progress_bar.progress(0.3, text="Crafting headline and introduction...")

            # Run article generation
            article = st.session_state.pipeline.stage3_write(
                st.session_state.transcript,
                st.session_state.analysis
            )

            progress_bar.progress(1.0, text="Article complete!")

            # Show success with snippets
            status_container.success(f"✓ Article generated: {article.word_count} words, {len(article.sections)} sections!")

            # Show preview
            with preview_container.container():
                st.subheader("📰 Article Preview:")
                st.markdown(f"# {article.headline}")
                st.markdown(article.introduction[:200] + "...")
                st.info(f"✓ {len(article.sections)} sections written")

            st.session_state.article = article

            import time
            time.sleep(1.5)  # Let user see the preview
            st.rerun()

        except Exception as e:
            status_container.error(f"❌ Article generation failed: {e}")
            logger.error(f"Article generation error: {e}", exc_info=True)
            if st.button("← Back"):
                st.session_state.stage = 2
                st.rerun()
            return

    # Show article
    article = st.session_state.article

    st.success("✅ Article generated successfully!")

    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Word Count", article.word_count)
    with col2:
        st.metric("Sections", len(article.sections))
    with col3:
        reading_time = article.word_count // 200
        st.metric("Reading Time", f"{reading_time} min")

    st.markdown("---")

    # Article preview
    st.subheader("📰 Article Preview")

    # Headline
    st.markdown(f"# {article.headline}")

    # Introduction
    st.markdown(article.introduction)

    # Sections
    for section in article.sections:
        st.markdown(f"## {section.heading}")
        st.markdown(section.content)

    # Conclusion
    if article.conclusion:
        st.markdown("## Conclusion")
        st.markdown(article.conclusion)

    st.markdown("---")

    # Full markdown
    with st.expander("📝 View Full Markdown"):
        st.code(article.markdown, language="markdown")

    st.markdown("---")

    # Actions
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back"):
            st.session_state.stage = 2
            st.session_state.article = None
            st.rerun()

    with col2:
        if st.button("✓ Approve & Add SEO →", type="primary"):
            st.session_state.stage = 4
            st.rerun()


def stage4_seo():
    """Stage 4: SEO Optimization"""
    st.title("🚀 Stage 4: SEO Optimization")
    show_progress()
    st.markdown("---")

    if st.session_state.seo is None:
        # Create status containers
        status_container = st.empty()
        preview_container = st.empty()

        try:
            status_container.info("🚀 AI is optimizing for SEO... (using Llama 3.1 8B)")

            # Run SEO generation
            seo = st.session_state.pipeline.stage4_optimize_seo(
                st.session_state.article,
                st.session_state.analysis,
                st.session_state.transcript
            )

            # Show success with snippets
            status_container.success(f"✓ SEO package complete: {len(seo.secondary_keywords) + 1} keywords, meta tags, social posts!")

            # Show preview
            with preview_container.container():
                st.subheader("🔑 SEO Preview:")
                st.markdown(f"**Meta Title:** {seo.meta_title}")
                st.markdown(f"**Primary Keyword:** {seo.primary_keyword}")
                st.markdown(f"**URL Slug:** {seo.slug}")
                st.info(f"✓ Meta tags, Open Graph, Twitter Card, and social posts ready!")

            st.session_state.seo = seo

            import time
            time.sleep(1.5)  # Let user see the preview
            st.rerun()

        except Exception as e:
            status_container.error(f"❌ SEO generation failed: {e}")
            logger.error(f"SEO error: {e}", exc_info=True)
            if st.button("← Back"):
                st.session_state.stage = 3
                st.rerun()
            return

    # Show SEO
    seo = st.session_state.seo

    st.success("✅ SEO package generated!")

    st.markdown("---")

    # Meta tags
    st.subheader("🏷️ Meta Tags")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Meta Title", seo.meta_title, disabled=True)
        st.text_input("URL Slug", seo.slug, disabled=True)
    with col2:
        st.text_area("Meta Description", seo.meta_description, disabled=True)

    # Keywords
    st.subheader("🔑 Keywords")
    st.info(f"**Primary:** {seo.primary_keyword}")
    st.write(f"**Secondary:** {', '.join(seo.secondary_keywords)}")

    # Social Media
    st.subheader("📱 Social Media Posts")
    col1, col2 = st.columns(2)
    with col1:
        st.text_area("Twitter/X", seo.social_posts.twitter, height=100, disabled=True)
    with col2:
        st.text_area("LinkedIn", seo.social_posts.linkedin, height=100, disabled=True)

    st.markdown("---")

    # Actions
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back"):
            st.session_state.stage = 3
            st.session_state.seo = None
            st.rerun()

    with col2:
        if st.button("✓ Complete & Download →", type="primary"):
            st.session_state.stage = 5
            st.rerun()


def stage5_complete():
    """Stage 5: Complete & Download"""
    st.title("✅ Conversion Complete!")
    show_progress()
    st.markdown("---")

    st.success("🎉 Your YouTube video has been successfully converted to an article!")

    # Summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Words", st.session_state.article.word_count)
    with col2:
        st.metric("Sections", len(st.session_state.article.sections))
    with col3:
        st.metric("Keywords", len(st.session_state.seo.secondary_keywords) + 1)

    st.markdown("---")

    # Download options
    st.subheader("📥 Download Your Article")

    # Markdown download
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📄 Download Markdown",
            data=st.session_state.article.markdown,
            file_name=f"{st.session_state.seo.slug}.md",
            mime="text/markdown"
        )

    with col2:
        # JSON download
        import json
        final_output = {
            "article": st.session_state.article.model_dump(),
            "seo": st.session_state.seo.model_dump(),
            "transcript": st.session_state.transcript.model_dump()
        }
        st.download_button(
            label="📦 Download Full Package (JSON)",
            data=json.dumps(final_output, indent=2, default=str),
            file_name=f"{st.session_state.seo.slug}_complete.json",
            mime="application/json"
        )

    st.markdown("---")

    # Start new conversion
    if st.button("🔄 Convert Another Video", type="primary"):
        reset_workflow()
        st.rerun()


def main():
    """Main app entry point."""
    init_session_state()

    # Sidebar
    with st.sidebar:
        st.title("⚙️ Pipeline Status")
        st.markdown("---")

        stages = [
            ("📝 Input", 0),
            ("🎤 Transcribe", 1),
            ("🔍 Analyze", 2),
            ("✍️ Write", 3),
            ("🚀 SEO", 4),
            ("✅ Complete", 5)
        ]

        for name, stage_num in stages:
            if st.session_state.stage > stage_num:
                st.success(f"✓ {name}")
            elif st.session_state.stage == stage_num:
                st.info(f"→ {name}")
            else:
                st.text(f"  {name}")

        st.markdown("---")

        if st.session_state.stage > 0:
            if st.button("🔄 Start Over"):
                reset_workflow()
                st.rerun()

    # Main content
    if st.session_state.stage == 0:
        stage0_input()
    elif st.session_state.stage == 1:
        stage1_transcribe()
    elif st.session_state.stage == 2:
        stage2_analyze()
    elif st.session_state.stage == 3:
        stage3_write()
    elif st.session_state.stage == 4:
        stage4_seo()
    elif st.session_state.stage == 5:
        stage5_complete()


if __name__ == "__main__":
    main()
