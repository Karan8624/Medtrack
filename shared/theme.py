"""
Shared visual theme for all three MedTrack Streamlit apps (patient, nurse,
doctor) — one dark/light color system, one set of card/pill/badge styles,
so the three interfaces read as a single product instead of three
separately-styled apps.

Usage, near the top of each app.py (after st.set_page_config):

    from shared.theme import inject_theme, theme_toggle, sidebar_profile

    if "theme" not in st.session_state:
        st.session_state.theme = "dark"
    c = inject_theme(st.session_state.theme)   # returns the color dict too,
                                                # in case a page needs a raw hex
    ...
    with st.sidebar:
        ... st.radio(...) for nav ...
        theme_toggle()
        sidebar_profile(user, "Patient")
"""

import streamlit as st


def theme_colors(mode: str) -> dict:
    if mode == "dark":
        return dict(
            bg="#13131a", sidebar_bg="#191922", card_bg="#1e1e29", border="#2a2a38",
            text="#f2f1f7", muted="#9d9bae",
            accent="#8b7cf6", accent_soft="#2a2338", accent_text_on="#ffffff",
            pill_bg="#20202b", pill_border="#2e2e3d",
            red_bg="#3a1f22", red_border="#5c2b2f", red_text="#f2b8b5",
            amber_bg="#3d2f1a", amber_border="#5c4a22", amber_text="#e0b24d",
            green_bg="#1f3d2c", green_border="#2c5a40", green_text="#6fd99a",
            blue_bg="#20243d", blue_border="#30375c", blue_text="#9fb0f7",
            shadow="none",
        )
    else:
        return dict(
            bg="#f6f6fa", sidebar_bg="#fbfbfe", card_bg="#ffffff", border="#e7e5f0",
            text="#272538", muted="#817d94",
            accent="#5b4fcf", accent_soft="#efedfc", accent_text_on="#ffffff",
            pill_bg="#f3f2f9", pill_border="#e7e5f0",
            red_bg="#fdeceb", red_border="#f3c9c7", red_text="#9a372f",
            amber_bg="#fdf1dd", amber_border="#f0ddb3", amber_text="#8a5a12",
            green_bg="#e8f6ee", green_border="#c3e8d3", green_text="#1f7a49",
            blue_bg="#eef1fd", blue_border="#cdd6f7", blue_text="#3b4fae",
            shadow="0 1px 2px rgba(30, 20, 60, 0.05)",
        )


def inject_theme(mode: str) -> dict:
    c = theme_colors(mode)
    st.markdown(
        f"""
        <style>
        .stApp {{ background: {c['bg']}; color: {c['text']}; }}
        section[data-testid="stSidebar"] {{ background: {c['sidebar_bg']}; border-right: 1px solid {c['border']}; }}
        h1, h2, h3, p, span, label, div {{ color: {c['text']}; }}
        .muted {{ color: {c['muted']} !important; font-size: 0.82rem; }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {c['card_bg']};
            border: 1px solid {c['border']};
            border-radius: 14px;
            padding: 4px 6px;
            box-shadow: {c['shadow']};
        }}

        .eyebrow {{ color: {c['accent']}; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }}

        .badge {{
            display: inline-block; padding: 2px 9px; border-radius: 999px;
            font-size: 0.72rem; font-weight: 600; letter-spacing: 0.01em;
        }}
        .badge-green  {{ background: {c['green_bg']};  color: {c['green_text']}; }}
        .badge-amber  {{ background: {c['amber_bg']};  color: {c['amber_text']}; }}
        .badge-red    {{ background: {c['red_bg']};    color: {c['red_text']}; }}
        .badge-blue   {{ background: {c['blue_bg']};   color: {c['blue_text']}; }}
        .badge-accent {{ background: {c['accent_soft']}; color: {c['accent']}; }}
        .badge-neutral{{ background: transparent; color: {c['muted']}; border: 1px solid {c['border']}; }}

        .left-accent-red   {{ border-left: 3px solid {c['red_text']}; }}
        .left-accent-amber {{ border-left: 3px solid {c['amber_text']}; }}
        .left-accent-green {{ border-left: 3px solid {c['green_text']}; }}

        .sos-card {{ background: {c['red_bg']}; border: 1px solid {c['red_border']}; border-radius: 14px; padding: 14px 16px; }}
        .sos-card h4 {{ color: {c['red_text']}; margin: 0 0 4px 0; }}
        .sos-card p {{ color: {c['red_text']}; opacity: 0.85; margin: 0; font-size: 0.85rem; }}

        .stat-row {{ display: flex; gap: 28px; justify-content: flex-end; }}
        .stat-row .stat-num {{ font-size: 1.4rem; font-weight: 700; text-align: center; }}
        .stat-row .stat-label {{ font-size: 0.72rem; color: {c['muted']}; text-align: center; }}

        .stButton > button {{
            border-radius: 8px; border: 1px solid {c['border']}; background: {c['card_bg']}; color: {c['text']};
        }}
        .stButton > button:hover {{ border-color: {c['accent']}; color: {c['accent']}; }}
        div[data-testid="stProgress"] > div > div > div {{ background: {c['accent']}; }}
        div[data-testid="stToggle"] label div[data-checked="true"] {{ background: {c['accent']} !important; }}

        /* radio groups as clean pill buttons (no circles) */
        div[role="radiogroup"] {{ gap: 6px; }}
        div[role="radiogroup"] label {{
            background: {c['pill_bg']}; border: 1px solid {c['pill_border']}; border-radius: 8px;
            padding: 7px 14px; margin: 0 !important; transition: background 0.1s ease, border-color 0.1s ease;
        }}
        div[role="radiogroup"] label > div:first-child {{ display: none; }}
        div[role="radiogroup"] label:has(input:checked) {{ background: {c['accent']}; border-color: {c['accent']}; }}
        div[role="radiogroup"] label:has(input:checked) p {{ color: {c['accent_text_on']} !important; font-weight: 600; }}

        /* sidebar nav: vertical list, no circles */
        section[data-testid="stSidebar"] div[role="radiogroup"] {{ flex-direction: column; gap: 2px; }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label {{
            background: transparent; border: none; border-radius: 8px; padding: 9px 12px; width: 100%;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{ background: {c['pill_bg']}; }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
            background: {c['accent_soft']}; border-left: 3px solid {c['accent']}; padding-left: 9px;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {{
            color: {c['accent']} !important; font-weight: 600;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    return c


def theme_toggle():
    """Call inside the sidebar. Flips st.session_state.theme and reruns on change."""
    is_dark = st.session_state.theme == "dark"
    new_dark = st.toggle("Dark mode", value=is_dark)
    if new_dark != is_dark:
        st.session_state.theme = "dark" if new_dark else "light"
        st.rerun()


def sidebar_profile(user: dict, role_label: str):
    """Call inside the sidebar. Shows initials + name + role."""
    initials = "".join(part[0] for part in user["name"].split()[:2]).upper()
    st.markdown(
        f"**{initials}**  \n{user['name']}  \n<span class='muted'>{role_label}</span>",
        unsafe_allow_html=True,
    )


def with_title(name: str, title: str) -> str:
    """Avoid double-prefixing a name that already carries the title (e.g. seed name 'Dr. Brady')."""
    name = name or "—"
    return name if name.startswith(title) else f"{title} {name}"
