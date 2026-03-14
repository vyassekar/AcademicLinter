# AcademicLinter
Simple python script to flag common issues in papers
# LaTeX Academic Linter & Citation Auditor

A Python-based utility to clean up LaTeX projects. It identifies unused bibliography entries, suggests where to add them based on content matching, and flags common academic writing pitfalls.

## 🚀 Features

- **Citation Audit:** Scans `.tex` files to find references in your `.bib` files that haven't been cited.
- **Smart Suggestions:** Uses keyword density and abstract analysis to suggest specific paragraphs where unused references might fit.
- **Style Guard:** - Flags **Passive Voice** (e.g., "was analyzed").
  - Identifies **Weasel Words** (e.g., "very", "significantly").
  - Suggests alternatives for **Wordy Phrases** (e.g., "due to the fact that" → "because").
- **Drafting Hygiene:** Finds `TODO`, `XXX`, `???` markers and repeated words (e.g., "the the").
- **Privacy Check:** Alerts you if author names from your BibTeX appear in LaTeX comments (crucial for double-blind review).
- **Cross-File Support:** Works with multiple `.tex` and `.bib` files, supporting wildcards and entire directories.

## 🛠️ Installation

1. Clone this repository or download the script.
2. Install the required dependency:
   ```bash
   pip install bibtexparser
