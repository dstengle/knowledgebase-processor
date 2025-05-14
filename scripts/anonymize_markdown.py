import spacy
from typing import List, Dict, Set
import os

# Ensure the spaCy model is available
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print(
        "spaCy English model 'en_core_web_sm' not found. "
        "Please run: python -m spacy download en_core_web_sm"
    )
    exit(1)

# Define plausible fictional names for replacement
# In a real scenario, these might be more extensive or generated
FICTIONAL_PERSONS = [
    "Alex Cipher", "Blair Quantum", "Casey Nebula", "Dakota Starlight",
    "Emerson Galaxy", "Finley Comet", "Glynn Cosmos", "Harper Meteor",
    "Indigo Pulsar", "Jordan Quasar", "Kai Supernova", "Lane Astro",
    "Morgan Celestial", "Nico Orbit", "Orion Stellar", "Phoenix Nebula",
    "Quinn Galaxy", "Riley Comet", "Sage Cosmos", "Skyler Meteor"
]
FICTIONAL_ORGS = [
    "Stellar Solutions Inc.", "Quantum Leap Corp.", "Nebula Innovations Ltd.",
    "Cosmic Ventures LLC", "Galaxy Dynamics Co.", "Comet Technologies",
    "Pulsar Systems", "Quasar Industries", "Supernova Group", "Astro Enterprises",
    "Celestial Data", "Orbit Labs", "Meteor Software", "Starlight Consulting",
    "Cipher Analytics", "Quantum Mechanics Inc.", "Nebula Research", "Cosmic Coders",
    "Galaxy Software Solutions", "Comet Computing"
]

def get_entities(text: str) -> List[spacy.tokens.span.Span]:
    """Extracts PERSON and ORG entities from text using spaCy."""
    doc = nlp(text)
    entities = [ent for ent in doc.ents if ent.label_ in ["PERSON", "ORG"]]
    # Sort entities by start character to process them in order
    entities.sort(key=lambda ent: ent.start_char)
    return entities

def anonymize_content(content: str) -> str:
    """
    Identifies and replaces PERSON and ORG entities in the content
    with fictional names.
    """
    entities = get_entities(content)
    if not entities:
        return content

    # Keep track of replacements to ensure consistency within the document
    replacement_map: Dict[str, str] = {}
    person_names_used: Set[str] = set()
    org_names_used: Set[str] = set()
    
    new_content_parts = []
    current_pos = 0

    for ent in entities:
        # Add the text before the current entity
        new_content_parts.append(content[current_pos:ent.start_char])
        
        original_text = ent.text
        
        if original_text in replacement_map:
            replacement = replacement_map[original_text]
        else:
            if ent.label_ == "PERSON":
                available_names = [name for name in FICTIONAL_PERSONS if name not in person_names_used]
                if not available_names: # Fallback if we run out of unique names
                    replacement = f"Person{len(person_names_used) + 1}"
                else:
                    replacement = available_names[0]
                person_names_used.add(replacement)
            elif ent.label_ == "ORG":
                available_names = [name for name in FICTIONAL_ORGS if name not in org_names_used]
                if not available_names: # Fallback
                    replacement = f"Organization{len(org_names_used) + 1}"
                else:
                    replacement = available_names[0]
                org_names_used.add(replacement)
            else: # Should not happen based on get_entities filter
                replacement = original_text 
            
            replacement_map[original_text] = replacement
        
        new_content_parts.append(replacement)
        current_pos = ent.end_char
        
    # Add any remaining text after the last entity
    new_content_parts.append(content[current_pos:])
    
    return "".join(new_content_parts)

def process_file(filepath: str):
    """Reads, anonymizes, and overwrites a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        anonymized_content = anonymize_content(original_content)
        
        if original_content != anonymized_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(anonymized_content)
            print(f"Anonymized: {filepath}")
        else:
            print(f"No changes needed (or no entities found) for: {filepath}")
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

def main():
    files_to_process = [
        "sample_data/Coffee Ops-2024-11-07.md",
        "sample_data/daily-note-2024-11-07-Thursday.md",
        "sample_data/DORA Community Chat_2024-11-07-Thursday-12:56:10.md",
        "sample_data/DORA Community Discussion-2024-11-07.md",
        "sample_data/Michael Krohn-meetingnote-2024-11-07.md",
        "sample_data/RLS CTO Coffee-2024-11-07.md",
    ]
    
    # Ensure paths are relative to the script's execution directory if needed,
    # or use absolute paths. Assuming script is run from project root.
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    for file_path_relative in files_to_process:
        # Construct absolute path if files are relative to project root
        # If script is in /workspaces/knowledgebase-processor/scripts/
        # and files are in /workspaces/knowledgebase-processor/sample_data/
        # then file_path_relative is correct as is if script is run from project root.
        # If script is run from scripts/ then paths need adjustment.
        # For simplicity, assuming script is run from project root.
        full_path = os.path.join(project_root, file_path_relative)
        if not os.path.exists(full_path):
             # Fallback for when script is run from /workspaces/knowledgebase-processor
            full_path = file_path_relative
            if not os.path.exists(full_path):
                print(f"File not found: {file_path_relative} (tried {os.path.join(project_root, file_path_relative)} and {full_path})")
                continue
        process_file(full_path)

if __name__ == "__main__":
    main()