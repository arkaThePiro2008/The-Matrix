from pathlib import Path
import streamlit as st
import dashboard

st.set_page_config(
    page_title="THE MATRIX",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def load_css() -> None:
    css_path = Path("style.css")
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def render_home() -> None:
    load_css()

    st.markdown("""
        <div class="matrix-video-wrapper">
            <video class="matrix-bg-video" autoplay loop muted playsinline>
                <source src="https://www.pexels.com/download/video/31360633/" type="video/mp4">
            </video>
        </div>
        <div class="vignette-overlay"></div>

        <div class="hero-shell">
            <h1 class="hero-title">THE MATRIX</h1>
            <p class="hero-subtitle">
                A monochrome 3D virtual town inhabited by 100 autonomous human agents.
                Observe their daily lives, conversations, and routines—or intervene as the Creator
                through Neutral, Happy, and Chaos states.
            </p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.45, 1.0, 1.45])
    with c2:
        if st.button("GET STARTED", use_container_width=True):
            st.session_state.entered_matrix = True
            st.query_params["view"] = "matrix"
            st.rerun()


def main() -> None:
    # Check if the user clicked the "⌂ HOME" button inside the 3D dashboard
    if st.query_params.get("view") == "home":
        st.session_state.entered_matrix = False
        st.query_params.clear()

    if "entered_matrix" not in st.session_state:
        st.session_state.entered_matrix = st.query_params.get("view") == "matrix"

    if st.session_state.entered_matrix:
        dashboard.render_dashboard()
    else:
        render_home()


if __name__ == "__main__":
    main()