import re
import argparse
import bibtexparser
import os
import glob
from pathlib import Path

# --- Configuration ---
STOPWORDS = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'else', 'at', 'from', 'by', 'for', 'with', 'is', 'are', 'was', 'were', 'to', 'of', 'in', 'on', 'this', 'that'}
WEASEL_WORDS = {'very', 'extremely', 'remarkably', 'quite', 'fairly', 'rather', 'surprisingly', 'significantly', 'clearly', 'obviously'}
FILLER_PHRASES = {
    'it is important to note that': 'note that',
    'it should be mentioned that': 'note that',
    'in order to': 'to',
    'due to the fact that': 'because',
    'a large number of': 'many',
    'is able to': 'can',
    'at this point in time': 'currently'
}

class AcademicLinter:
    def __init__(self, tex_files, bib_files, threshold=3):
        self.tex_files = tex_files
        self.bib_files = bib_files
        self.threshold = threshold
        self.all_entries = {}
        self.cited_keys = set()
        self.author_names = set()

    def clean_and_tokenize(self, text):
        """Removes LaTeX commands and returns a set of meaningful lowercase words."""
        text = re.sub(r'\\[\w]+(?:\{.*?\})?', '', text)
        words = re.findall(r'\w+', text.lower())
        return {w for w in words if w not in STOPWORDS and len(w) > 2}

    def load_bibs(self):
        """Parses all .bib files for keys, metadata, and privacy checking."""
        print(f"📚 Loading {len(self.bib_files)} bibliography files...")
        for bib_path in self.bib_files:
            try:
                with open(bib_path, 'r', encoding='utf-8') as f:
                    db = bibtexparser.load(f)
                    for entry in db.entries:
                        raw_content = f"{entry.get('title', '')} {entry.get('keywords', '')} {entry.get('abstract', '')}"
                        self.all_entries[entry['ID']] = {
                            'keywords': self.clean_and_tokenize(raw_content),
                            'title': entry.get('title', 'No Title'),
                            'fields': entry.keys(),
                            'source': bib_path
                        }
                        if 'author' in entry:
                            # Extract capitalized first/last names for privacy check
                            names = re.findall(r'\b[A-Z][a-z]+\b', entry['author'])
                            self.author_names.update(names)
            except Exception as e:
                print(f"❌ Error parsing {bib_path}: {e}")

    def run_audit(self):
        """Executes the full suite of checks across all provided .tex files."""
        all_tex_content = ""
        
        for tex_path in self.tex_files:
            print(f"\n{'='*60}\n🔍 AUDITING: {tex_path}\n{'='*60}")
            try:
                with open(tex_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                content = "".join(lines)
                all_tex_content += content + "\n\n"
                
                # 1. Extraction of Citations
                cites = re.findall(r'\\cite(?:p|t|alt|alp|author|year)?\*?\{([\w\s,:-]+)\}', content)
                file_cites = {k.strip() for m in cites for k in m.split(',')}
                self.cited_keys.update(file_cites)

                for i, line in enumerate(lines, 1):
                    clean_line = line.strip().lower()
                    
                    # --- 2. Privacy Check (Comments) ---
                    if line.strip().startswith('%'):
                        for name in self.author_names:
                            if len(name) > 3 and name in line:
                                print(f"   [PRIVACY] Line {i}: Author name '{name}' found in comment.")
                        continue # Don't run style checks on comments

                    # --- 3. Prose Cleanup (Duplicates & Placeholders) ---
                    dupes = re.findall(r'\b(\w+)\s+\1\b', clean_line)
                    for d in dupes: print(f"   [DUPE]    Line {i}: Repeated word '{d}'")
                    
                    marks = re.findall(r'\b(TODO|XXX|FIXME|\?\?\?)\b', line)
                    for m in marks: print(f"   [MARK]    Line {i}: Placeholder '{m}'")

                    # --- 4. Style Module ---
                    # Passive Voice (Simplified: Be-verb + past participle)
                    passive = re.findall(r'\b(?:am|is|are|was|were|be|been|being)\b\s+\w+ed\b', clean_line)
                    for p in passive: print(f"   [STYLE]   Line {i}: Passive voice? '{p}'")

                    # Weasel Words
                    for word in WEASEL_WORDS:
                        if f" {word} " in f" {clean_line} ":
                            print(f"   [STYLE]   Line {i}: Weasel word '{word}'")

                    # Wordy Phrases
                    for phrase, suggestion in FILLER_PHRASES.items():
                        if phrase in clean_line:
                            print(f"   [STYLE]   Line {i}: Wordy! Consider '{suggestion}' instead of '{phrase}'")

                # --- 5. Bib Integrity Check ---
                for key in file_cites:
                    if key not in self.all_entries:
                        print(f"   [MISSING] Key '{key}' cited but not in .bib")
                    else:
                        f_list = self.all_entries[key]['fields']
                        if 'year' not in f_list or 'author' not in f_list:
                            print(f"   [BIB!]    Entry '{key}' is missing critical fields (Year/Author).")

            except Exception as e:
                print(f"❌ Error reading {tex_path}: {e}")

        # --- 6. Suggestion Engine for Unused References ---
        unused = set(self.all_entries.keys()) - self.cited_keys
        if unused:
            print(f"\n{'='*60}\n💡 SUGGESTIONS FOR UNUSED REFERENCES ({len(unused)})\n{'='*60}")
            paragraphs = [p.strip() for p in all_tex_content.split('\n\n') if p.strip()]
            for key in sorted(unused):
                best_match = (0, None) # (score, paragraph_text)
                ref_keywords = self.all_entries[key]['keywords']
                
                for para in paragraphs:
                    score = len(ref_keywords.intersection(self.clean_and_tokenize(para)))
                    if score > best_match[0]:
                        best_match = (score, para)

                if best_match[0] >= self.threshold:
                    excerpt = best_match[1][:120].replace('\n', ' ')
                    print(f"📌 Key: {key}")
                    print(f"   Title: {self.all_entries[key]['title']}")
                    print(f"   Suggestion: High match in paragraph (Score {best_match[0]}):")
                    print(f"   \"{excerpt}...\"\n")

def expand_paths(path_list, extension):
    expanded = []
    for path in path_list:
        if '*' in path:
            expanded.extend(glob.glob(path, recursive=True))
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(extension):
                        expanded.append(os.path.join(root, file))
        elif os.path.isfile(path) and path.endswith(extension):
            expanded.append(path)
    return list(set(expanded))

def main():
    parser = argparse.ArgumentParser(description="Consolidated Academic LaTeX Linter")
    parser.add_argument('tex', nargs='+', help='Tex files, dirs, or wildcards')
    parser.add_argument('--bib', nargs='+', required=True, help='Bib files, dirs, or wildcards')
    parser.add_argument('--min', type=int, default=3, help='Min match score for suggestions')
    
    args = parser.parse_args()
    
    tex_files = expand_paths(args.tex, '.tex')
    bib_files = expand_paths(args.bib, '.bib')

    if not tex_files or not bib_files:
        print("❌ Error: Could not find .tex or .bib files. Check your paths.")
        return

    linter = AcademicLinter(tex_files, bib_files, args.min)
    linter.load_bibs()
    linter.run_audit()

if __name__ == "__main__":
    main()
