# Rare Poem System - Implementation Plan

## Overview
This plan outlines the step-by-step implementation of a procedurally generated poetry system using rare words enriched with phonetic, semantic, and poetic-structure metadata.

## Phase 1: Foundation & Data Pipeline (Tasks 1-5)
- **Task 1:** Set up project structure and core infrastructure
- **Task 2:** Implement Data Ingestion Layer (A) - Phrontistery Scraper (A1)
- **Task 3:** Implement External Dictionary Enrichment (A2)
- **Task 4:** Implement Phonetics & IPA processing (A3)
- **Task 5:** Implement Frequency & Rarity analysis (A4)

## Phase 2: Semantic Intelligence (Tasks 6-10)
- **Task 6:** Implement Semantic Layer (B) - Lexical Structure (B1)
- **Task 7:** Implement Embeddings system (B2)
- **Task 8:** Implement Tagging system (B3) - rule-based and embedding-based
- **Task 9:** Build Concept Graph (B4) with clustering and relationship edges
- **Task 10:** Define and implement final WORD_RECORD schema (B5)

## Phase 3: Poetic Form Engines (Tasks 11-14)
- **Task 11:** Implement Poetic Form Engine (C) - Form Library (C1)
- **Task 12:** Build Sound Engine (C2) for rhyme, alliteration, assonance
- **Task 13:** Build Meter Engine (C3) for validation and repair
- **Task 14:** Build Grammar Engine (C4) with syntactic templates

## Phase 4: Generation Pipeline (Tasks 15-19)
- **Task 15:** Implement Generation Engine (D) - Input Spec and Theme Selection (D1-D2)
- **Task 16:** Implement Stanza & Line Scaffolding (D3)
- **Task 17:** Implement Line Realisation (D4) with word selection and meter adjustment
- **Task 18:** Implement Device Application (D5) for motif recurrence and poetic devices
- **Task 19:** Implement Global Pass (D6) for thematic smoothing

## Phase 5: Quality Control (Tasks 20-22)
- **Task 20:** Implement Constraint Model and Steering Framework (Section 3)
- **Task 21:** Implement Conflict Detection and Repair Strategies (Section 3.2-3.3)
- **Task 22:** Implement Ranking Metrics system (Section 4) - Meter, Rhyme, Semantic variables

## Phase 6: Tooling & Interface (Tasks 23-26)
- **Task 23:** Build Tooling/UI (E) - Dictionary Browser (E1)
- **Task 24:** Build Semantic Map Viewer (E2)
- **Task 25:** Build Form Debugger (E3)
- **Task 26:** Build Parameter Panel (E4) for generation controls

## Phase 7: Integration (Tasks 27-28)
- **Task 27:** Set up all databases (rare_lexicon, lexico, phonetics, freq_profile, semantics, concept_graph, poetic_forms, generation_runs)
- **Task 28:** Integration testing and end-to-end poem generation validation

## Key Technical Considerations

### Data Sources Priority

**Tier 1 (Required):**
- Phrontistery wordlist (scraped)
- CMU Pronouncing Dictionary
- Google Books Ngram
- Embedding model (sentence-transformers)
- Hand-authored ontology

**Tier 2 (Recommended):**
- Wordnik API
- Wiktionary
- WordNet

**Tier 3 (Optional):**
- ConceptNet
- Premium dictionary APIs

### Critical Integration Points
1. **WORD_RECORD** is the central data structure unifying all layers
2. **Concept Graph** bridges semantic understanding and generation
3. **Constraint model** orchestrates quality vs. creativity tradeoffs

### Architecture Highlights
- Deterministic engines for rhyme/meter validation
- LLM usage constrained to bounded paraphrase/synonym tasks
- Iterative repair loop with scored constraints and policy-driven relaxation

## Progress Tracking

### Completed Phases
- [ ] Phase 1: Foundation & Data Pipeline
- [ ] Phase 2: Semantic Intelligence
- [ ] Phase 3: Poetic Form Engines
- [ ] Phase 4: Generation Pipeline
- [ ] Phase 5: Quality Control
- [ ] Phase 6: Tooling & Interface
- [ ] Phase 7: Integration

### Phase Reports
Phase reports will be added to `/reports/` directory as each phase completes.
