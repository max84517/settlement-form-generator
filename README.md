# Settlement Form Generator

A desktop application that automatically generates Word settlement contracts from Excel data.  
Built with Python 3.11+, Poetry, customtkinter (dark mode), and python-docx.

**[⬇ Download latest release (Windows .exe)](https://github.com/max84517/settlement-form-generator/releases/latest)**

---

## Quick Start (no Python required)

1. Go to [Releases](https://github.com/max84517/settlement-form-generator/releases/latest) and download `SettlementFormGenerator-v*.zip`
2. **Extract to a local folder** (avoid OneDrive / network paths — spaces in the path can cause issues)
3. Run `SettlementFormGenerator\SettlementFormGenerator.exe`
4. On first launch, create a user profile (just enter a name). All settings are saved per user in a single `config.json` — ideal for shared OneDrive folders where multiple people use the same installation.

---

## Features

- **Multi-user profiles** – on startup, select or create a user profile; each user's paths and settings are saved independently in a single `config.json`
- **Filter & preview** settlement data by Sub-Category and Status before generating
- **Chicony split** – automatically separates Chicony NB / DT into distinct contracts
- **iCertis code entry** – modal dialog collects one iCertis code per supplier before generation
- **FY/Quarter picker** – aware of HP's fiscal calendar (Q1 = Nov–Jan, Q2 = Feb–Apr, Q3 = May–Jul, Q4 = Aug–Oct)
- **Keyword replacement** – plain-text keywords anywhere in the Word template (body, text boxes, headers/footers, content controls) are replaced case-insensitively; longest keyword matched first (prevents substring collisions)
- **Table auto-fill** – platform/amount rows inserted into the contract table with a bold Total row; works even when the table is inside a Word content control (SDT)
- **Missing-fields summary** – post-generation popup lists any suppliers with empty required fields
- **Open Output Folder** button – opens the most recent timestamped output folder directly
- **Status update** – optionally writes "Contract Generated" back to the source Excel after generation
- **Supplier name normalisation** – case and spacing variants (e.g. `Liteon` / `LiteOn`) are treated as one supplier

---

## Project Structure

```
settlement-form-generator/
├── src/settlement_form/
│   ├── main.py                   # Entry point (CTk dark mode init)
│   ├── config/
│   │   └── settings.py           # Load / save config.json
│   ├── utils/
│   │   ├── fy_utils.py           # FY & quarter logic, ICMEffectiveDate
│   │   └── amount_utils.py       # Dollar amount → uppercase English words
│   ├── core/
│   │   ├── data_loader.py        # Read & filter input Excel ("Data" sheet)
│   │   ├── data_merger.py        # Join with settlement info, add ICM columns
│   │   └── contract_generator.py # Word keyword replacement & table filling
│   └── ui/
│       ├── main_window.py        # Main CTk window
│       ├── icertis_dialog.py     # Modal: iCertis code per supplier
│       ├── quarter_dialog.py     # Modal: FY/Quarter selection
│       └── widgets/
│           ├── dropdown_checklist.py  # Multi-select checkbox dropdown
│           └── data_table.py          # Scrollable table with row checkboxes
├── data/
│   ├── template/                 # Place your .docx contract template here
│   ├── settlement info/          # Place settlement info.xlsx here
│   ├── input/                    # settlement data.xlsx written here at runtime
│   └── output/                   # Generated contracts saved here (timestamped folders)
├── pyproject.toml
└── poetry.lock
```

---

## Setup (from source)

### Prerequisites

- Python 3.11 or later
- [Poetry](https://python-poetry.org/docs/#installation) 1.8+

### Install & run

```bash
git clone https://github.com/max84517/settlement-form-generator.git
cd settlement-form-generator
poetry install
poetry run python -m settlement_form.main
```

### Build executable

```bat
build_exe.bat
```

Builds to `C:\Temp\SFGen\` (avoids OneDrive path issues), then copies the result to `dist\` and creates `SettlementFormGenerator.zip` ready for release.

---

## Data Files

The `data\` folder ships with the template and settlement info already in place.  
If you need to update them:

| File | Location | Description |
|------|----------|-------------|
| Contract template | `data\template\<any name>.docx` | Word template with plain-text keywords (see below) |
| Settlement info | `data\settlement info\settlement info.xlsx` | ICM party / signatory data per supplier |

### Input Excel (selected via UI)

Must contain a sheet named **`Data`** with at least these columns:

`Platform`, `ODM`, `GBU`, `GTK Supplier`, `Sub-Category`, `Status`, `Actual Payment`  
(Other columns are ignored.)

### Settlement Info Excel

Required columns:

`Sub-Category`, `GBU`, `GTK Supplier`, `ICMPartyName1`, `ICMExternalSignatory`, `ICMExternalSignatoryTitle`, `ICMInternalSignatory`, `ICMInternalSignatoryTitle`, `ICMSRAgreementEffectiveDate`, `ICMSRAGREEMENTCODE`

---

## Word Template Keywords

Place these **plain-text** keywords anywhere in the `.docx` template.  
Matching is **case-insensitive**.

| Keyword | Filled with |
|---------|-------------|
| `ICMAgreementCode` | iCertis code entered in the dialog |
| `ICMPartyName1` | Supplier party name (from settlement info) |
| `ICMSRAgreementCode` | Settlement release agreement code |
| `ICMSRAgreementEffectiveDate` | Formatted as `MMM D, YYYY` (e.g. `Nov 1, 2025`) |
| `ICMEffectiveDate` | First day of the selected FY quarter |
| `GTK Supplier` | Supplier name |
| `Sub-Category` | Product sub-category |
| `ICMInternalSignatory` | HP signatory name |
| `ICMInternalSignatoryTitle` | HP signatory title |
| `ICMExternalSignatory` | Supplier signatory name |
| `ICMExternalSignatoryTitle` | Supplier signatory title |
| `TOTALPAYMENT` | Total payment (e.g. `$1,734.56`) |
| `CAPITALLETTERSAMOUNT` | Total in uppercase words (e.g. `ONE THOUSAND SEVEN HUNDRED THIRTY-FOUR DOLLARS AND FIFTY-SIX CENTS`) |
| `PLATFORMLIST` | Comma-separated platform list (e.g. `Pavilion, EliteBook, ProBook`) |

### Platform Table

The template must contain a table with **2 columns**.  
Row 0 is the header (preserved as-is).  
Rows 1 onward are filled with:

| Column 0 | Column 1 |
|----------|----------|
| `[Sub-Category/Platform] E&O GTK Parts` | `$amount` |
| … | … |
| **Total Settlement Payment (in USD)** (bold, right-aligned) | `$total` |

---

## Chicony Special Handling

When the supplier is **Chicony** and has rows with both NB-type and DT-type GBU values (`bNB`, `cNB`, `bDT`, `cDT`, etc.), the app automatically splits them into two separate contracts:  
`Chicony - NB` and `Chicony - DT`.

Each gets its own iCertis code entry and generates its own output file.

---

## Output

Contracts are saved to:

```
data/output/<YYYY-MM-DD HH-MM>/SETTLEMENT AND RELEASE AGREEMENT_<Supplier>_<ICMAgreementCode>.docx
```

A consolidated `settlement data.xlsx` is also written to `data/input/` after each run.

---

## HP Fiscal Year Calendar

| Quarter | Months |
|---------|--------|
| Q1 | November, December, January |
| Q2 | February, March, April |
| Q3 | May, June, July |
| Q4 | August, September, October |

FY year rule: if the current month ≥ November → FY = calendar year + 1, otherwise FY = calendar year.  
(e.g. November 2025 = FY26 Q1)
