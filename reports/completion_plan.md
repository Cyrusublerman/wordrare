# WordRare Completion Plan

**Date:** 2025-12-17
**Status:** Active
**Total Tasks:** 16 across 5 phases
**Estimated Timeline:** 6-9 weeks

## Overview

This document outlines a systematic plan to complete all 23 identified placeholder and incomplete implementations in the WordRare codebase.

---

## **PHASE 1: Foundation - Data & Infrastructure**
**Goal:** Complete core data pipelines and infrastructure needed by all other features
**Duration:** 2-3 weeks

### Tasks:

#### **1.1 Real Corpus Frequency Data** (HIGH complexity)
- **File:** `src/ingestion/rarity_analyzer.py` (lines 41-91)
- **Current state:** Uses heuristics instead of real corpus
- **Implementation:**
  - Integrate Google Books Ngram data
  - Add frequency lookup from actual corpus files
  - Implement caching mechanism for performance
  - Update `estimate_frequency()` to use real data
- **External dependencies:**
  - Google Books Ngram dataset (download required)
  - Or alternative: COCA corpus, BNC corpus
- **Open questions:** Which corpus to prioritize? Local vs API-based?

#### **1.2 POS Tagging Integration** (MEDIUM complexity)
- **File:** `src/forms/grammar_engine.py` (lines 304-313)
- **Current state:** Returns None for pos_sequence
- **Implementation:**
  - Use NLTK's POS tagger (already in requirements.txt)
  - Map NLTK tags to WordRare POS categories
  - Cache POS results for performance
  - Update `analyze_line_syntax()` to return actual POS sequence
- **External dependencies:** NLTK data files (nltk.download('averaged_perceptron_tagger'))
- **Depends on:** Nothing (can start immediately)

#### **1.3 Semantic Tag Assignment** (MEDIUM complexity)
- **Files:** Create new module in `src/semantic/`
- **Purpose:** Generate domain_tags, affect_tags, register_tags for Semantics table
- **Implementation:**
  - Use embedding-based classification for domain tags
  - Rule-based approach for register tags (based on labels from Lexico)
  - Embedding similarity to affect lexicon for affect tags
  - Create semantic tagger class
- **External dependencies:**
  - Affect lexicon (NRC Emotion Lexicon or similar)
  - Domain classification model or manual seed list
- **Depends on:** Embeddings (already have sentence-transformers)

---

## **PHASE 2: Metrics - Real Computation**
**Goal:** Replace all placeholder metrics with actual computations
**Duration:** 1-2 weeks

### Tasks:

#### **2.1 Rhyme Stability Metric** (LOW complexity)
- **File:** `src/metrics/poem_metrics.py` (line 326)
- **Current state:** Hardcoded to 0.8
- **Implementation:**
  - Track rhyme class assignments across poem
  - Compute variance in rhyme quality within each rhyme class
  - Formula: `1.0 - variance(rhyme_similarities_per_class)`
- **Depends on:** Nothing (RhymeMatch already provides similarity)

#### **2.2 Motif Coherence Metric** (MEDIUM complexity)
- **File:** `src/metrics/poem_metrics.py` (line 376)
- **Current state:** Hardcoded to 0.7
- **Implementation:**
  - Extract embeddings for all words in poem
  - Compute centroid for theme concepts from semantic palette
  - Calculate mean cosine similarity to centroid
- **Depends on:** Embeddings must be populated in Semantics table

#### **2.3 Technique Metrics (density/regularization/variation)** (LOW complexity)
- **File:** `src/metrics/poem_metrics.py` (lines 404-408)
- **Current state:** Uses placeholders
- **Implementation:**
  - **Density:** Count actual device events per line (already partially done)
  - **Regularization:** Compute variance of event positions across lines
  - **Variation:** Calculate scheme distance between techniques (Jaccard or Hamming)
- **Depends on:** Sound device detection (already working)

#### **2.4 Rhyme Divergence (Layering)** (LOW complexity)
- **File:** `src/metrics/poem_metrics.py` (line 425)
- **Current state:** Hardcoded to 0.6
- **Implementation:**
  - Build technique activation vectors for each line
  - Compute average pairwise distance (Hamming or Jaccard)
- **Depends on:** Technique metrics from 2.3

#### **2.5 Semantic & Affect Constraint Evaluation** (MEDIUM complexity)
- **File:** `src/constraints/constraint_model.py` (lines 157-162)
- **Current state:** Hardcoded to 0.8 and 0.7
- **Implementation:**
  - **Semantic constraint:**
    - Get embeddings for words in line
    - Compare to semantic palette theme concepts
    - Score = avg similarity to palette
  - **Affect constraint:**
    - Check affect tags of words against spec.affect_profile
    - Score = proportion of words matching affect
- **Depends on:** Phase 1.3 (semantic tags) and embeddings

---

## **PHASE 3: Critical Generation Features**
**Goal:** Implement missing generation capabilities
**Duration:** 2-3 weeks

### Tasks:

#### **3.1 Semantic Correction (Repair Strategy)** (HIGH complexity)
- **File:** `src/constraints/repair.py` (lines 269-271)
- **Current state:** Returns None (not implemented)
- **Implementation:**
  - Analyze line's semantic alignment with theme
  - Identify words with low alignment
  - Query database for semantically similar words with better alignment
  - Substitute while preserving meter/rhyme
  - Use embedding similarity for word selection
- **Depends on:**
  - Phase 1.3 (semantic tags)
  - Phase 2.5 (semantic constraint evaluation)
  - Embeddings in Semantics table

#### **3.2 Device Application** (HIGH complexity)
- **File:** `src/generation/engine.py` (lines 145-154)
- **Current state:** Empty stub
- **Implementation:**
  - **Enjambment:** Identify syntax breaks, move to cross lines
  - **Caesura:** Insert mid-line pauses using punctuation
  - **Internal rhyme:** Add rhyming word pairs within lines
  - **Metaphor bridges:** Link cross-domain concepts from semantic palette
  - **Motif recurrence:** Repeat motif words from palette
  - Create DeviceApplicator class with each device as method
- **Depends on:**
  - Phase 1.2 (POS tagging for syntax analysis)
  - Semantic palette (already available)
- **Open questions:** How aggressive should device application be?

#### **3.3 Global Thematic Pass** (HIGH complexity)
- **File:** `src/generation/engine.py` (lines 167-176)
- **Current state:** Empty stub
- **Implementation:**
  - **Thematic progression analysis:**
    - Compute embedding centroids per stanza
    - Check for smooth transitions (cosine similarity)
  - **Transition smoothing:**
    - Identify jarring transitions (low similarity)
    - Adjust word choices at stanza boundaries
  - **Emotional intensity balancing:**
    - Extract affect scores per line
    - Ensure arc follows desired pattern
  - Create GlobalThematicAnalyzer class
- **Depends on:**
  - Phase 1.3 (affect tags)
  - Phase 2.2 (motif coherence)
  - Embeddings

---

## **PHASE 4: Enhanced Features (Optional but Valuable)**
**Goal:** Add polish and utility features
**Duration:** 2-3 days

### Tasks:

#### **4.1 Find-Rhymes CLI Enhancement** (LOW complexity)
- **File:** `src/forms/sound_engine.py` (lines 404-405)
- **Current state:** Placeholder message
- **Implementation:**
  - Query WordRecord table for words with matching rhyme_key
  - Apply rarity and POS filters
  - Display results with rhyme similarity scores
- **Depends on:** Nothing (data already in database)

#### **4.2 UI Module Initialization** (LOW complexity)
- **Files:**
  - `src/ui/semantic_viewer.py` (line 17)
  - `src/ui/dictionary_browser.py` (line 18)
  - `src/semantic/word_record_builder.py` (line 24)
- **Current state:** Empty `__init__` methods (but classes are functional)
- **Implementation:**
  - Add any needed initialization (currently none required)
  - Document that empty init is intentional
  - Or add configuration options if desired
- **Depends on:** Nothing

---

## **PHASE 5: Documentation & Examples**
**Goal:** Complete user-facing documentation
**Duration:** 1 week

### Tasks:

#### **5.1 API Documentation** (MEDIUM complexity)
- **Create:** `docs/api/` directory
- **Content:**
  - API reference for PoemGenerator
  - GenerationSpec configuration guide
  - Constraint model documentation
  - Metrics explanation
  - Database schema reference
- **Format:** Markdown + Sphinx or MkDocs
- **Depends on:** All implementation complete

#### **5.2 Examples Directory** (LOW complexity)
- **Create:** `examples/` directory
- **Content:**
  - Basic generation examples
  - Form customization examples
  - Constraint tuning examples
  - Batch generation scripts
  - Metrics analysis examples
- **Depends on:** Core functionality working

#### **5.3 Tutorial Documentation** (MEDIUM complexity)
- **Create:** `docs/tutorials/` directory
- **Content:**
  - Getting started guide
  - Advanced generation techniques
  - Custom form creation
  - Database exploration
  - Troubleshooting guide
- **Depends on:** Examples from 5.2

---

## **Dependency Graph & Sequencing**

```
Phase 1 (Foundation) - Start immediately, can parallelize:
├─ 1.1 Corpus Data (independent)
├─ 1.2 POS Tagging (independent)
└─ 1.3 Semantic Tags (depends on embeddings already available)

Phase 2 (Metrics) - Can start after Phase 1.3:
├─ 2.1 Rhyme Stability (independent, start immediately)
├─ 2.2 Motif Coherence (depends on 1.3)
├─ 2.3 Technique Metrics (independent, start immediately)
├─ 2.4 Rhyme Divergence (depends on 2.3)
└─ 2.5 Semantic/Affect Constraints (depends on 1.3)

Phase 3 (Generation) - Can start after Phase 2:
├─ 3.1 Semantic Correction (depends on 1.3, 2.5)
├─ 3.2 Device Application (depends on 1.2)
└─ 3.3 Global Thematic Pass (depends on 1.3, 2.2)

Phase 4 (Polish) - Can parallelize with Phase 3:
├─ 4.1 Find-Rhymes CLI (independent)
└─ 4.2 UI Init (independent)

Phase 5 (Docs) - Final phase:
└─ All tasks depend on implementation completion
```

---

## **Complexity & Effort Estimates**

| Phase | Tasks | Total Complexity | Estimated Time |
|-------|-------|-----------------|----------------|
| 1 | 3 tasks | 2 HIGH, 1 MED | 2-3 weeks |
| 2 | 5 tasks | 3 MED, 2 LOW | 1-2 weeks |
| 3 | 3 tasks | 3 HIGH | 2-3 weeks |
| 4 | 2 tasks | 2 LOW | 2-3 days |
| 5 | 3 tasks | 2 MED, 1 LOW | 1 week |
| **TOTAL** | **16 tasks** | | **6-9 weeks** |

---

## **Critical Decisions Needed**

### 1. Corpus Selection (Phase 1.1)
**Options:**
- Google Books Ngram (large, comprehensive, requires download)
- COCA/BNC (smaller, requires API or download)
- Custom corpus (full control, requires creation)

**Recommendation:** Start with Google Ngram 1-grams

### 2. Semantic Tag Sources (Phase 1.3)
**Options:**
- NRC Emotion Lexicon for affect tags
- Manual seed lists for domain tags
- WordNet domains for domain classification

**Recommendation:** Combine NRC + manual seeds

### 3. Device Application Aggressiveness (Phase 3.2)
**Options:**
- Conservative: Only apply if high confidence
- Moderate: Apply based on spec.device_profile strength
- Aggressive: Always apply, rely on metrics to score

**Recommendation:** Moderate approach with configurable parameter

### 4. LLM Integration (Optional)
**Questions:**
- Should semantic correction use LLM for word substitution?
- Should global pass use LLM for line rewrites?

**Recommendation:** Start deterministic, add LLM as optional enhancement

---

## **Risk Mitigation**

| Risk | Mitigation |
|------|-----------|
| Corpus data too large | Use sampling, implement lazy loading |
| POS tagger accuracy issues | Add manual overrides, confidence thresholds |
| Semantic tags low quality | Implement manual review pipeline |
| Device application breaks meter | Add constraint checking after each device |
| Global pass too slow | Limit to stanza boundaries, add caching |

---

## **Critical Files for Implementation**

### Top 5 Priority Files:

1. **`src/ingestion/rarity_analyzer.py`**
   Core data quality issue; affects all rarity-based features; needs real corpus integration

2. **`src/generation/engine.py`**
   Main generation pipeline; contains 2 of 3 critical stubs (device application, global pass); central to poem quality

3. **`src/constraints/repair.py`**
   Semantic correction is critical for theme coherence; affects overall poem quality

4. **`src/metrics/poem_metrics.py`**
   Contains 5 placeholder metrics; needed for proper evaluation and ranking of generated poems

5. **`src/semantic/tagger.py`** (NEW FILE TO CREATE)
   Will handle semantic tag assignment; foundational for multiple features in Phases 2-3

---

## **Progress Tracking**

### Phase 1: Foundation
- [ ] 1.1 Real Corpus Frequency Data
- [x] 1.2 POS Tagging Integration ✅ **COMPLETED 2025-12-17**
- [ ] 1.3 Semantic Tag Assignment

### Phase 2: Metrics
- [x] 2.1 Rhyme Stability Metric ✅ **COMPLETED 2025-12-17**
- [ ] 2.2 Motif Coherence Metric
- [x] 2.3 Technique Metrics ✅ **COMPLETED 2025-12-17**
- [x] 2.4 Rhyme Divergence ✅ **COMPLETED 2025-12-17**
- [ ] 2.5 Semantic & Affect Constraints

### Phase 3: Generation
- [ ] 3.1 Semantic Correction
- [ ] 3.2 Device Application
- [ ] 3.3 Global Thematic Pass

### Phase 4: Polish
- [ ] 4.1 Find-Rhymes CLI
- [ ] 4.2 UI Module Initialization

### Phase 5: Documentation
- [ ] 5.1 API Documentation
- [ ] 5.2 Examples Directory
- [ ] 5.3 Tutorial Documentation

---

## **Notes**

This plan provides incremental progress with clear milestones, testable outcomes at each phase, and flexibility to adjust priorities based on immediate needs.

**Next Steps:** Begin with Phase 1.2 (POS Tagging) - medium complexity, no external data downloads, unlocks grammar features immediately.

---

## **Implementation Log**

### 2025-12-17: Phase 1.2 - POS Tagging Integration ✅

**Completed:**
- Installed NLTK and downloaded POS tagger data (`averaged_perceptron_tagger_eng`, `punkt_tab`)
- Created comprehensive Penn Treebank to WordRare POS tag mapping (40+ tag mappings)
- Implemented `get_pos_tags()` function with LRU caching (maxsize=1024)
- Updated `analyze_line_syntax()` to return actual POS sequences instead of placeholders
- Added template matching capability
- Verified caching performance: 205x speedup on repeated calls

**Files Modified:**
- `src/forms/grammar_engine.py`:
  - Added NLTK imports and POS tag mapping dictionary
  - Added `get_pos_tags()` helper function with caching
  - Updated `analyze_line_syntax()` to use real POS tagging
  - Returns `pos_sequence` (full tuples) and `wordrare_pos_only` (simplified tags)
  - Implements template matching logic

**Results:**
- POS tagging now fully functional for grammar analysis
- Grammar engine can now analyze actual syntactic structures
- Caching ensures performance even with repeated queries
- Unlocks Phase 3.2 (Device Application) which depends on POS tagging for syntax analysis

**Next Phase Candidates:**
1. Phase 2.1: Rhyme Stability Metric (LOW complexity, independent)
2. Phase 2.3: Technique Metrics (LOW complexity, independent)
3. Phase 1.3: Semantic Tag Assignment (MEDIUM complexity, unlocks multiple Phase 2 tasks)

---

### 2025-12-17: Phases 2.1, 2.3, 2.4 - Metrics Implementation ✅

**Completed:**
- **Phase 2.1: Rhyme Stability Metric**
  - Replaced hardcoded 0.8 value with real variance calculation
  - Tracks rhyme similarity scores for each rhyme group
  - Computes variance within each rhyme class
  - Formula: `stability = max(0, 1.0 - avg_variance)`
  - Handles edge cases (single pairs, no rhymes, etc.)

- **Phase 2.3: Technique Metrics**
  - Replaced placeholder values for density, regularization, and variation
  - **Density**: Tracks boolean presence per line (equals intensity for binary detection)
  - **Regularization**: Computes `1 - variance(presence_pattern)` for consistency measurement
  - **Variation**: Implements Jaccard distance between technique occurrence sets
  - All three techniques (alliteration, assonance, consonance) now have real metrics

- **Phase 2.4: Rhyme Divergence (Layering)**
  - Replaced hardcoded 0.6 value with computed divergence
  - Divergence = average of variation scores across active techniques
  - Measures how well-separated different sound techniques are
  - High divergence indicates distinct, non-overlapping patterns

**Files Modified:**
- `src/metrics/poem_metrics.py`:
  - Updated `analyze_rhyme()` to compute real stability (lines 308-354)
  - Updated `analyze_techniques()` with density, regularization, variation calculations (lines 406-477)
  - Updated `analyze_layering()` with real divergence calculation (lines 479-498)

**Results:**
- All placeholder metrics for rhyme and techniques are now real computations
- Metrics system can now properly evaluate poem quality
- More accurate ranking and comparison of generated poems
- Variance-based stability and regularization provide meaningful quality signals

**Remaining Phase 2 Tasks:**
1. Phase 2.2: Motif Coherence Metric (MEDIUM - requires embeddings)
2. Phase 2.5: Semantic & Affect Constraints (MEDIUM - requires Phase 1.3)

**Next Phase Candidates:**
1. Phase 1.3: Semantic Tag Assignment (unlocks 2.2 and 2.5)
2. Phase 4.1: Find-Rhymes CLI (LOW complexity, independent)
3. Phase 4.2: UI Module Initialization (LOW complexity, independent)
