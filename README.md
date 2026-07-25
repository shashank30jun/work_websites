# 📚 BSGP Book Redistribution Platform

**Dev Sanskriti Vishwavidyalaya (DSVV)** — Bharatiya Sanskriti Gyaan Pariksha (BSGP)

A web application for managing book inventory, tracking donations, and distributing BSGP study materials to students of Classes 5–10.

---

## 🏗️ Architecture

This platform uses a **two-tier inventory system**:

```
┌─────────────────────────────────────────────────────────────┐
│                    MASTER CATALOG                            │
│  One row per UNIQUE book title                               │
│  Tracks: Title, Author, Genre, Class, Cost, QTY columns    │
│  Columns: Total_Qty | Available_Qty | Reserved_Qty | Dist   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STOCK LEDGER                              │
│  One row per PHYSICAL book copy                              │
│  Tracks: Copy_ID, Status, Current_Holder, Assigned_Date      │
│  Status: Available → In_Transit → Distributed                │
└─────────────────────────────────────────────────────────────┘
```

### Why Two Tiers?

| Problem (Old Design) | Solution (New Design) |
|---------------------|----------------------|
| 50 copies = 50 identical rows | 1 catalog row + 50 ledger rows |
| No quantity visibility | `Total_Qty`, `Available_Qty` columns |
| Can't track individual copy journey | Each copy has unique `Copy_ID` |
| Who has which book? Unknown | `Current_Holder` in ledger |

---

## 📊 Google Sheets Worksheets

| Worksheet | Purpose | Rows Represent |
|-----------|---------|----------------|
| **Master_Catalog** | Unique book titles with quantities | One per title |
| **Stock_Ledger** | Individual physical copies | One per copy |
| **Requests** | Student/school book requests | One per request |
| **Distribution** | Handover log | One per distribution event |
| **Volunteers** | Volunteer/teacher master list | One per person |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Google Cloud Service Account with Sheets API enabled

### 1. Clone & Setup

```bash
cd bsgp_book_platform
```

### 2. Install Dependencies

Using **uv** (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

### 3. Configure Google Sheets

1. Create a Google Sheet named **`BSGP_Book_Inventory`**
2. Share it with your service account email (from `credentials.json`)
3. Place `credentials.json` in the project root

### 4. Run the App

```bash
uv run streamlit run app.py
```

Or:
```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## 📋 Sample Data Setup

### Master_Catalog

| Catalog_ID | Title | Author | Genre | Class | Language | Cost_Per_Unit_INR | Total_Qty | Available_Qty | Reserved_Qty | Distributed_Qty | Donor_Name | Donor_Type | Notes |
|------------|-------|--------|-------|-------|----------|-------------------|-----------|---------------|----------------|-----------------|------------|------------|-------|
| CAT001 | Bharatiya Sanskriti Pravesh | Pt. Shriram Sharma Acharya | Cultural Studies | Class 8 | Hindi | 120 | 50 | 45 | 5 | 0 | AWGP | Organization | BSGP Material |
| CAT002 | Gayatri Mahavijnan | Vedmurti Taponishth | Spiritual Science | Class 6 | Hindi | 85 | 30 | 25 | 5 | 0 | Shantikunj Trust | Organization | BSGP Material |
| CAT003 | Bharat Ke Mahapurush | Dr. Pranav Pandya | Biography | Class 10 | Hindi | 150 | 40 | 35 | 5 | 0 | DSVV | Organization | BSGP Material |
| CAT004 | Sanskar Gyan | Shantikunj Prakashan | Value Education | Class 5 | Hindi | 65 | 25 | 20 | 5 | 0 | Individual Donor | Individual | BSGP Material |
| CAT005 | Itihas Ke Panna | Prof. Keshav | History | Class 9 | Hindi | 110 | 35 | 30 | 5 | 0 | AWGP Delhi | Organization | BSGP Material |

### Volunteers

| Volunteer_ID | Name | Type | Contact | Email | City | Is_Active | Books_Holding | Books_Distributed_Lifetime |
|--------------|------|------|---------|-------|------|-----------|---------------|---------------------------|
| VOL001 | Rajesh Kumar | Expert Volunteer | 9876543215 | rajesh@awgp.org | Haridwar | Yes | 0 | 45 |
| VOL002 | Sunita Devi | Volunteer | 9876543216 | sunita@awgp.org | Dehradun | Yes | 0 | 23 |
| VOL003 | Dr. Anand Sharma | Teacher | 9876543217 | anand@dsvv.ac.in | Haridwar | Yes | 0 | 67 |
| VOL004 | Priya Patel | Volunteer | 9876543218 | priya@awgp.org | Delhi | Yes | 0 | 12 |

---

## 📁 Project Structure

```
bsgp_book_platform/
├── app.py                          # Main Streamlit entry point
├── config.py                       # App config, sheet schemas, column mappings
├── pyproject.toml                  # uv project config & dependencies
├── requirements.txt                # pip fallback dependencies
├── credentials.json                # Google Cloud service account key (NOT in git)
├── README.md                       # This file
│
├── models/
│   ├── __init__.py
│   ├── master_catalog.py           # MasterCatalogItem dataclass
│   ├── stock_ledger.py           # StockLedgerItem dataclass
│   ├── book.py                    # Legacy Book model
│   └── request.py                 # BookRequest dataclass
│
├── services/
│   ├── __init__.py
│   ├── sheets_service.py          # Google Sheets API wrapper (thread-safe, rate-limited)
│   └── cache_service.py           # Thread-safe TTL cache
│
├── components/
│   ├── __init__.py
│   ├── home_dashboard.py          # Home page with metrics & insights
│   ├── catalog.py                 # Public book catalog with qty display
│   ├── request_form.py            # Book request form with validation
│   └── admin_dashboard.py         # Admin panel with approve/reject
│
├── utils/
│   ├── __init__.py
│   ├── validators.py              # Phone, email, cost validation
│   └── formatters.py              # Status badges, currency formatting
│
└── assets/
    └── style.css                  # Custom CSS styles
```

---

## 🔐 Environment Variables

Create a `.env` file (or use Streamlit secrets):

```env
# Google Cloud Service Account
GOOGLE_CREDENTIALS_PATH=credentials.json
# OR paste JSON directly (for Streamlit Cloud):
# GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}

# Admin Password
ADMIN_PASSWORD=bsgp2024

# App Config
APP_DEBUG=false
CACHE_TTL_SECONDS=30
```

---

## 🎯 Key Features

| Feature | Description |
|---------|-------------|
| **📊 Home Dashboard** | High-level metrics: total books, available, in transit, distributed, schools, students |
| **📖 Book Catalog** | Browse by title/class/genre with real-time quantity display |
| **📝 Request Form** | Students/schools request books; form data persists on validation errors |
| **📊 Admin Dashboard** | Approve/reject requests, view master catalog & stock ledger, cost analytics |
| **📦 Quantity Tracking** | Master catalog shows qty per title; stock ledger tracks individual copies |
| **👥 Volunteer Tracking** | See which volunteer/teacher holds how many books |
| **💰 Cost Analytics** | Total value, cost by class, cost by genre |

---

## 🛡️ Error Handling

| Error | Handling |
|-------|----------|
| API Rate Limit (429) | Exponential backoff, auto-retry |
| Invalid Phone | 10-digit Indian number validation |
| Qty > Available | Form validation prevents overselling |
| Connection Lost | Auto-refresh on next request |

---

## 🙏 About BSGP

**Bharatiya Sanskriti Gyaan Pariksha (BSGP)** is organized by **Dev Sanskriti Vishwavidyalaya (DSVV)**, Shantikunj, Haridwar, under the guidance of **All World Gayatri Pariwar (AWGP)**.

> *"संस्कृति रक्षणम्, चरित्र निर्माणम्"*  
> *Protecting Culture, Building Character*

---

## 📄 License

Internal use for DSVV / AWGP. All rights reserved.

---

## 🤝 Support

For issues or questions, contact the BSGP coordination team at DSVV, Shantikunj, Haridwar.
