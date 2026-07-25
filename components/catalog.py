"""
Public Book Catalog Component
"""

import streamlit as st

from config import CONFIG
from models.book import Book
from services.sheets_service import GoogleSheetsService
from utils.formatters import get_status_badge, get_class_badge


def render_catalog(sheets_service: GoogleSheetsService):
    st.markdown("""
    <style>
    .book-card {
        background: white;
        border-radius: 14px;
        padding: 0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        transition: transform 0.2s, box-shadow 0.2s;
        overflow: hidden;
        height: 100%;
    }
    .book-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }
    .book-header {
        height: 100px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
    }
    .book-body {
        padding: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.spinner("Loading catalog..."):
        try:
            records = sheets_service.get_all_records(CONFIG.WORKSHEET_INVENTORY)
            books = [Book.from_row(r) for r in records]
        except Exception as e:
            st.error(f"Failed to load catalog: {str(e)}")
            return

    col1, col2, col3, col4 = st.columns([2, 1, 1, 0.8])

    with col1:
        search = st.text_input("🔍 Search", placeholder="Title, Author, or Genre...", 
                               label_visibility="collapsed")
    with col2:
        class_filter = st.selectbox("Class", ["All"] + CONFIG.CLASSES, 
                                    label_visibility="collapsed")
    with col3:
        status_filter = st.selectbox("Status", ["All"] + CONFIG.STATUS_ALL, 
                                     label_visibility="collapsed")
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("🔄", help="Refresh data", use_container_width=True)

    if refresh:
        st.cache_data.clear()
        st.rerun()

    filtered = books
    if search:
        search_lower = search.lower()
        filtered = [b for b in filtered if (
            search_lower in b.title.lower() or 
            search_lower in b.author.lower() or 
            search_lower in b.genre.lower()
        )]

    if class_filter != "All":
        filtered = [b for b in filtered if b.target_class == class_filter]

    if status_filter != "All":
        filtered = [b for b in filtered if b.status == status_filter]
    else:
        filtered = [b for b in filtered if b.status == CONFIG.STATUS_AVAILABLE]

    st.markdown(f"<p style='color: #666; font-size: 13px;'>Showing {len(filtered)} books</p>", 
                unsafe_allow_html=True)

    if not filtered:
        st.info("No books found matching your criteria.")
        return

    genre_colors = {
        "Cultural Studies": "linear-gradient(135deg, #e8f5e9, #c8e6c9)",
        "Spiritual Science": "linear-gradient(135deg, #fff3e0, #ffe0b2)",
        "Biography": "linear-gradient(135deg, #e3f2fd, #bbdefb)",
        "Value Education": "linear-gradient(135deg, #f3e5f5, #e1bee7)",
        "History": "linear-gradient(135deg, #fce4ec, #f8bbd0)",
        "Philosophy": "linear-gradient(135deg, #e0f2f1, #b2dfdb)",
    }

    cols = st.columns(3)
    for idx, book in enumerate(filtered):
        with cols[idx % 3]:
            header_color = genre_colors.get(book.genre, "linear-gradient(135deg, #f5f5f5, #e0e0e0)")

            st.markdown(f"""
            <div class="book-card">
                <div class="book-header" style="background: {header_color};">
                    📖
                </div>
                <div class="book-body">
                    <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                        {get_class_badge(book.target_class)}
                        {get_status_badge(book.status)}
                    </div>
                    <h4 style="margin:8px 0 4px 0; font-size:15px; color:#1a3a2f; font-weight:700;">
                        {book.title}
                    </h4>
                    <p style="margin:0; font-size:12px; color:#666;">by {book.author}</p>
                    <p style="margin:4px 0 0 0; font-size:11px; color:#888;">{book.genre} •</p>
                    <div style="display:flex; justify-content:space-between; align-items:center; 
                                margin-top:10px; padding-top:10px; border-top:1px solid #f0ece4;">
                        <span style="font-size:14px; font-weight:700; color:#1a3a2f;">
                            {book.formatted_cost}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if book.is_available:
                if st.button("Request Book", key=f"req_{book.book_id}", 
                           use_container_width=True, type="primary"):
                    st.session_state.selected_book = book
                    st.session_state.show_request_form = True
                    st.rerun()
            else:
                st.button("Unavailable", key=f"unav_{book.book_id}", 
                         use_container_width=True, disabled=True)
