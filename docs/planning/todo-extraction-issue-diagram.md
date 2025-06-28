# Todo Extraction Issue - Visual Diagram

## Current State vs Expected State

```mermaid
graph TD
    A[Markdown File] --> B{TodoItemExtractor}
    B --> C[Regex Pattern:<br/>^-\s+\[[ xX]\]\s+.+$]
    
    D[" - [x] Task 1<br/> - [ ] Task 2"] --> C
    C --> E[❌ No Matches Found]
    
    F["- [x] Task 1<br/>- [ ] Task 2"] --> C
    C --> G[✅ 2 Matches Found]
    
    style D fill:#ffcccc
    style E fill:#ff6666
    style F fill:#ccffcc
    style G fill:#66ff66
```

## Solution Flow

```mermaid
graph LR
    A[Update Regex] --> B[Add \s* after ^]
    B --> C[New Pattern:<br/>^\s*-\s+\[[ xX]\]\s+.+$]
    C --> D[Matches todos with<br/>or without indentation]
    
    E[Test Cases] --> F[No indent<br/>Single space<br/>Multiple spaces<br/>Tabs]
    F --> G[Verify All Pass]
    
    H[Integration] --> I[Process sample file]
    I --> J[Verify RDF output<br/>contains all todos]
```

## Example Matches with New Pattern

```mermaid
graph TD
    A[Input Text] --> B[New Regex Pattern<br/>^\s*-\s+\[[ xX]\]\s+.+$]
    
    C["- [ ] No indent"] --> B
    D[" - [ ] One space"] --> B
    E["  - [x] Two spaces"] --> B
    F["    - [ ] Four spaces"] --> B
    G["	- [x] Tab indent"] --> B
    
    B --> H[All Matched ✅]
    
    style C fill:#e6f3ff
    style D fill:#e6f3ff
    style E fill:#e6f3ff
    style F fill:#e6f3ff
    style G fill:#e6f3ff
    style H fill:#66ff66
```

## Position Tracking Adjustment

```mermaid
graph TD
    A[Original Match Position] --> B[Account for Leading Whitespace]
    B --> C[Adjust start position]
    B --> D[Maintain end position]
    
    E[Example: " - [ ] Task"] --> F[match.start() = 0]
    F --> G[Actual todo start = 1]
    G --> H[Need to track whitespace offset]
```

## Implementation Timeline

```mermaid
gantt
    title Todo Extraction Fix Implementation
    dateFormat  YYYY-MM-DD
    section Planning
    Create fix plan           :done, 2024-01-01, 1d
    Get approval             :active, 2024-01-02, 1d
    section Implementation
    Update regex pattern     :2024-01-03, 1d
    Add test cases          :2024-01-03, 1d
    Fix position tracking   :2024-01-04, 1d
    section Verification
    Run unit tests          :2024-01-05, 1d
    Integration testing     :2024-01-05, 1d
    Update documentation    :2024-01-06, 1d