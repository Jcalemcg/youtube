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
YOUTUBE_DARK = "#1a1a1a"
YOUTUBE_DARKER = "#0f0f0f"
YOUTUBE_LIGHT_GRAY = "#F9F9F9"
YOUTUBE_GRAY = "#909090"
ACCENT_BLUE = "#4B8FE0"
ACCENT_GREEN = "#0F9D58"
ACCENT_ORANGE = "#F08C21"

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
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}

    /* Main theme */
    .stApp {{
        background: linear-gradient(135deg, {YOUTUBE_DARKER} 0%, {YOUTUBE_DARK} 100%);
        color: #e0e0e0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}

    /* Headers - Better typography */
    h1 {{
        color: white !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
        margin-bottom: 1rem !important;
        margin-top: 1.5rem !important;
    }}

    h2 {{
        color: white !important;
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.25px !important;
        margin-bottom: 0.75rem !important;
        margin-top: 1.25rem !important;
    }}

    h3 {{
        color: #e0e0e0 !important;
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
        margin-top: 1rem !important;
    }}

    h4, h5, h6 {{
        color: #b0b0b0 !important;
        font-weight: 600 !important;
    }}

    /* Text */
    p {{
        color: #c8c8c8;
        line-height: 1.6;
    }}

    /* Links */
    a {{
        color: {ACCENT_BLUE} !important;
        text-decoration: none;
        transition: color 0.2s ease;
    }}

    a:hover {{
        color: #6fa3e8 !important;
        text-decoration: underline;
    }}

    /* Buttons - Enhanced styling */
    .stButton > button {{
        background-color: {YOUTUBE_RED};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 12px rgba(255, 0, 0, 0.25);
        cursor: pointer;
        letter-spacing: 0.5px;
    }}

    .stButton > button:hover {{
        background-color: #e60000;
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(255, 0, 0, 0.35);
    }}

    .stButton > button:active {{
        transform: translateY(0);
        box-shadow: 0 2px 8px rgba(255, 0, 0, 0.25);
    }}

    /* Primary button variant */
    .stButton > button[data-testid="baseButton-primary"] {{
        background: linear-gradient(135deg, {YOUTUBE_RED} 0%, #e60000 100%);
    }}

    /* Input fields - Enhanced styling */
    .stTextInput > div > div > input {{
        background-color: #1e1e1e;
        color: white;
        border: 2px solid #303030;
        border-radius: 6px;
        padding: 0.7rem 0.9rem !important;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        line-height: 1.5;
    }}

    .stTextInput > div > div > input:focus {{
        border-color: {ACCENT_BLUE};
        box-shadow: 0 0 0 3px rgba(75, 143, 224, 0.1);
        background-color: #252525;
    }}

    .stTextInput > div > div > input::placeholder {{
        color: #666666;
    }}

    /* Text areas - Enhanced styling */
    .stTextArea > div > div > textarea {{
        background-color: #1e1e1e;
        color: white;
        border: 2px solid #303030;
        border-radius: 6px;
        padding: 0.9rem !important;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        line-height: 1.6;
        font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
    }}

    .stTextArea > div > div > textarea:focus {{
        border-color: {ACCENT_BLUE};
        box-shadow: 0 0 0 3px rgba(75, 143, 224, 0.1);
        background-color: #252525;
    }}

    .stTextArea > div > div > textarea::placeholder {{
        color: #666666;
    }}

    /* Select inputs */
    .stSelectbox > div > div > select {{
        background-color: #1e1e1e;
        color: white;
        border: 2px solid #303030;
        border-radius: 6px;
        padding: 0.7rem 0.9rem;
        transition: all 0.3s ease;
    }}

    .stSelectbox > div > div > select:focus {{
        border-color: {ACCENT_BLUE};
        outline: none;
    }}

    /* Checkboxes and Radio buttons */
    .stCheckbox {{
        color: #c8c8c8;
    }}

    .stCheckbox > label > span {{
        font-weight: 500;
    }}

    .stRadio {{
        color: #c8c8c8;
    }}

    /* Success/Info/Warning/Error boxes - Enhanced cards */
    .stSuccess {{
        background-color: rgba(15, 157, 88, 0.15);
        border: 2px solid {ACCENT_GREEN};
        border-radius: 8px;
        padding: 1rem !important;
        color: #e0e0e0 !important;
    }}

    .stInfo {{
        background-color: rgba(75, 143, 224, 0.15);
        border: 2px solid {ACCENT_BLUE};
        border-radius: 8px;
        padding: 1rem !important;
        color: #e0e0e0 !important;
    }}

    .stWarning {{
        background-color: rgba(240, 140, 33, 0.15);
        border: 2px solid {ACCENT_ORANGE};
        border-radius: 8px;
        padding: 1rem !important;
        color: #e0e0e0 !important;
    }}

    .stError {{
        background-color: rgba(255, 0, 0, 0.15);
        border: 2px solid {YOUTUBE_RED};
        border-radius: 8px;
        padding: 1rem !important;
        color: #ff6b6b !important;
    }}

    /* Progress bar - Enhanced */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, {YOUTUBE_RED} 0%, #ff3333 100%);
        border-radius: 4px;
    }}

    .stProgress {{
        height: 6px;
    }}

    /* Sidebar - Enhanced */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(135deg, #1a1a1a 0%, #1e1e1e 100%);
        border-right: 1px solid #303030;
    }}

    section[data-testid="stSidebar"] > div > div:first-child {{
        padding-top: 2rem;
    }}

    /* Sidebar text */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: white !important;
    }}

    /* Sidebar links */
    section[data-testid="stSidebar"] a {{
        color: {ACCENT_BLUE};
    }}

    /* Expanders - Better styling */
    .streamlit-expanderHeader {{
        background-color: #252525;
        border: 1px solid #303030;
        border-radius: 6px;
        padding: 0.75rem !important;
        transition: all 0.2s ease;
    }}

    .streamlit-expanderHeader:hover {{
        background-color: #2d2d2d;
        border-color: {ACCENT_BLUE};
    }}

    .streamlit-expanderContent {{
        background-color: #1e1e1e;
        border: 1px solid #303030;
        border-top: none;
        border-radius: 0 0 6px 6px;
        padding: 1rem !important;
    }}

    /* Metric boxes - Card styling */
    .metric-card {{
        background-color: #252525;
        border: 1px solid #303030;
        border-radius: 8px;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }}

    .metric-card:hover {{
        border-color: {ACCENT_BLUE};
        box-shadow: 0 4px 12px rgba(75, 143, 224, 0.1);
    }}

    /* Divider */
    hr {{
        border: none;
        border-top: 1px solid #303030;
        margin: 1.5rem 0;
    }}

    /* Code blocks */
    .stCodeBlock {{
        background-color: #0d0d0d;
        border: 1px solid #303030;
        border-radius: 6px;
        padding: 1rem;
    }}

    pre {{
        background-color: #1a1a1a;
        border: 1px solid #303030;
        border-radius: 6px;
        padding: 1rem;
        overflow-x: auto;
    }}

    code {{
        background-color: #252525;
        color: #e0e0e0;
        padding: 0.25rem 0.5rem;
        border-radius: 3px;
        font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
        font-size: 0.85rem;
    }}

    pre code {{
        background-color: transparent;
        padding: 0;
    }}

    /* Tables */
    .dataframe {{
        background-color: #1e1e1e;
        color: #c8c8c8;
    }}

    .dataframe th {{
        background-color: #252525;
        color: white;
        border-color: #303030;
        font-weight: 600;
    }}

    .dataframe td {{
        border-color: #303030;
        color: #c8c8c8;
    }}

    /* Columns and containers */
    .stColumn {{
        padding-right: 0.5rem;
        padding-left: 0.5rem;
    }}

    /* General container styling */
    .element-container {{
        color: #c8c8c8;
        line-height: 1.6;
    }}

    /* Custom card container */
    .custom-card {{
        background-color: #252525;
        border: 1px solid #303030;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }}

    .custom-card:hover {{
        border-color: {ACCENT_BLUE};
        box-shadow: 0 4px 12px rgba(75, 143, 224, 0.1);
    }}

    /* Smooth transitions */
    * {{
        transition-property: background-color, border-color, color, box-shadow;
        transition-duration: 0.2s;
        transition-timing-function: ease;
    }}

    input, textarea, select, button {{
        transition-property: all;
        transition-duration: 0.3s;
        transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    }}
</style>
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    """Initialize session state variables."""
    if 'stage' not in st.session_state:
        st.session_state.stage = 0  # 0=input, 1=transcribe, 2=filter, 3=analyze, 4=theme, 5=write, 6=seo, 7=qa, 8=complete
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = None
    if 'transcript' not in st.session_state:
        st.session_state.transcript = None
    if 'content_filter' not in st.session_state:
        st.session_state.content_filter = None
    if 'analysis' not in st.session_state:
        st.session_state.analysis = None
    if 'theme' not in st.session_state:
        st.session_state.theme = None
    if 'article' not in st.session_state:
        st.session_state.article = None
    if 'seo' not in st.session_state:
        st.session_state.seo = None
    if 'quality_assessment' not in st.session_state:
        st.session_state.quality_assessment = None
    if 'youtube_url' not in st.session_state:
        st.session_state.youtube_url = ""


def reset_workflow():
    """Reset workflow to start."""
    st.session_state.stage = 0
    st.session_state.transcript = None
    st.session_state.content_filter = None
    st.session_state.analysis = None
    st.session_state.theme = None
    st.session_state.article = None
    st.session_state.seo = None
    st.session_state.quality_assessment = None
    st.session_state.youtube_url = ""


def show_progress():
    """Show progress indicator with enhanced styling."""
    stages = ["📝 Input", "🎤 Transcribe", "🔒 Filter", "🔍 Analyze", "🎨 Theme", "✍️ Write", "🚀 SEO", "✅ QA", "📦 Complete"]
    current_stage = st.session_state.stage

    # Create visual progress bar
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="
            background-color: #303030;
            height: 4px;
            border-radius: 2px;
            overflow: hidden;
            margin-bottom: 1.5rem;
        ">
            <div style="
                background: linear-gradient(90deg, #FF0000 0%, #ff3333 100%);
                height: 100%;
                width: {(current_stage / len(stages)) * 100}%;
                transition: width 0.5s ease;
                border-radius: 2px;
            "></div>
        </div>
        <div style="
            display: flex;
            justify-content: space-between;
            gap: 0.25rem;
            flex-wrap: wrap;
        ">
    """, unsafe_allow_html=True)

    cols = st.columns(len(stages), gap="small")
    for i, (col, stage_name) in enumerate(zip(cols, stages)):
        with col:
            if i < current_stage:
                # Completed stages - green with checkmark
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #0F9D58 0%, #089d42 100%);
                    border: 2px solid #0F9D58;
                    border-radius: 6px;
                    padding: 0.6rem 0.4rem;
                    text-align: center;
                    font-weight: 600;
                    font-size: 0.75rem;
                    color: white;
                    box-shadow: 0 2px 8px rgba(15, 157, 88, 0.3);
                ">
                    {stage_name}
                </div>
                """, unsafe_allow_html=True)
            elif i == current_stage:
                # Current stage - red with highlight
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #FF0000 0%, #ff3333 100%);
                    border: 2px solid #FF0000;
                    border-radius: 6px;
                    padding: 0.6rem 0.4rem;
                    text-align: center;
                    font-weight: 700;
                    font-size: 0.75rem;
                    color: white;
                    box-shadow: 0 2px 12px rgba(255, 0, 0, 0.4);
                    animation: pulse 2s infinite;
                ">
                    {stage_name}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Future stages - gray
                st.markdown(f"""
                <div style="
                    background-color: #303030;
                    border: 2px solid #404040;
                    border-radius: 6px;
                    padding: 0.6rem 0.4rem;
                    text-align: center;
                    font-weight: 500;
                    font-size: 0.75rem;
                    color: #808080;
                    transition: all 0.3s ease;
                ">
                    {stage_name}
                </div>
                """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Add animation keyframes
    st.markdown("""
    <style>
        @keyframes pulse {
            0%, 100% { box-shadow: 0 2px 12px rgba(255, 0, 0, 0.4); }
            50% { box-shadow: 0 4px 20px rgba(255, 0, 0, 0.6); }
        }
    </style>
    """, unsafe_allow_html=True)


def stage0_input():
    """Stage 0: YouTube URL Input"""
    st.title("🎥 YouTube to Article Converter")

    # Hero section with better styling
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(255, 0, 0, 0.1) 0%, rgba(75, 143, 224, 0.05) 100%);
        border: 1px solid rgba(75, 143, 224, 0.3);
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 2rem;
    ">
        <h2 style="color: white; margin-top: 0;">Welcome to YouTube to Article Converter</h2>
        <p style="color: #c8c8c8; font-size: 1.05rem; margin-bottom: 1.5rem;">
            Transform any YouTube video into a professional, SEO-optimized article with AI-powered processing.
        </p>
        <div style="
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
        ">
            <div style="padding: 0.75rem; background-color: rgba(255, 0, 0, 0.1); border-left: 3px solid #FF0000; border-radius: 4px;">
                <strong style="color: #FF0000;">1. Input URL</strong>
                <p style="color: #b0b0b0; font-size: 0.85rem; margin-top: 0.25rem;">📝 Paste video link</p>
            </div>
            <div style="padding: 0.75rem; background-color: rgba(75, 143, 224, 0.1); border-left: 3px solid #4B8FE0; border-radius: 4px;">
                <strong style="color: #4B8FE0;">2. Extract</strong>
                <p style="color: #b0b0b0; font-size: 0.85rem; margin-top: 0.25rem;">🎤 Get transcript</p>
            </div>
            <div style="padding: 0.75rem; background-color: rgba(15, 157, 88, 0.1); border-left: 3px solid #0F9D58; border-radius: 4px;">
                <strong style="color: #0F9D58;">3. Process</strong>
                <p style="color: #b0b0b0; font-size: 0.85rem; margin-top: 0.25rem;">✍️ Generate article</p>
            </div>
            <div style="padding: 0.75rem; background-color: rgba(240, 140, 33, 0.1); border-left: 3px solid #F08C21; border-radius: 4px;">
                <strong style="color: #F08C21;">4. Optimize</strong>
                <p style="color: #b0b0b0; font-size: 0.85rem; margin-top: 0.25rem;">🚀 SEO & export</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # URL input section
    st.markdown("<div style='margin-bottom: 1.5rem;'><h3 style='margin-top: 0;'>Get Started</h3></div>", unsafe_allow_html=True)

    youtube_url = st.text_input(
        "Enter YouTube Video URL",
        placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        value=st.session_state.youtube_url
    )

    # Example URLs in a card
    with st.expander("📌 Example Videos", expanded=False):
        st.markdown("""
        <div style="display: grid; gap: 0.5rem;">
            <div style="padding: 0.75rem; background-color: #252525; border-radius: 4px; font-family: monospace; color: #4B8FE0;">
                https://www.youtube.com/watch?v=jNQXAC9IVRw
            </div>
            <div style="padding: 0.75rem; background-color: #252525; border-radius: 4px; font-family: monospace; color: #4B8FE0;">
                https://youtu.be/dQw4w9WgXcQ
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # Action buttons and options
    col1, col2 = st.columns([3, 1], gap="medium")

    with col1:
        if st.button("🚀 Start Conversion", type="primary", use_container_width=True):
            if youtube_url:
                st.session_state.youtube_url = youtube_url
                st.session_state.stage = 1
                st.rerun()
            else:
                st.error("Please enter a YouTube URL")

    with col2:
        st.markdown("<div style='height: 2.5rem; display: flex; align-items: center;'><label style='color: #c8c8c8;'>⚙️</label></div>", unsafe_allow_html=True)
        force_whisper = st.checkbox("Force Whisper", help="Skip YouTube captions and use Whisper transcription", value=False)
        st.session_state.force_whisper = force_whisper


def stage1_transcribe():
    """Stage 1: Transcription"""
    st.title("🎤 Stage 1: Transcription")
    show_progress()

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

    # Edit Transcript
    with st.expander("✏️ Edit Transcript"):
        st.markdown("**Customize the transcript before continuing:**")

        edited_transcript = st.text_area(
            "Edit Full Transcript",
            transcript.transcript,
            height=300,
            key="edit_transcript_text"
        )

        if edited_transcript != transcript.transcript:
            if st.button("💾 Save Transcript Changes"):
                # Update the transcript in session state
                st.session_state.transcript.transcript = edited_transcript
                st.success("✓ Transcript updated!")
                st.info("The edited transcript will be used for analysis in the next stage.")
                import time
                time.sleep(1)
                st.rerun()

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


def stage2_filter():
    """Stage 2: Content Filtering & Policy Compliance"""
    st.title("🔒 Stage 2: Content Filtering & Policy Compliance")
    show_progress()

    if st.session_state.content_filter is None:
        # Create status containers
        status_container = st.empty()
        results_container = st.empty()

        try:
            status_container.info("🔍 Running content policy checks...")

            # Run content filtering
            content_filter = st.session_state.pipeline.stage1_5_filter(st.session_state.transcript)

            # Show success
            status_container.success(f"✓ Content filtering complete!")
            st.session_state.content_filter = content_filter

            import time
            time.sleep(1)
            st.rerun()

        except Exception as e:
            status_container.error(f"❌ Content filtering failed: {e}")
            logger.error(f"Content filtering error: {e}", exc_info=True)
            if st.button("← Back"):
                st.session_state.stage = 1
                st.session_state.transcript = None
                st.rerun()
            return

    # Show filtering results
    content_filter = st.session_state.content_filter

    # Overall compliance status with enhanced styling
    compliance_colors = {
        "compliant": "#0F9D58",
        "warning": "#FBBC04",
        "flagged": "#EA4335",
        "blocked": "#D32F2F"
    }
    color = compliance_colors.get(content_filter.overall_compliance, "#909090")

    col1, col2 = st.columns([2, 3], gap="medium")
    with col1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            border: 2px solid {color};
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        ">
            <h3 style="color: white; margin: 0 0 0.5rem 0;">Policy Check</h3>
            <h1 style="color: white; margin: 0.5rem 0 0 0; font-size: 2rem;">{content_filter.overall_compliance.upper()}</h1>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<h4 style='margin-top: 0;'>📊 Content Metrics</h4>", unsafe_allow_html=True)

        metric_col1, metric_col2 = st.columns(2, gap="small")
        with metric_col1:
            st.markdown(f"""
            <div style="
                background-color: #252525;
                border: 1px solid #303030;
                border-radius: 8px;
                padding: 1rem;
                text-align: center;
            ">
                <div style="color: #c8c8c8; font-size: 0.85rem; margin-bottom: 0.5rem;">Promotional</div>
                <div style="color: #FF0000; font-size: 1.5rem; font-weight: 700;">{content_filter.promotional_score:.0%}</div>
            </div>
            """, unsafe_allow_html=True)

        with metric_col2:
            st.markdown(f"""
            <div style="
                background-color: #252525;
                border: 1px solid #303030;
                border-radius: 8px;
                padding: 1rem;
                text-align: center;
            ">
                <div style="color: #c8c8c8; font-size: 0.85rem; margin-bottom: 0.5rem;">Flags</div>
                <div style="color: #4B8FE0; font-size: 1.5rem; font-weight: 700;">{len(content_filter.flags)}</div>
            </div>
            """, unsafe_allow_html=True)

    # Summary
    st.subheader("📋 Filtering Summary")
    st.write(content_filter.summary)

    st.markdown("---")

    # Sponsor and promotional info
    if content_filter.is_sponsor_content:
        st.warning("⚠️ **Sponsored Content Detected**")
        st.markdown(f"Mentions: {', '.join(content_filter.sponsor_mentions)}")
        st.info("💡 Ensure sponsor relationships are clearly disclosed in the article.")

    if content_filter.promotional_score > 0.5:
        st.warning("⚠️ **High Promotional Content**")
        st.info(f"This content appears to be {content_filter.promotional_score:.0%} promotional. Consider adjusting article tone to be more editorial.")

    # Display detected flags
    if content_filter.flags:
        st.markdown("---")
        st.subheader("🚩 Detected Issues")

        # Group by severity
        by_severity = {}
        for flag in content_filter.flags:
            if flag.severity not in by_severity:
                by_severity[flag.severity] = []
            by_severity[flag.severity].append(flag)

        # Critical issues
        if "critical" in by_severity:
            st.markdown("#### 🔴 Critical Issues")
            for flag in by_severity["critical"]:
                with st.expander(f"⚠️ {flag.category.upper()}: {flag.message}"):
                    st.markdown(f"**Text:** *{flag.text}*")
                    st.markdown(f"**Position:** {flag.position or 'N/A'}")
                    st.markdown(f"**Confidence:** {flag.confidence:.0%}")

        # High issues
        if "high" in by_severity:
            st.markdown("#### 🟠 High Priority Issues")
            for flag in by_severity["high"]:
                with st.expander(f"⚠️ {flag.category.upper()}: {flag.message}"):
                    st.markdown(f"**Text:** *{flag.text}*")
                    st.markdown(f"**Position:** {flag.position or 'N/A'}")
                    st.markdown(f"**Confidence:** {flag.confidence:.0%}")

        # Medium and low
        if "medium" in by_severity or "low" in by_severity:
            st.markdown("#### ℹ️ Other Items")
            for severity in ["medium", "low"]:
                if severity in by_severity:
                    for flag in by_severity[severity]:
                        with st.expander(f"ℹ️ {flag.category.upper()}: {flag.message}"):
                            st.markdown(f"**Text:** *{flag.text}*")
                            st.markdown(f"**Confidence:** {flag.confidence:.0%}")

    if content_filter.quality_issues:
        st.markdown("---")
        st.markdown("#### 🔍 Quality Issues")
        for issue in content_filter.quality_issues:
            st.warning(f"• {issue}")

    st.markdown("---")

    # Actions - handle based on compliance status
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("← Back"):
            st.session_state.stage = 1
            st.session_state.transcript = None
            st.session_state.content_filter = None
            st.rerun()

    # Proceed button based on compliance
    if content_filter.overall_compliance == "blocked":
        with col3:
            st.error("❌ Content is blocked. Review critical issues above. This content cannot be converted due to policy violations.")
    else:
        with col2:
            if st.button("✓ Approve & Continue →", type="primary"):
                st.session_state.stage = 3
                st.rerun()
        with col3:
            if content_filter.overall_compliance in ["flagged", "warning"]:
                with st.expander("⚠️ Override & Continue Anyway"):
                    st.warning("You are proceeding with flagged content. Ensure any necessary adjustments are made.")
                    if st.button("⚠️ Continue with Review →"):
                        st.session_state.stage = 3
                        st.rerun()


def stage3_analyze():
    """Stage 3: Content Analysis"""
    st.title("🔍 Stage 3: Content Analysis")
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
                st.session_state.stage = 2
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

    # Edit Analysis
    with st.expander("✏️ Edit Analysis"):
        st.markdown("**Customize the content analysis:**")

        col1, col2 = st.columns([1, 1])

        # Edit main topic
        with col1:
            st.markdown("##### Main Topic")
            edited_main_topic = st.text_area(
                "Edit main topic",
                analysis.main_topic,
                height=80,
                key="edit_main_topic"
            )
            if edited_main_topic != analysis.main_topic:
                st.session_state.analysis.main_topic = edited_main_topic

        # Edit subtopics
        with col2:
            st.markdown("##### Key Subtopics")
            subtopics_text = "\n".join(analysis.subtopics)
            edited_subtopics_text = st.text_area(
                "Edit subtopics (one per line)",
                subtopics_text,
                height=80,
                key="edit_subtopics"
            )
            if edited_subtopics_text != subtopics_text:
                edited_subtopics = [s.strip() for s in edited_subtopics_text.split("\n") if s.strip()]
                st.session_state.analysis.subtopics = edited_subtopics

        # Edit suggested sections
        st.markdown("##### Suggested Article Sections")
        for i, section in enumerate(analysis.suggested_sections):
            col1, col2 = st.columns([2, 1])
            with col1:
                edited_title = st.text_input(
                    f"Section {i+1} title",
                    section.title,
                    key=f"edit_section_title_{i}"
                )
                if edited_title != section.title:
                    st.session_state.analysis.suggested_sections[i].title = edited_title

            with col2:
                edited_desc = st.text_area(
                    f"Section {i+1} description",
                    section.description,
                    height=60,
                    key=f"edit_section_desc_{i}"
                )
                if edited_desc != section.description:
                    st.session_state.analysis.suggested_sections[i].description = edited_desc

        # Save changes
        if st.button("💾 Save Analysis Changes"):
            st.success("✓ Analysis updated!")
            st.info("The edited analysis will be used for article generation in the next stage.")
            import time
            time.sleep(1)
            st.rerun()

    st.markdown("---")

    # Actions
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back"):
            st.session_state.stage = 2
            st.session_state.analysis = None
            st.rerun()

    with col2:
        if st.button("✓ Approve & Select Theme →", type="primary"):
            st.session_state.stage = 4
            st.rerun()


def stage4_select_theme():
    """Stage 4: Article Theme Selection"""
    st.title("🎨 Stage 4: Select Article Theme")
    show_progress()
    st.markdown("---")

    # Show analysis summary
    st.subheader("📌 Content Summary")
    analysis = st.session_state.analysis
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Main Topic", analysis.main_topic[:40] + "...")
    with col2:
        st.metric("Suggested Sections", len(analysis.suggested_sections))

    st.markdown("---")

    st.subheader("🎨 Customize Your Article Theme")
    st.markdown("Choose how your article should be written:")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📖 Theme Style")
        theme_style = st.radio(
            "Select article style:",
            options=["professional", "casual", "news", "how-to", "opinion"],
            format_func=lambda x: {
                "professional": "👔 Professional (formal, authoritative)",
                "casual": "😊 Casual (friendly, conversational)",
                "news": "📰 News (objective, journalistic)",
                "how-to": "🔧 How-To (step-by-step, actionable)",
                "opinion": "💭 Opinion (editorial, perspective)"
            }[x],
            key="theme_style"
        )

        st.markdown("#### 👥 Target Audience")
        target_audience = st.radio(
            "Who is this for?",
            options=["expert", "beginner", "general"],
            format_func=lambda x: {
                "expert": "🧠 Experts (deep technical knowledge)",
                "beginner": "🌱 Beginners (beginner-friendly)",
                "general": "👨‍👩‍👧 General (broad audience)"
            }[x],
            key="target_audience"
        )

        st.markdown("#### 📏 Article Length")
        article_length = st.radio(
            "How long should it be?",
            options=["concise", "standard", "comprehensive"],
            format_func=lambda x: {
                "concise": "📄 Concise (quick read)",
                "standard": "📰 Standard (normal length)",
                "comprehensive": "📚 Comprehensive (in-depth)"
            }[x],
            key="article_length"
        )

    with col2:
        st.markdown("#### 💬 Tone Adjustment")
        tone_adjustment = st.radio(
            "Fine-tune the tone:",
            options=["creative", "neutral", "formal"],
            format_func=lambda x: {
                "creative": "✨ Creative (more engaging)",
                "neutral": "⚖️ Neutral (balanced)",
                "formal": "🎩 Formal (very professional)"
            }[x],
            key="tone_adjustment"
        )

        st.markdown("#### 🎬 Visual Preference")
        visual_preference = st.radio(
            "Visual elements:",
            options=["balanced", "code-heavy", "minimal"],
            format_func=lambda x: {
                "balanced": "⚖️ Balanced (tables, lists, code)",
                "code-heavy": "💻 Code-Heavy (more code examples)",
                "minimal": "📝 Minimal (mostly text)"
            }[x],
            key="visual_preference"
        )

        st.markdown("#### ✨ Additional Options")
        use_examples = st.checkbox("Include practical examples & case studies", value=True, key="use_examples")
        include_quotes = st.checkbox("Include quotes from the video", value=True, key="include_quotes")

    st.markdown("---")

    st.markdown("#### 📝 Custom Focus (Optional)")
    custom_focus = st.text_area(
        "Any specific areas to focus on or avoid?",
        placeholder="E.g., 'Focus on ROI implications' or 'Avoid technical jargon'",
        key="custom_focus"
    )

    st.markdown("---")

    # Actions
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back"):
            st.session_state.stage = 2
            st.rerun()

    with col2:
        if st.button("✓ Generate Article with Theme →", type="primary"):
            # Create ArticleTheme object
            from models.schemas import ArticleTheme
            theme = ArticleTheme(
                theme_style=st.session_state.theme_style,
                target_audience=st.session_state.target_audience,
                article_length=st.session_state.article_length,
                tone_adjustment=st.session_state.tone_adjustment,
                visual_preference=st.session_state.visual_preference,
                use_examples=st.session_state.use_examples,
                include_quotes=st.session_state.include_quotes,
                custom_focus=st.session_state.custom_focus if st.session_state.custom_focus else None
            )
            st.session_state.theme = theme
            st.session_state.stage = 4
            st.rerun()


def stage5_write():
    """Stage 5: Article Generation"""
    st.title("✍️ Stage 5: Article Generation")
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
            article = st.session_state.pipeline.stage4_write(
                st.session_state.transcript,
                st.session_state.analysis,
                st.session_state.theme
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
                st.session_state.stage = 3
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

    # Edit Article
    with st.expander("✏️ Edit Article Content"):
        st.markdown("**Customize your article:**")

        # Edit headline
        st.markdown("##### Headline")
        edited_headline = st.text_input(
            "Edit headline",
            article.headline,
            key="edit_headline"
        )
        if edited_headline != article.headline:
            st.session_state.article.headline = edited_headline

        # Edit introduction
        st.markdown("##### Introduction")
        edited_intro = st.text_area(
            "Edit introduction",
            article.introduction,
            height=120,
            key="edit_introduction"
        )
        if edited_intro != article.introduction:
            st.session_state.article.introduction = edited_intro

        # Edit sections
        st.markdown("##### Article Sections")
        for i, section in enumerate(article.sections):
            st.markdown(f"**Section {i+1}: {section.heading}**")
            edited_heading = st.text_input(
                f"Section {i+1} heading",
                section.heading,
                key=f"edit_heading_{i}"
            )
            if edited_heading != section.heading:
                st.session_state.article.sections[i].heading = edited_heading

            edited_content = st.text_area(
                f"Section {i+1} content",
                section.content,
                height=150,
                key=f"edit_content_{i}"
            )
            if edited_content != section.content:
                st.session_state.article.sections[i].content = edited_content

        # Edit conclusion
        if article.conclusion:
            st.markdown("##### Conclusion")
            edited_conclusion = st.text_area(
                "Edit conclusion",
                article.conclusion,
                height=120,
                key="edit_conclusion"
            )
            if edited_conclusion != article.conclusion:
                st.session_state.article.conclusion = edited_conclusion

        # Save changes
        if st.button("💾 Save Article Changes"):
            # Recalculate word count from updated sections
            from models.schemas import Article
            new_markdown = f"# {st.session_state.article.headline}\n\n"
            new_markdown += st.session_state.article.introduction + "\n\n"
            for section in st.session_state.article.sections:
                new_markdown += f"## {section.heading}\n\n{section.content}\n\n"
            if st.session_state.article.conclusion:
                new_markdown += f"## Conclusion\n\n{st.session_state.article.conclusion}\n\n"

            word_count = len(new_markdown.split())
            st.session_state.article.markdown = new_markdown
            st.session_state.article.word_count = word_count

            st.success("✓ Article updated!")
            st.info("The edited article will be used for SEO optimization in the next stage.")
            import time
            time.sleep(1)
            st.rerun()

    st.markdown("---")

    # Actions
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back"):
            st.session_state.stage = 3
            st.session_state.article = None
            st.rerun()

    with col2:
        if st.button("✓ Approve & Add SEO →", type="primary"):
            st.session_state.stage = 5
            st.rerun()


def stage6_seo():
    """Stage 6: SEO Optimization"""
    st.title("🚀 Stage 6: SEO Optimization")
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
                st.session_state.stage = 4
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

    # Edit SEO
    with st.expander("✏️ Edit SEO Package"):
        st.markdown("**Customize your SEO optimization:**")

        col1, col2 = st.columns([1, 1])

        # Edit meta tags
        with col1:
            st.markdown("##### Meta Tags")
            edited_meta_title = st.text_input(
                "Edit meta title",
                seo.meta_title,
                max_chars=60,
                key="edit_meta_title"
            )
            if edited_meta_title != seo.meta_title:
                st.session_state.seo.meta_title = edited_meta_title

            edited_meta_desc = st.text_area(
                "Edit meta description",
                seo.meta_description,
                height=80,
                key="edit_meta_desc"
            )
            if edited_meta_desc != seo.meta_description:
                st.session_state.seo.meta_description = edited_meta_desc

            edited_slug = st.text_input(
                "Edit URL slug",
                seo.slug,
                key="edit_slug"
            )
            if edited_slug != seo.slug:
                st.session_state.seo.slug = edited_slug

        # Edit keywords
        with col2:
            st.markdown("##### Keywords")
            edited_primary_keyword = st.text_input(
                "Edit primary keyword",
                seo.primary_keyword,
                key="edit_primary_keyword"
            )
            if edited_primary_keyword != seo.primary_keyword:
                st.session_state.seo.primary_keyword = edited_primary_keyword

            secondary_keywords_text = ", ".join(seo.secondary_keywords)
            edited_secondary_text = st.text_area(
                "Edit secondary keywords (comma-separated)",
                secondary_keywords_text,
                height=80,
                key="edit_secondary_keywords"
            )
            if edited_secondary_text != secondary_keywords_text:
                edited_secondary = [k.strip() for k in edited_secondary_text.split(",") if k.strip()]
                st.session_state.seo.secondary_keywords = edited_secondary

        # Edit social posts
        st.markdown("##### Social Media Posts")
        col1, col2 = st.columns([1, 1])

        with col1:
            edited_twitter = st.text_area(
                "Edit Twitter/X post",
                seo.social_posts.twitter,
                height=80,
                key="edit_twitter_post"
            )
            if edited_twitter != seo.social_posts.twitter:
                st.session_state.seo.social_posts.twitter = edited_twitter

        with col2:
            edited_linkedin = st.text_area(
                "Edit LinkedIn post",
                seo.social_posts.linkedin,
                height=80,
                key="edit_linkedin_post"
            )
            if edited_linkedin != seo.social_posts.linkedin:
                st.session_state.seo.social_posts.linkedin = edited_linkedin

        # Save changes
        if st.button("💾 Save SEO Changes"):
            st.success("✓ SEO package updated!")
            st.info("The edited SEO data will be included in your final output.")
            import time
            time.sleep(1)
            st.rerun()

    st.markdown("---")

    # Actions
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back"):
            st.session_state.stage = 4
            st.session_state.seo = None
            st.rerun()

    with col2:
        if st.button("✓ Assess Quality →", type="primary"):
            st.session_state.stage = 6
            st.rerun()


def stage7_quality_assessment():
    """Stage 7: Quality Assessment"""
    st.title("✅ Stage 7: Quality Assessment")
    show_progress()
    st.markdown("---")

    if st.session_state.quality_assessment is None:
        # Create status containers
        status_container = st.empty()
        preview_container = st.empty()

        try:
            status_container.info("🔍 Analyzing article quality...")

            # Run quality assessment
            qa = st.session_state.pipeline.stage5_assess_quality(
                st.session_state.article,
                st.session_state.analysis,
                st.session_state.seo
            )

            # Show success with quality rating
            status_container.success(f"✓ Quality assessment complete: {qa.quality_rating.upper()} ({qa.overall_score:.1f}/100)")

            # Show preview
            with preview_container.container():
                st.subheader("📊 Quality Overview:")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Overall Score", f"{qa.overall_score:.0f}/100")
                with col2:
                    st.metric("Content Quality", f"{qa.content_quality.average_score:.0f}/100")
                with col3:
                    st.metric("SEO Quality", f"{qa.seo_quality.average_score:.0f}/100")
                with col4:
                    st.metric("Structure", f"{qa.structure_check.passed_checks}/{qa.structure_check.total_checks}")

            st.session_state.quality_assessment = qa

            import time
            time.sleep(1.5)  # Let user see the preview
            st.rerun()

        except Exception as e:
            status_container.error(f"❌ Quality assessment failed: {e}")
            logger.error(f"Quality assessment error: {e}", exc_info=True)
            if st.button("← Back"):
                st.session_state.stage = 5
                st.rerun()
            return

    # Show quality assessment
    qa = st.session_state.quality_assessment

    st.success("✅ Quality assessment complete!")

    st.markdown("---")

    # Quality rating with color
    rating_colors = {
        "excellent": "#0F9D58",
        "good": "#4285F4",
        "fair": "#F9AB00",
        "poor": "#EA4335"
    }
    rating_color = rating_colors.get(qa.quality_rating, "#909090")

    col1, col2 = st.columns([2, 3])
    with col1:
        st.markdown(f"""
        <div style="background-color: {rating_color}; padding: 20px; border-radius: 8px; text-align: center;">
            <h1 style="color: white; margin: 0;">{qa.overall_score:.1f}</h1>
            <h3 style="color: white; margin: 5px 0 0 0;">Quality Score</h3>
            <p style="color: white; font-size: 18px; margin: 10px 0 0 0; text-transform: uppercase;">{qa.quality_rating}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### 📊 Detailed Scores")
        st.info(f"**Content Quality:** {qa.content_quality.average_score:.1f}/100")
        st.info(f"**SEO Quality:** {qa.seo_quality.average_score:.1f}/100")
        st.info(f"**Structure Check:** {qa.structure_check.passed_checks}/{qa.structure_check.total_checks} ✓")

    st.markdown("---")

    # Content Quality Breakdown
    st.subheader("📝 Content Quality Breakdown")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Readability", f"{qa.content_quality.readability_score:.0f}", help="How easy the article is to read")
        st.metric("Coherence", f"{qa.content_quality.coherence_score:.0f}", help="How well sections flow together")
    with col2:
        st.metric("Completeness", f"{qa.content_quality.completeness_score:.0f}", help="Coverage of topic")
        st.metric("Relevance", f"{qa.content_quality.relevance_score:.0f}", help="Alignment with main topic")
    with col3:
        st.metric("Uniqueness", f"{qa.content_quality.uniqueness_score:.0f}", help="Originality of content")

    st.markdown("---")

    # SEO Quality Breakdown
    st.subheader("🔍 SEO Quality Breakdown")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Keyword Optimization", f"{qa.seo_quality.keyword_optimization:.0f}")
        st.metric("Meta Tag Quality", f"{qa.seo_quality.meta_tag_quality:.0f}")
    with col2:
        st.metric("Slug Quality", f"{qa.seo_quality.slug_quality:.0f}")
        st.metric("Schema Markup", f"{qa.seo_quality.schema_markup_quality:.0f}")
    with col3:
        st.metric("Social Media", f"{qa.seo_quality.social_media_optimization:.0f}")

    st.markdown("---")

    # Structure Validation
    st.subheader("🏗️ Structure Validation")
    checks = [
        ("Headline present", qa.structure_check.has_headline),
        ("Introduction present", qa.structure_check.has_introduction),
        ("Body sections present", qa.structure_check.has_sections),
        ("Conclusion present", qa.structure_check.has_conclusion),
        ("Minimum word count (200+)", qa.structure_check.min_word_count_met),
        ("All sections have content", qa.structure_check.sections_have_content),
        ("Proper Markdown formatting", qa.structure_check.proper_formatting)
    ]

    col1, col2 = st.columns(2)
    for i, (check_name, passed) in enumerate(checks):
        col = col1 if i % 2 == 0 else col2
        with col:
            if passed:
                st.success(f"✓ {check_name}")
            else:
                st.error(f"✗ {check_name}")

    st.markdown("---")

    # Recommendations
    if qa.recommendations:
        st.subheader("💡 Improvement Recommendations")

        # Group recommendations by severity
        critical = [r for r in qa.recommendations if r.severity == "critical"]
        warning = [r for r in qa.recommendations if r.severity == "warning"]
        info = [r for r in qa.recommendations if r.severity == "info"]

        if critical:
            st.markdown("#### 🔴 Critical Issues")
            for rec in critical:
                with st.expander(f"⚠️ {rec.message}"):
                    st.markdown(f"**Category:** {rec.category}")
                    st.markdown(f"**Issue:** {rec.message}")
                    if rec.action:
                        st.markdown(f"**Recommended Action:** {rec.action}")

        if warning:
            st.markdown("#### 🟡 Warnings")
            for rec in warning:
                with st.expander(f"⚠️ {rec.message}"):
                    st.markdown(f"**Category:** {rec.category}")
                    st.markdown(f"**Issue:** {rec.message}")
                    if rec.action:
                        st.markdown(f"**Recommended Action:** {rec.action}")

        if info:
            st.markdown("#### ℹ️ Suggestions")
            for rec in info:
                with st.expander(f"💡 {rec.message}"):
                    st.markdown(f"**Category:** {rec.category}")
                    st.markdown(f"**Issue:** {rec.message}")
                    if rec.action:
                        st.markdown(f"**Recommended Action:** {rec.action}")
    else:
        st.success("🎉 No improvement recommendations - your article is excellent!")

    st.markdown("---")

    # Actions
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back"):
            st.session_state.stage = 5
            st.session_state.quality_assessment = None
            st.rerun()

    with col2:
        if st.button("✓ Download Results →", type="primary"):
            st.session_state.stage = 7
            st.rerun()


def stage8_complete():
    """Stage 8: Complete & Download"""
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
        st.metric("Quality Score", f"{st.session_state.quality_assessment.overall_score:.0f}/100" if st.session_state.quality_assessment else "N/A")

    st.markdown("---")

    # Quality summary if available
    if st.session_state.quality_assessment:
        qa = st.session_state.quality_assessment
        st.subheader("✅ Quality Assessment Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rating", qa.quality_rating.upper())
        with col2:
            st.metric("Content Quality", f"{qa.content_quality.average_score:.0f}/100")
        with col3:
            st.metric("SEO Quality", f"{qa.seo_quality.average_score:.0f}/100")
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
            "transcript": st.session_state.transcript.model_dump(),
            "quality_assessment": st.session_state.quality_assessment.model_dump() if st.session_state.quality_assessment else None
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
            ("🔒 Filter", 2),
            ("🔍 Analyze", 3),
            ("🎨 Theme", 4),
            ("✍️ Write", 5),
            ("🚀 SEO", 6),
            ("✅ QA", 7),
            ("📦 Complete", 8)
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
        stage2_filter()
    elif st.session_state.stage == 3:
        stage3_analyze()
    elif st.session_state.stage == 4:
        stage4_select_theme()
    elif st.session_state.stage == 5:
        stage5_write()
    elif st.session_state.stage == 6:
        stage6_seo()
    elif st.session_state.stage == 7:
        stage7_quality_assessment()
    elif st.session_state.stage == 8:
        stage8_complete()


if __name__ == "__main__":
    main()
