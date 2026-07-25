"""
Book Catalog View: Product Directory with Search & Filters
"""

import streamlit as st

from config import CONFIG
from models.master_catalog import MasterCatalogItem


def render_catalog(sheets_service):
    st.header("📖 Book Catalog")

    catalog = []
    try:
        records = sheets_service.get_all_records(
            CONFIG.WORKSHEET_MASTER_CATALOG
        )
        if records:
            catalog = [
                MasterCatalogItem.from_row(r)
                for r in records
                if isinstance(r, dict)
            ]
    except Exception as e:
        st.error(f"Failed to load catalog: {str(e)}")
        return

    if not catalog:
        st.info("No books found in the catalog.")
        return

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input(
            "🔍 Search", placeholder="Title, Author, or Genre..."
        )
    with col2:
        class_filter = st.selectbox("Class", ["All"] + CONFIG.CLASSES)
    with col3:
        status_filter = st.selectbox(
            "Stock Status", ["All", "In Stock", "Low Stock", "Out of Stock"]
        )

    filtered = catalog
    if search:
        s = search.lower()
        filtered = [
            c
            for c in filtered
            if s in c.title.lower()
            or s in c.author.lower()
            or s in c.genre.lower()
        ]
    if class_filter != "All":
        filtered = [c for c in filtered if c.target_class == class_filter]
    if status_filter != "All":
        filtered = [c for c in filtered if c.stock_status == status_filter]

    st.caption(f"Showing {len(filtered)} titles")

    for i in range(0, len(filtered), 3):
        cols = st.columns(3)
        for j in range(3):
            idx = i + j
            if idx >= len(filtered):
                break
            item = filtered[idx]
            with cols[j]:
                with st.container(border=True):
                    st.write(f"**{item.title}**")
                    st.caption(f"by {item.author}")
                    st.write(f"📚 {item.target_class} • {item.formatted_cost}")

                    if item.is_in_stock:
                        if st.button(
                            "Request Book",
                            key=f"req_{item.catalog_id}",
                            type="primary",
                        ):
                            st.session_state.selected_book = item
                            st.session_state.show_request_form = True
                            st.rerun()
                    else:
                        st.button(
                            "Out of Stock",
                            key=f"out_{item.catalog_id}",
                            disabled=True,
                        )
