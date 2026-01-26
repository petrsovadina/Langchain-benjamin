# Feature Specification: BioMCP PubMed Agent

**Feature Branch**: `005-biomcp-pubmed-agent`
**Created**: 2026-01-20
**Status**: Draft
**Input**: User description: "PubMed research agent using BioMCP for international biomedical literature search https://biomcp.org/"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic PubMed Article Search (Priority: P1)

Physician searches international biomedical literature for evidence-based clinical information using natural language queries in Czech.

**Why this priority**: Core MVP functionality - physicians need access to latest research evidence for clinical decision-making. PubMed/MEDLINE contains 35+ million citations and is the primary source for evidence-based medicine.

**Independent Test**: Can be fully tested by querying "Jaké jsou nejnovější studie o léčbě diabetu typu 2?" (What are the latest studies on type 2 diabetes treatment?) and verifying the agent returns relevant PubMed articles with Czech summary.

**Acceptance Scenarios**:

1. **Given** user asks research question in Czech, **When** BioMCP article_searcher is queried, **Then** system returns top 5 most relevant PubMed articles with titles, authors, publication year, and abstracts translated to Czech
2. **Given** user specifies time constraint (e.g., "studies from last 2 years"), **When** search executes, **Then** results are filtered by publication date accordingly
3. **Given** no relevant articles found, **When** search completes, **Then** system responds with "No relevant studies found for your query" in Czech with suggestion to refine search

---

### User Story 2 - Article Details and Full Text Access (Priority: P2)

Physician requests detailed information about a specific article including abstract, citation, and access to full text when available.

**Why this priority**: After finding relevant articles, physicians need complete details to evaluate study quality and access full methods/results. Essential for evidence verification.

**Independent Test**: Can be tested by requesting "Show me full details for PMID:12345678" and verifying system retrieves complete article metadata with Czech abstract summary and PubMed link.

**Acceptance Scenarios**:

1. **Given** user provides PubMed ID (PMID), **When** article_getter is called, **Then** system returns title, authors, journal, publication date, full abstract (Czech translation), DOI, and direct PubMed URL
2. **Given** article has free full text available, **When** retrieved, **Then** system includes link to PMC (PubMed Central) full text
3. **Given** article is behind paywall, **When** displayed, **Then** system indicates "Full text requires subscription" with institutional access suggestions

---

### User Story 3 - Citation Tracking and Source Verification (Priority: P3)

Physician verifies sources and tracks citations for all articles referenced in agent responses.

**Why this priority**: Enables auditability and trust - physicians must trace every claim back to primary source. Required for clinical safety but builds on basic search functionality.

**Independent Test**: Can be tested by verifying that every article mention includes inline citation [1], [2], [3] and references section with clickable PubMed URLs.

**Acceptance Scenarios**:

1. **Given** agent response references multiple articles, **When** displayed, **Then** each fact has inline citation number [N] linking to References section
2. **Given** user clicks citation number, **When** expanded, **Then** full citation shows: Authors, Title, Journal, Year, PMID, and PubMed URL
3. **Given** multiple queries in conversation, **When** citations accumulated, **Then** reference numbering continues sequentially [1], [2], ..., [N] without duplicates

---

### Edge Cases

- What happens when BioMCP service is unavailable (API timeout, network issues)?
- How does system handle queries returning 100+ articles (pagination, result limits)?
- What if Czech → English translation fails or produces ambiguous query?
- How to handle queries for very recent articles (not yet indexed in PubMed)?
- What if article abstract is in language other than English (e.g., German, French)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST translate Czech user query to English before calling BioMCP article_searcher
- **FR-002**: System MUST call BioMCP `article_searcher` tool with translated English query
- **FR-003**: System MUST retrieve article metadata: title, authors, journal, year, abstract, PMID, DOI
- **FR-004**: System MUST translate English abstracts to Czech for user display
- **FR-005**: System MUST return top 5 most relevant articles by default (configurable via Context)
- **FR-006**: System MUST format responses with LangChain Document structure including metadata source="PubMed"
- **FR-007**: System MUST include direct PubMed URLs (https://pubmed.ncbi.nlm.nih.gov/PMID/) in all responses
- **FR-008**: System MUST handle "no results found" gracefully with Czech error message
- **FR-009**: System MUST support article retrieval by PMID using `article_getter` tool
- **FR-010**: System MUST provide fallback behavior when BioMCP client fails (network error, timeout)
- **FR-011**: System MUST track all article citations with unique numbering for auditability

### Key Entities

- **PubMed Article**: Represents a biomedical research article with PMID (unique identifier), title, authors, journal name, publication date, abstract, DOI, PubMed URL, PMC ID (if free full text available)
- **Research Query**: User's natural language question in Czech, including optional filters (date range, article type, journal)
- **Citation Reference**: Links article to specific claim in response with citation number [N], full bibliographic entry, and source verification URL

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Physicians can retrieve relevant PubMed articles for clinical questions in under 5 seconds for 90% of queries
- **SC-002**: System accurately translates Czech medical queries to English with 95% semantic preservation (evaluated by bilingual medical expert)
- **SC-003**: 80% of physicians successfully find at least one relevant article on first search attempt
- **SC-004**: Every article reference includes verifiable PubMed URL, enabling 100% auditability
- **SC-005**: System handles BioMCP service failures gracefully with clear Czech error messages, maintaining physician trust

## Assumptions *(optional - document defaults)*

- BioMCP service is accessible via Python package `biomcp-python` (per CLAUDE.md installation guide)
- BioMCP `article_searcher` tool uses PubMed/MEDLINE as primary data source
- Translation pattern follows "Sandwich Pattern": Czech → English (query) → Search → English (results) → Czech (display)
- Article abstracts are in English (standard for indexed MEDLINE/PubMed articles)
- Default result limit is 5 articles (aligned with typical search result display)
- PubMed IDs (PMIDs) are stable and persistent for citation verification
- Physicians have institutional or personal access to full-text articles (system only provides links)

## Dependencies *(optional - if applicable)*

- **Feature 002-mcp-infrastructure**: Requires BioMCPClient implementation for calling BioMCP tools
- **Translation Service**: Requires Czech ↔ English translation capability (can use LLM for MVP)
- **LangGraph State Schema**: Requires extending `State` dataclass with `research_query` field
- **Feature 008-citation-system**: May integrate with centralized citation tracking (if implemented before Feature 005)

## Out of Scope *(optional - explicit boundaries)*

- Full-text article parsing and summarization (only abstracts)
- Citation network analysis (related articles, citation counts)
- Non-PubMed sources (bioRxiv, medRxiv, Europe PMC - future features)
- Personal article library management (bookmarking, collections)
- Automated critical appraisal or study quality assessment
- Direct integration with institutional library systems for full-text access
