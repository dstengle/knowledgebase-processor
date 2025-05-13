# Core Use Cases and Desired Outcomes

This document outlines the primary use cases and target questions that the Knowledge Base Processor aims to address. It also details the types of derived or inferred information the system should provide to enhance knowledge discovery and utility.

## Target Questions to Answer

The system should enable users to find answers to the following types of questions:

### 1. When was my last meeting with <PERSON/ENTITY>?
*   **Desired Outcome:** The date of the most recent interaction identified or tagged as a "meeting" (or similar concept) involving the specified person or entity.
*   **Example:** "When was my last meeting with Jane Doe?" should return a specific date.

### 2. How do I know <PERSON/ENTITY>?
*   **Desired Outcome:** Contextual information about the relationship or first/key interactions with a specified person or entity, derived from notes where they are mentioned.
*   **Example:** "How do I know John Smith?" might return "Met at Conference X (see note Y)" or "Worked together on Project Z (see note A)."

### 3. What are my meeting follow-ups from my last meeting with <PERSON/ENTITY/TOPIC>?
*   **Desired Outcome:** A list of outstanding to-do items or action points explicitly linked or contextually related to the most recent meeting with a specific person, entity, or about a particular topic.
*   **Example:** "What are my follow-ups from my last meeting with Project Alpha team?" should list tasks like "Draft proposal for Phase 2" or "Schedule demo with stakeholders."

### 4. When did I meet <PERSON/ENTITY>?
*   **Desired Outcome:** The date(s) of interactions identified as a "meeting" (or similar concept) involving the specified person or entity. This could be the first meeting or all recorded meetings.
*   **Example:** "When did I meet Alice?" might return "2023-03-15" or a list of dates.

### 5. What is my list of writing ideas that haven't been completed?
*   **Desired Outcome:** A consolidated list of items identified as "writing ideas" (e.g., via tags, specific to-do syntax, or section titles) that are not marked as completed.
*   **Example:** Returns a list of blog post titles, article concepts, or book chapter ideas.

### 6. What upcoming networking tasks do I have?
*   **Desired Outcome:** A list of to-do items or scheduled reminders related to networking activities (e.g., "Follow up with <PERSON>", "Attend <EVENT>").
*   **Example:** "Follow up with Bob from Tech Meetup," "Prepare for Networking Event Y."

### 7. Do I have any follow-up meetings that need to be scheduled?
*   **Desired Outcome:** Identification of notes or to-do items that suggest a follow-up meeting is required but not yet scheduled (e.g., a to-do like "Schedule follow-up with Client X" or a note saying "Need to discuss Y further with Z").
*   **Example:** Returns "Client X: Discuss contract renewal (from meeting notes on 2024-05-10)."

## Derived or Inferred Information Needs

To support the above questions and enhance overall knowledge utility, the system should aim to derive or infer the following:

### 1. Synonyms for Titles, Tags, and Terms
*   **Description:** The system should be able to recognize, link, or suggest alternative terms, acronyms, or synonyms for key metadata elements like document titles, tags, or important terms within the content.
*   **Example:** "AI" should be relatable to "Artificial Intelligence"; "Project KBP" to "Knowledge Base Processor project."

### 2. Concept and Topic Inference for Notes
*   **Description:** Beyond explicit tags, the system should analyze note content to infer underlying concepts, topics, or themes.
*   **Example:** A note discussing "machine learning, neural networks, and data sets" could be inferred to be about the topic "Artificial Intelligence" even if not explicitly tagged.

### 3. Placeholder Link Suggestions (People, Books, Places) with Content Aggregation
*   **Description:** Identify mentions of entities (like people, books, organizations, places) that are not yet formally linked within the knowledge base and suggest creating a dedicated note or placeholder for them. Aggregated mentions of these entities should be easily viewable.
*   **Example:** If "Dr. Eva Rostova" is mentioned in multiple notes but doesn't have a dedicated page, suggest creating one and link existing mentions.

### 4. "Employee of" Relationships
*   **Description:** Infer or allow explicit definition of employment relationships between people and organizations mentioned in the notes.
*   **Example:** If "John Doe mentioned he works at Acme Corp," the system could link John Doe to Acme Corp with an "employee of" relationship.

### 5. "Organization is part of" Relationships
*   **Description:** Infer or allow explicit definition of parent/subsidiary or other structural relationships between organizations.
*   **Example:** If "Beta Inc. is a subsidiary of Alpha LLC," this relationship should be capturable.

## Future Considerations (Out of Current Scope for Initial Enhancement)

While the following data sources are valuable for a comprehensive personal knowledge base, their integration is considered a future evolution and not part of the immediate design enhancements driven by the core use cases above:

*   Processing emails
*   Processing calendar items
*   Processing web browsing history
*   Processing bookmarks

These will be considered in later phases of the system's evolution.