# Rare Poem System – Build Canvas

## 0. Overview

* Goal: Procedurally generate poems using a rare-word dictionary enriched with phonetic, semantic, and poetic-structure metadata.
* Core idea: One unified WORD_RECORD powering:

  * rarity-based selection
  * semantic/thematic coherence
  * meter/rhyme/sound devices

---

## 1. System Build Structure

### 1.1 Data Ingestion Layer (A)

* **A1. Phrontistery Scraper**

  * Extract: `word`, `phrontistery_definition`, `source_url`.
* **A2. External Dictionary Enrichment**

  * Query APIs to get: `definitions`, `examples`, `labels_raw`, `etymology_raw`, `pos_raw`, `phonetics_raw`.
* **A3. Phonetics & IPA**

  * Use CMU-based tools + dictionary phonetics to get: `ipa_us_cmu`, `ipa_dict`, `stress_pattern`, `syllable_count`.
* **A4. Frequency & Rarity**

  * Collect corpus counts → `freq_written`, `freq_spoken`, `freq_historical`, `dispersion_index`.
  * Compute `rarity_score` and `temporal_profile`.

### 1.2 Semantic Layer (B)

* **B1. Lexical Structure**

  * Parse lexicographic data into: `sense_list`, `usage_notes`, `labels_norm`.
  * Optional WordNet-style: `synonyms`, `antonyms`, `hypernyms`, `hyponyms`.
* **B2. Embeddings**

  * Build `semantic_text` (definition + examples + labels).
  * Encode → `embedding` vector per lemma/phrase.
* **B3. Tagging**

  * RULE_TAGGER: derive `domain_tags`, `register_tags` from labels/keywords.
  * EMBEDDING_TAGGER: derive `affect_tags`, `imagery_tags`, `theme_tags` using seed sets + similarity.
* **B4. Concept Graph**

  * Cluster embeddings within ontology slices → `CONCEPT_NODE`s.
  * Edges:

    * `ASSOCIATES_WITH` (high similarity/co-occurrence)
    * `CONTRASTS_WITH` (hand-authored oppositions)
    * `METAPHOR_BRIDGE` (cross-domain pairs).
* **B5. Final WORD_RECORD Schema**

  * `{lemma, pos_primary, pos_all[], ipa_*, stress_pattern, syllable_count,
     rarity_score, temporal_profile, domain_tags[], register_tags[],
     affect_tags[], imagery_tags[], embedding, concept_links[]}`.

### 1.3 Poetic Form Engine (C)

* **C1. Form Library**

  * JSON specs for forms: sonnet, villanelle, haiku, tanka, limerick, blank verse, free verse, etc.
  * Fields: stanza count, lines per stanza, rhyme pattern, meter pattern, special rules (volta, refrains).
* **C2. Sound Engine**

  * Derive rhyme classes from IPA (final stressed syllable + coda).
  * Alliteration/assonance/consonance checks from onset/nucleus/coda.
* **C3. Meter Engine**

  * Validate/repair lines against target foot pattern (iambic, trochaic, anapestic, etc.).
* **C4. Grammar Engine**

  * Simple syntactic templates (NP/VP/PP/clause patterns).
  * LINE patterns as ordered POS roles.

### 1.4 Generation Engine (D)

* **D1. Input Spec**

  * `{form, theme, affect_profile, rarity_bias, device_profile, cross_domain, motif_density}`.
* **D2. Theme & Motif Selection**

  * Query Concept Graph for CONCEPT_NODEs matching theme + affect.
  * Pick 1–3 MOTIF_NODEs (clustered imagery/lexical sets).
* **D3. Stanza & Line Scaffolding**

  * Build stanza/line scaffolds from Form Library (rhyme/meter slots + syntactic templates).
* **D4. Line Realisation**

  * For each line:

    * Determine target rhyme, meter, syntactic pattern.
    * Query WORD_RECORDs with filters: POS, tags, rarity range, rhyme/sound, concept proximity.
    * Assemble candidate line then meter-adjust.
* **D5. Device Application**

  * Enforce motif recurrence, enjambment, caesura, internal rhyme, metaphor bridges.
* **D6. Global Pass**

  * Smooth thematic progression, contrasts, and intensity over stanzas.

### 1.5 Tooling / UI (E)

* **E1. Dictionary Browser** – inspect individual WORD_RECORDs.
* **E2. Semantic Map Viewer** – graph of concepts, domains, metaphor bridges.
* **E3. Form Debugger** – meter, rhyme, semantic tags per line.
* **E4. Parameter Panel** – sliders and toggles for generation controls.

---

## 2. Databases & Sources

### 2.1 Rare-Word Base (Phrontistery & Friends)

* **Target DB:** `rare_lexicon`
* **Fields:** `lemma`, `phrontistery_definition`, `source_url`, `phrontistery_list_id`.
* **Sources (required):**

  * Phrontistery International House of Logorrhea (scraped A–Z pages).
* **Sources (optional/augment):**

  * Other curated rare-word lists (e.g. specialty glossaries, archaic word lists).

### 2.2 Lexicographic DB

* **Target DB:** `lexico`
* **Fields:** `lemma`, `definitions[]`, `examples[]`, `labels_raw[]`, `etymology_raw`, `pos_raw[]`.
* **Sources (primary candidates):**

  * Free/Oss dictionary API (definitions + examples + phonetics + POS).
  * Wordnik API (good rare-word coverage).
  * Wiktionary (API or dump) for obscure/archaic entries.
* **Sources (premium/optional):**

  * Oxford/MW/Collins APIs for higher-quality sense/usage labels.

### 2.3 Phonetics & IPA DB

* **Target DB:** `phonetics`
* **Fields:** `lemma`, `ipa_us_cmu`, `ipa_dict_uk`, `ipa_dict_us`, `stress_pattern`, `syllable_count`, `rhyme_key`.
* **Sources (required):**

  * English-to-IPA / CMU Pronouncing Dictionary.
* **Sources (optional):**

  * IPA/phonetics from lexical APIs (UK/US variants).

### 2.4 Frequency & Rarity DB

* **Target DB:** `freq_profile`
* **Fields:** `lemma`, `freq_written`, `freq_spoken`, `freq_historical[]`, `dispersion_index`, `rarity_score`, `temporal_profile`.
* **Sources (required):**

  * Google Books Ngram (historical frequency time-series).
* **Sources (recommended):**

  * Contemporary web/news corpus frequency lists.
  * Subtitle/spoken corpora (e.g. OpenSubtitles) for spoken frequency proxy.

### 2.5 Semantic & Tagging DB

* **Target DB:** `semantics`
* **Fields:** `lemma`, `embedding`, `domain_tags[]`, `register_tags[]`, `affect_tags[]`, `imagery_tags[]`, `theme_tags[]`, `synonyms[]`, `antonyms[]`, `hypernyms[]`, `hyponyms[]`.
* **Sources (required):**

  * Embedding model (sentence/word encoder) for `embedding`.
  * Rule-based tagger: handcrafted keyword/label → tag mappings.
* **Sources (recommended):**

  * WordNet or similar for lexical relations.
  * Seed lists for each tag family (domain, affect, imagery, themes).
  * ConceptNet or similar for extra associative links (optional).

### 2.6 Concept Graph DB

* **Target DB:** `concept_graph`
* **Nodes:** `CONCEPT_NODE{id, label, centroid_embedding, ontology_refs}`; `MOTIF_NODE{id, label, concept_ids[]}`.
* **Edges:** `ASSOCIATES_WITH`, `CONTRASTS_WITH`, `METAPHOR_BRIDGE`, `PART_OF`.
* **Sources (required):**

  * Clustering over `semantics.embedding`.
  * Manually authored ontology (themes, domains, imagery categories).
* **Sources (optional):**

  * External knowledge graphs for initial link suggestions (WordNet/ConceptNet).

### 2.7 Poetic Forms & Device Profiles DB

* **Target DB:** `poetic_forms`
* **Fields:**

  * `form_id`, `name`, `stanza_specs[]`, `rhyme_pattern`, `meter_pattern`, `special_rules`, `device_profile_defaults`.
* **Sources (required):**

  * classify-poetry repository (form patterns, classification features).
  * Hand-authored specs based on standard prosody references + Masterclass article.
* **Sources (optional):**

  * Additional prosody handbooks for more obscure forms and meter variants.

### 2.8 Generation Configuration & Logs

* **Target DB:** `generation_runs`
* **Fields:** `run_id`, `input_spec`, `form_id`, `theme`, `parameter_snapshot`, `poem_text`, `debug_annotations` (meter/rhyme/semantic traces).
* **Sources:**

  * Internal only (no external data) – produced by Generation Engine.

---

## 3. Steering & Iteration Framework

### 3.1 Constraint Model

* Represent each line with scored constraints: `S_rhyme`, `S_meter`, `S_semantics`, `S_affect`, `S_coherence`, `S_style`.
* Utility: `U = Σ w_i · S_i` with adjustable weights for strict/loose forms.
* Constraint tiers: **hard** (structure), **soft-high** (rhyme, meter), **soft-med** (theme/affect), **soft-low** (devices, rarity).

### 3.2 Conflict Detection

* Evaluate generated line against target form + semantic profile.
* Identify primary conflict type: *rhyme*, *meter*, *semantic*, *coherence*.

### 3.3 Repair Strategies (Ordered)

* **Local substitution**: keep rhyme/meter; swap terms within same semantic cluster.
* **Slant-rhyme tolerance**: broaden rhyme class; re-evaluate linked lines.
* **Rhyme-class pivot**: adopt new anchor word; update lines sharing that rhyme symbol.
* **Meter micro-edits**: replace tokens with shorter/longer synonyms; insert/remove light words.
* **Semantic correction**: adjust domain/affect alignment; pull back to motif.
* **Coherence smoothing**: adjust nearby lines; insert bridging terms.
* **Structural relaxation** (optional): allow controlled form-breaking via policy.

### 3.4 LLM Usage (Constrained)

* Use only for bounded tasks: paraphrase under constraint, propose near-synonyms, perform micro-edits.
* Inputs always include: target meter, rhyme class, semantic cluster, POS roles.
* Outputs always validated by deterministic engines (rhyme/meter/theme checks).

### 3.5 Iteration Loop

```
for each line:
    L0 ← core_generation()
    score0 ← evaluate(L0)
    if acceptable: accept
    else:
        conflict ← diagnose(score0)
        L1 ← repair(L0, conflict, policy)
        score1 ← evaluate(L1)
        if score1 ≥ score0: accept L1 else accept L0 or escalate
```

### 3.6 Steering Policies

* Profiles define behaviour: `{w_rhyme, w_meter, w_semantics, allow_slant, allow_pivot, allow_breaks, max_repairs}`.
* Examples: **strict_sonnet**, **loose_tercet**, **free_verse**.

---

## 4. Ranking Metrics & Audit Framework

### 4.0 Characteristic Variable Map (Per Poem)

*All variables normalised to [0,1] unless noted.*

#### Meter Variables

* **Meter Pattern Encoding (per line)**

  * `meter_pattern.n`

    * Meaning: syllable count for the line.
    * Type: integer.
  * `meter_pattern.bits`

    * Meaning: binary stress pattern, one bit per syllable.
    * Encoding: `0` = unstressed, `1` = stressed; length = `n`.
    * Storage: bitstring (e.g. "010010") or packed integer.
  * `expected_bits`

    * Meaning: target stress pattern for the line length.
    * Construction: repeat/truncate target foot pattern (e.g. iamb `[0,1]`) to length `n`.

* `M_foot_accuracy`

  * Meaning: proportion of feet matching target pattern.
  * Per line: segment `meter_pattern.bits` into feet; `matches / total_feet`.
  * Range: 0 = no feet match, 1 = all feet match.

* `M_syllable_deviation`

  * Meaning: average deviation from target syllable count.
  * Raw: `abs(meter_pattern.n - target_syllables)`.
  * Normalised: map max tolerated deviation `D_max` to 0 → `M_syllable_deviation = 1 - (avg_dev / D_max)`.

* `M_stress_deviation`

  * Meaning: deviation in stress sequence vs canonical pattern.
  * Raw: Hamming distance between `meter_pattern.bits` and `expected_bits` divided by `n`.
  * Normalised: `M_stress_deviation = 1 - (hamming / n)`.

* `M_rhythm_variance`

  * Meaning: regularity of stress spacing.
  * Raw: compute positions of `1` in `meter_pattern.bits`; take variance of intervals.
  * Normalised: `M_rhythm_variance = 1 - normalise(variance)`.

* `M_downbeat_alignment`

  * Meaning: alignment of actual stresses with expected stresses.
  * Raw: dot product between `meter_pattern.bits` and `expected_bits` divided by `n`.
  * Range: [0,1].

* `M_syncopation_index`

  * Meaning: degree of stress on unexpected positions.
  * Raw: sum over positions where `meter_pattern.bits[i]=1` and `expected_bits[i]=0`, divided by total stresses.
  * Range: [0,1].

* `M_stability`

  * Meaning: consistency of meter across poem.
  * Raw: variance of `M_foot_accuracy`, `M_syllable_deviation`, and `M_stress_deviation` across lines.
  * Normalised: `M_stability = 1 - normalise(variance)`.

* `M_score`

  * Meaning: overall meter quality.
  * Formula: `M_score = a·M_foot_accuracy + b·M_syllable_deviation + c·M_stress_deviation + d·M_rhythm_variance + e·M_downbeat_alignment`, with weights summing to 1.

#### Rhyme Variables (summary)

* `M_foot_accuracy`

  * Meaning: proportion of feet matching target stress pattern.
  * Range: 0 = no feet match, 1 = all feet match.
  * Per line: `correct_feet / total_feet`.
  * Aggregation: mean across lines; stanza-level means optional.

* `M_syllable_deviation`

  * Meaning: average deviation from target syllable count.
  * Raw: `abs(line_syllables - target_syllables)`.
  * Normalised: map max tolerated deviation `D_max` to 0 → `M_syllable_deviation = 1 - (avg_dev / D_max)` clipped to [0,1].

* `M_stress_deviation`

  * Meaning: deviation in stress sequence vs canonical pattern.
  * Raw: Hamming distance between target and actual stress pattern / foot.
  * Normalised: `1 - (avg_stress_distance / max_distance)`.

* `M_stability`

  * Meaning: consistency of meter across poem.
  * Raw: variance of `M_foot_accuracy` and `M_syllable_deviation` across lines.
  * Normalised: `M_stability = 1 - normalise(variance)`.

* `M_score`

  * Meaning: overall meter quality.
  * Formula: `M_score = a·M_foot_accuracy + b·M_syllable_deviation + c·M_stress_deviation + d·M_stability` with `a+b+c+d=1`.

#### Rhyme Variables (summary)

* `R_density`: rhyme-linked positions ÷ eligible positions.
* `R_economy`: 1 − (num_rhyme_classes / max_classes).
* `R_strictness`: proportion of pairs with slant_distance ≤ τ_strict.
* `R_stability`: 1 − variance of rhyme-class assignment per symbol.

#### Semantic Variables (summary)

* `S_motif_coherence`: mean similarity line_vectors → motif_centroid.
* `S_theme_coherence`: 1 − variance of theme/domain tags across lines.
* `S_depth`: normalised (rare_word_count × avg_definition_complexity).

#### Technique Pattern Encoding (per technique T)

* **Pattern Domain**

  * `P_T.n`

    * Meaning: length of pattern domain for technique T (e.g. syllables, words, rhyme slots).
    * Type: integer per line.
  * `P_T.seq`

    * Meaning: discrete pattern over domain for technique T.
    * Type: sequence of length `P_T.n` with values in `{0,…,K_T-1}`.

      * Example (binary): alliteration presence per word → `0` = none, `1` = participates.
      * Example (multi-valued): rhyme-class index per line-ending → `0..K_rhyme-1`.
    * Storage: integer array, small enums, or compact code.

* **Per-line Derived Metrics for T**

  * `T_presence_line`

    * Meaning: does T occur at least once in the line?
    * Raw: `any(P_T.seq != 0)`.
  * `T_intensity_line`

    * Meaning: proportion of positions with T-active states.
    * Raw: `count(P_T.seq != 0) / P_T.n`.
  * `T_pattern_regularisation_line`

    * Meaning: regularity of active positions for T.
    * Raw: variance of intervals between active indices; normalised.
  * `T_shape_line`

    * Meaning: normalised positions of active indices (for cross-line comparison).
    * Raw: `{i/(P_T.n-1) | P_T.seq[i] != 0}`.

* **Aggregated Metrics for T (poem-level)**

  * `T_intensity`

    * Meaning: avg `T_intensity_line` across lines.
  * `T_coverage`

    * Meaning: fraction of lines where `T_presence_line` is true.
  * `T_regularisation`

    * Meaning: 1 − normalised variance of `T_shape_line` patterns across lines/stanzas.
  * `T_scheme_divergence`

    * Meaning: avg distance between T’s pattern and other techniques’ patterns (shape comparison over normalised positions).

* `T_score`

  * Meaning: overall quality/structure for technique T.
  * Formula: `T_score = α·T_coverage + β·T_intensity + γ·T_regularisation + δ·T_scheme_divergence`.

#### Technique Variables (per technique T)

* `T_intensity`: fraction of lines containing ≥1 event of T.
* `T_density`: avg events_per_line.
* `T_regularisation`: 1 − variance of event positions across stanzas.
* `T_variation`: avg scheme distance between T and other techniques.
* `T_score`: `α·T_intensity + β·T_density + γ·T_regularisation + δ·T_variation`.
* `T_intensity`: fraction of lines containing ≥1 event of T.
* `T_density`: avg events_per_line.
* `T_regularisation`: 1 − variance of event positions across stanzas.
* `T_variation`: avg scheme distance between T and other techniques.
* `T_score`: `α·T_intensity + β·T_density + γ·T_regularisation + δ·T_variation`.

#### Layering & Variation

* `L_layers`: active techniques count ÷ total techniques.
* `L_divergence`: average inter-technique scheme distance.
* `L_score`: `u·L_layers + v·L_divergence`.

---

### 4.1 Global Score Structure

* Each poem receives a vector of metrics:

  * `R_rhyme` (rhyme density/quality)
  * `R_meter` (meter consistency)
  * `R_semantic` (semantic coherence + motif stability)
  * `R_depth` (information richness)
  * `R_layers` (multi-technique layering)
  * `R_variation` (technique-scheme differentiation)
* Final score: `TOTAL = Σ w_i · R_i`.

### 4.2 Rhyme Metrics

* **Rhyme Density**: number of rhyme-linked positions ÷ total eligible positions.
* **Rhyme Economy**: fewer rhyme-classes → higher score.
* **Strictness**: proportion of perfect rhymes.
* **Slant Measurement**:

  * Distance metric on IPA finals: `D = α·vowel_dist + β·coda_dist`.
  * Slant score: `1 - normalise(D)`.
* **Rhyme Stability**: consistency of rhyme-class across all lines sharing symbol.

### 4.3 Meter Metrics

* **Foot Accuracy**: fraction of feet matching target stress pattern.
* **Line Deviation**: mean/variance of syllable count deviations.
* **Meter Stability**: consistency across stanzas.

### 4.4 Semantic Metrics

* **Motif Coherence**: average embedding similarity of lines to motif-centroid.
* **Theme Coherence**: variance of domain/affect tags across lines.
* **Information Depth**:

  * Weighted rarity × number of semantically rich tokens.
  * Penalise filler/common tokens.

### 4.5 Technique Layer Metrics

Techniques: alliteration, assonance, consonance, internal rhyme, parallelism.
For each technique **T**:

* **T_intensity**: proportion of lines containing T.
* **T_density**: number of T-events per line.
* **T_scheme**: categorical/structural map of positions where T appears.
* **T_regularisation**: similarity of T_scheme to itself across stanzas.
* **T_variation**: difference between this technique's scheme and others.
* Combined technique score:

  `R_T = w_int·T_intensity + w_den·T_density + w_reg·T_regularisation + w_var·T_variation`.

### 4.6 Layering Score

* Count techniques with `R_T ≥ threshold`.
* `R_layers = number_of_active_techniques / total_possible`.

### 4.7 Variation & Differentiation Metrics

* **Inter-technique divergence**: average pairwise difference between schemes.
* **Cross-stanza evolution**: measure of controlled drift in rhyme/meter/technique.

---

## 5. Source Priority Summary

* **Tier 1 (must have):**

  * Phrontistery wordlist (scraped).
  * One main dictionary API (definitions + POS + examples + phonetics if available).
  * English-to-IPA / CMU for phonetics.
  * Ngram or equivalent for historical frequency.
  * Embedding model for semantic vectors.
  * Hand-authored ontology + tag seed lists.
  * Hand-authored form specs (backed by classify-poetry + Masterclass).

* **Tier 2 (strongly recommended):**

  * Wordnik or another rare-word friendly API.
  * Wiktionary for archaic/obscure entries.
  * WordNet for lexical relations.
  * Contemporary frequency lists (web/news/subtitles).

* **Tier 3 (nice to have):**

  * ConceptNet or similar graph for extra associations.
  * Premium dictionary APIs for richer labels/usage notes.
  * Additional prosody/metrics databases for stress/meter validation.
