# Document Converter Suite

**Python-based document processing and spreadsheet conversion utilities**

**Developed & Maintained by CSS Development Team**

## Overview

Document Converter Suite is a collection of desktop-oriented tools designed to reduce manual document handling, extract structured information from business documents, validate extracted records, and prepare Excel outputs for operational workflows.

Each converter is maintained as a separate application within the repository. Its extraction rules and output format are tailored to its source documents; the converters should not be assumed to share interchangeable input templates.

## Applications

| Application | Purpose | Main capabilities |
| --- | --- | --- |
| **Delivery Note Converter** | Convert delivery-note PDFs into structured Excel records. | Extract delivery numbers, packing-list details and carton rows; validate totals; consolidate results from multiple PDFs. |
| **Pioneer Converter** | Process packing-list PDFs with invoice, lot, package and carton information. | Read relevant packing-list sections, handle rotated pages, apply document-specific extraction boundaries, filter records and export Excel. |
| **Hayleys Excel Converter** | Process supported Hayleys-format spreadsheet documents. | Extract and transform item-based records using format-specific parsing rules, including carrying an item code forward until the next item-code entry. |

### Delivery Note Converter

- Extracts delivery numbers and packing-list information from supported PDF layouts.
- Preserves leading zeros in delivery numbers when exporting to Excel by treating them as text.
- Extracts carton-level rows and checks calculated quantities and totals against the source document.
- Supports selecting multiple PDFs and consolidating their validated records into one Excel output.
- Exports all validated records from the selected documents, independently of temporary UI filtering.

### Pioneer Converter

- Processes supported packing-list PDFs, including rotated pages.
- Extracts invoice/ME references, LOT values, package information and carton rows according to the supported document layout.
- Applies extraction boundaries based on the first relevant invoice/LOT heading and the last package section.
- Supports filtering by invoice, LOT, package and carton information.
- Highlights the header row in the generated spreadsheet rather than applying header styling to all data rows.
- Reports a failure reason for files that cannot be processed.

### Hayleys Excel Converter

- Processes supported spreadsheet layouts using document-specific extraction and transformation logic.
- Retains the active item code for subsequent rows until a new item code is encountered.
- Provides a desktop user interface with System, Light and Dark appearance options.
- Supports structured output for downstream spreadsheet workflows.

> **Format compatibility:** Extraction behavior is designed for specific source layouts. New or revised supplier templates should be tested before operational use. The application descriptions above summarize established workflows; supported file variants and exact run commands should be checked against each converter's source and documentation.

## Repository Organization

```text
Document-Converter-Suite/
├── delivery-note-converter/
├── pioneer-converter/
├── hayleys-excel-converter/
├── .gitignore
└── README.md
```

Each application should keep its own source files, dependencies, configuration examples, tests, and application-specific README where applicable.

## Technology

- **Language:** Python
- **Document processing:** PDF and Excel parsing libraries, depending on the application
- **Desktop interface:** Python desktop UI components, depending on the application
- **Output:** Microsoft Excel-compatible workbooks
- **Version control:** Git and GitHub

Library versions, Python version requirements and packaging procedures are application-specific; consult each converter's dependency files and build configuration.

## Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/CSS-DEV-TEM/Document-Converter-Suite.git
   cd Document-Converter-Suite
   ```

2. Enter the folder of the converter you want to use.
3. Create and activate a Python virtual environment, if running from source:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. If the application includes a `requirements.txt` file, install its dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Run the application's documented entry point. Entry-point names and build commands may differ between converters.

**Windows note:** Desktop installers or packaged executables, where provided, may have a different installation procedure from the source workflow.

## Quality and Validation

Before releasing changes:

- Verify extraction against representative, approved test documents.
- Compare extracted row counts, key identifiers and numeric totals with source documents.
- Test multi-file processing and ensure UI filters do not accidentally limit exported records.
- Confirm leading-zero identifiers remain intact in Excel.
- Test invalid or unsupported documents and ensure failures are explained without silently producing incorrect data.
- Check the generated workbook's headings, data types and formatting.

## Security and Data Handling

These tools may process operational or customer documents. Follow the organization's data-handling policies:

- Do not commit customer PDFs, invoices, packing lists, exported spreadsheets, credentials or other confidential material.
- Use sanitized test fixtures where documentation or automated tests require examples.
- Keep local environments, build artifacts and generated files out of version control using `.gitignore`.
- Review repository visibility and access permissions before sharing source code or sample data.
- Review all staged files before pushing: `git diff --cached --name-only`.

## Development Workflow

Make application-specific changes in the relevant converter directory. Use descriptive commits and review changes before merging into the shared default branch. Follow any branch protection or pull-request policies configured for the repository.

## Maintenance

**Developed & Maintained by CSS Development Team**

This repository contains separate document-conversion utilities maintained under a shared codebase. Features and compatibility may vary by converter and release.
