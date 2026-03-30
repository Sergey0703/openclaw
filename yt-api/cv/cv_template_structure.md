# CV TEMPLATE STRUCTURE
# This file defines the fixed layout and formatting rules for ALL generated CVs.
# The Python docx generator must follow this exactly.

## VISUAL STYLE
- Black and white only — no colors
- Font: Calibri or Times New Roman, 11pt body, 14pt name
- Page margins: 1.5cm top/bottom, 1.8cm left/right (tight — matching original CV)
- Paragraph spacing: minimal (0-2pt between paragraphs, 4-6pt before section headings)
- No tables with borders (except education which uses invisible 2-column table)
- Sections separated by spacing, not lines

## DOCUMENT STRUCTURE (in order)

### 1. HEADER
- Full name: centered, bold, 14pt
- Address, Mobile, E-mail: centered, normal, 11pt (each on separate line or combined)
- LinkedIn URL: centered, MUST be a real clickable hyperlink (not just underlined text)
  - Use OOXML w:hyperlink element with r:id relationship pointing to the URL
  - Apply "Hyperlink" character style (blue + underlined in Word)

### 2. PERSONAL PROFILE
- Heading: "PERSONAL PROFILE" — bold, underlined, 11pt
- Content: single paragraph, 11pt
- *** ADAPT PER JOB: rewrite to match job title and key requirements ***
- Mention: years of experience, key relevant skills, location (Killarney), seeking full-time

### 3. KEY SKILLS
- Heading: "KEY SKILLS" — bold, underlined, 11pt
- Format: bullet points, each bullet has BOLD category label followed by colon, then normal text
- Example: "• Infrastructure & Servers: Windows Server, Active Directory..."
- *** ADAPT PER JOB: choose 5-7 most relevant skill categories, reorder by relevance ***
- Available categories from master profile:
  - Infrastructure & Servers
  - Cloud & Identity
  - Networking
  - Support & Operations
  - Automation & Tools
  - Languages & OS
  - AI & LLM Integration
  - RAG & Vector Systems
  - Frontend Development
  - Backend Development
  - Databases
  - eCommerce & Data
  - Leadership & Management

### 4. WORK EXPERIENCE
- Heading: "WORK EXPERIENCE" — bold, underlined, 11pt
- Each job entry format:
  - Line 1: "DATE_FROM – DATE_TO  COMPANY_NAME" — bold
  - Line 2 (indented): "Job Title" — bold
  - Then bullet points with responsibilities/achievements
- *** ADAPT PER JOB: emphasise relevant responsibilities, rewrite bullets to match job keywords ***
- Always include all jobs but adjust bullet content per target role

### 5. EDUCATION AND TRAINING
- Heading: "EDUCATION AND TRAINING" — bold, underlined, 11pt
- Format: invisible 2-column table
  - Left column: date range — bold
  - Right column: institution name (normal) + qualification (bold, separate line)
- *** ADAPT PER JOB: reorder or emphasise relevant certifications ***
- Rule: Java certs → include for software/IT roles; skip for marketing/admin roles
- Rule: QQI Level 5 → always include
- Rule: Economics degree → include for management/finance roles
- Rule: Microelectronics degree → include for technical/engineering roles

### 6. ADDITIONAL INFORMATION
- Heading: "ADDITIONAL INFORMATION" — bold, underlined, 11pt
- Format: bullet points, first word/phrase bold
- Fixed bullets (always include):
  - "Local Candidate: Residing in Killarney, available for immediate start and onsite work."
  - "Languages: English (B2), Ukrainian, Russian."
- Variable bullets (adapt per job):
  - "Automation Focus: ..." — for IT/technical roles
  - "Projects: ..." — mention AI MediaFlow and/or EnVocab if relevant
  - "Leadership: ..." — for management roles

## GOLDEN RULES (apply to every CV without exception)

### RULE 1: No page break immediately after a section heading
- A section heading must NEVER appear as the last element on a page (widow heading).
- If a heading would fall at the bottom of a page with no content following it on that page:
  - Option A: Add keep-with-next formatting so the heading moves to the next page together with its first content item.
  - Option B: Slightly reduce spacing or trim content in the preceding section to push the heading down onto the same page as its content.
- The Python docx generator must set `keep_with_next = True` on every section heading paragraph.

### RULE 2: Maximum two pages
- The entire document must fit within 2 pages. Never exceed this.
- If content is too long, apply these cuts in order:
  1. Older jobs (pre-2003): reduce to maximum 2 bullet points each
  2. KhersonOblenergo (1995-1997): reduce to 1 bullet point or remove entirely
  3. DnieperStyle (1998-1999): reduce to 1-2 bullet points
  4. Independent Tech Consultant (Aug 2025-Present): this is recent but can be condensed to 2-3 bullets if space is tight
  5. Remove VTOS education entry for programmer/developer/IT roles (see Rule 4)
  6. Shorten PERSONAL PROFILE to 2-3 sentences if needed
  7. Reduce KEY SKILLS to 5 categories maximum

### RULE 3: Work experience bullet reduction for old jobs
- Jobs older than 10 years: maximum 3 bullet points
- Jobs older than 15 years: maximum 2 bullet points
- Jobs older than 20 years (pre-2005): maximum 2 bullet points, focus on most relevant only
- Always keep the most relevant bullet to the target job, cut generic ones first

### RULE 4: Education — include/exclude by job type
- **Software Engineer / Developer / IT roles:**
  - ✅ Java certifications (eCollege) — ALWAYS include
  - ✅ University of Michigan SQL/PHP — include
  - ✅ Microelectronics degree — include
  - ✅ Economics degree — include (shows breadth)
  - ❌ VTOS QQI Level 5 — OMIT (not relevant, wastes space)
- **IT Support / Sysadmin roles:**
  - ✅ All of the above
  - ✅ VTOS QQI Level 5 ICDL/ECDL — include
- **Management / COO / Operations roles:**
  - ✅ Economics degree — ALWAYS include, put first
  - ✅ VTOS QQI Level 5 — include (Communications, Career Planning relevant)
  - ✅ Java — include
  - ❌ University of Michigan SQL/PHP — can omit
- **Marketing / eCommerce roles:**
  - ✅ Economics degree — include
  - ✅ VTOS QQI Level 5 — include
  - ❌ Java certifications — omit
  - ❌ University of Michigan SQL/PHP — omit

### RULE 5: Independent Tech Consultant section
- This is the most recent and impressive role — always include
- For non-technical roles: condense to 2 bullets focusing on project management and delivery
- For technical roles: keep 3-4 bullets with technical stack details
- Always mention AI MediaFlow by name as it shows initiative and full-stack capability

## ADAPTATION RULES FOR LLM

When generating CV for a specific job:

1. Read the job description carefully
2. Identify: job title, key required skills, company type, seniority level
3. Apply all GOLDEN RULES before finalising content
4. PERSONAL PROFILE: write 3-4 sentences that mirror job title and key requirements
5. KEY SKILLS: pick 5-7 categories most relevant, list specific technologies from job description first
6. WORK EXPERIENCE: for each job, write bullets that highlight experience matching the job
   - Use keywords from job description where truthful
   - Put most relevant experience bullets first
   - Apply bullet reduction rules for older jobs (Rule 3)
7. EDUCATION: include/exclude certifications based on Rule 4
8. ADDITIONAL INFORMATION: pick relevant variable bullets
9. Check total length — if exceeds 2 pages, apply cuts from Rule 2 in order

## OUTPUT FORMAT FOR DOCX GENERATOR

The LLM must output structured JSON that the Python docx script will render:

```json
{
  "name": "Serhii Baliasnyi",
  "contacts": ["Ballydowney, Killarney, Co Kerry", "Mobile: 0852007612", "E-mail: sergey070373@gmail.com"],
  "linkedin": "https://www.linkedin.com/in/serhii-baliasnyi-290b72246/",
  "personal_profile": "...paragraph text...",
  "key_skills": [
    {"label": "Infrastructure & Servers", "text": "Windows Server..."},
    {"label": "Cloud & Identity", "text": "Microsoft 365..."}
  ],
  "work_experience": [
    {
      "date": "Jun 2024 - Present",
      "company": "KPFA (part time)",
      "title": "System Computer Administrator",
      "bullets": ["bullet 1", "bullet 2"]
    }
  ],
  "education": [
    {
      "date": "Sep 2022 - May 2024",
      "institution": "Killarney VTOS, Ivy House, New Street, Killarney, Co Kerry",
      "qualification": "Payroll, ICDL Workforce/ECDL, Communications, Personal Effectiveness, Career Planning NFQ QQI Level 5"
    }
  ],
  "additional_info": [
    {"label": "Local Candidate", "text": "Residing in Killarney, available for immediate start and onsite work."},
    {"label": "Languages", "text": "English (B2), Ukrainian, Russian."}
  ]
}
```
