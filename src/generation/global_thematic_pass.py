"""
Global thematic pass - analyzes and smooths thematic progression across entire poem.

Implements thematic progression analysis, transition smoothing, and emotional intensity balancing.
"""

import logging
from typing import List, Dict, Optional, Tuple
import numpy as np

from ..database import Semantics, get_session
from .generation_spec import GenerationSpec

logger = logging.getLogger(__name__)


class GlobalThematicAnalyzer:
    """Analyzes and smooths thematic progression across entire poem."""

    def __init__(self, spec: GenerationSpec, semantic_palette: Dict):
        """
        Initialize GlobalThematicAnalyzer.

        Args:
            spec: Generation specification
            semantic_palette: Semantic palette with theme concepts
        """
        self.spec = spec
        self.semantic_palette = semantic_palette

    def apply_global_pass(self, lines: List[str]) -> List[str]:
        """
        Apply global thematic smoothing to poem.

        Args:
            lines: Original poem lines

        Returns:
            Modified lines with improved thematic progression
        """
        if len(lines) < 4:
            # Too short for meaningful global analysis
            return lines

        logger.info(f"Applying global thematic pass to {len(lines)} lines")

        # Analyze thematic progression
        progression = self._analyze_thematic_progression(lines)

        # Identify weak transitions
        weak_transitions = self._identify_weak_transitions(progression)

        if weak_transitions:
            logger.info(f"Found {len(weak_transitions)} weak transitions")
            # Smooth transitions
            lines = self._smooth_transitions(lines, weak_transitions, progression)

        # Balance emotional intensity
        if self.spec.affect_profile:
            lines = self._balance_emotional_intensity(lines)

        return lines

    def _analyze_thematic_progression(self, lines: List[str]) -> List[Dict]:
        """
        Analyze thematic progression throughout poem.

        Computes semantic centroid for groups of lines to understand
        how themes evolve through the poem.

        Args:
            lines: Poem lines

        Returns:
            List of progression data per group (stanza-like chunks)
        """
        # Group lines into chunks (stanzas or 4-line groups)
        chunk_size = 4
        progression = []

        for i in range(0, len(lines), chunk_size):
            chunk = lines[i:i + chunk_size]

            # Get embeddings for words in this chunk
            embeddings = []
            all_words = []

            with get_session() as session:
                for line in chunk:
                    words = [w.strip('.,!?;:\'\"').lower() for w in line.split()]
                    for word in words:
                        sem = session.query(Semantics).filter_by(lemma=word).first()
                        if sem and sem.embedding:
                            embeddings.append(np.array(sem.embedding))
                            all_words.append(word)

            if len(embeddings) >= 2:
                # Compute centroid for this chunk
                centroid = np.mean(embeddings, axis=0)

                progression.append({
                    'chunk_idx': i // chunk_size,
                    'line_start': i,
                    'line_end': min(i + chunk_size, len(lines)),
                    'centroid': centroid,
                    'embeddings': embeddings,
                    'words': all_words,
                    'num_words': len(all_words)
                })
            else:
                # Not enough data for this chunk
                progression.append({
                    'chunk_idx': i // chunk_size,
                    'line_start': i,
                    'line_end': min(i + chunk_size, len(lines)),
                    'centroid': None,
                    'embeddings': [],
                    'words': [],
                    'num_words': 0
                })

        return progression

    def _identify_weak_transitions(self, progression: List[Dict]) -> List[Tuple[int, int, float]]:
        """
        Identify weak transitions between chunks.

        Args:
            progression: Thematic progression data

        Returns:
            List of (chunk1_idx, chunk2_idx, similarity) for weak transitions
        """
        weak_transitions = []

        for i in range(len(progression) - 1):
            chunk1 = progression[i]
            chunk2 = progression[i + 1]

            if chunk1['centroid'] is None or chunk2['centroid'] is None:
                continue

            # Compute cosine similarity between chunk centroids
            centroid1 = chunk1['centroid']
            centroid2 = chunk2['centroid']

            dot_product = np.dot(centroid1, centroid2)
            norm_product = np.linalg.norm(centroid1) * np.linalg.norm(centroid2)

            if norm_product > 0:
                similarity = dot_product / norm_product
            else:
                similarity = 0.5

            # Identify weak transitions (low similarity)
            # Threshold: < 0.5 is considered weak
            if similarity < 0.5:
                weak_transitions.append((i, i + 1, similarity))
                logger.debug(f"Weak transition between chunks {i} and {i+1}: similarity={similarity:.3f}")

        return weak_transitions

    def _smooth_transitions(self, lines: List[str],
                           weak_transitions: List[Tuple[int, int, float]],
                           progression: List[Dict]) -> List[str]:
        """
        Smooth weak transitions by adjusting word choices.

        Args:
            lines: Original lines
            weak_transitions: List of weak transition tuples
            progression: Thematic progression data

        Returns:
            Modified lines with smoother transitions
        """
        modified_lines = lines.copy()

        for chunk1_idx, chunk2_idx, similarity in weak_transitions:
            # Focus on boundary lines (last line of chunk1, first line of chunk2)
            chunk1_data = progression[chunk1_idx]
            chunk2_data = progression[chunk2_idx]

            if chunk1_data['line_end'] > 0 and chunk2_data['line_start'] < len(lines):
                # Try to adjust the boundary line (last line of chunk1)
                boundary_line_idx = chunk1_data['line_end'] - 1

                # Get target centroid (average of both chunks)
                if chunk1_data['centroid'] is not None and chunk2_data['centroid'] is not None:
                    target_centroid = (chunk1_data['centroid'] + chunk2_data['centroid']) / 2

                    # Attempt word substitution to bridge the gap
                    modified_line = self._bridge_transition(
                        modified_lines[boundary_line_idx],
                        target_centroid
                    )

                    if modified_line:
                        modified_lines[boundary_line_idx] = modified_line
                        logger.debug(f"Smoothed transition at line {boundary_line_idx}")

        return modified_lines

    def _bridge_transition(self, line: str, target_centroid: np.ndarray) -> Optional[str]:
        """
        Adjust a line to bridge a thematic transition.

        Args:
            line: Original line
            target_centroid: Target semantic centroid to move toward

        Returns:
            Modified line or None if no improvement
        """
        words = line.split()
        if len(words) < 3:
            return None

        # Analyze word alignments with target centroid
        word_scores = []

        with get_session() as session:
            for idx, word in enumerate(words):
                clean_word = word.strip('.,!?;:\'\"').lower()
                if not clean_word:
                    continue

                sem = session.query(Semantics).filter_by(lemma=clean_word).first()
                if not sem or not sem.embedding:
                    word_scores.append((idx, 0.5, None))
                    continue

                word_emb = np.array(sem.embedding)
                dot_product = np.dot(word_emb, target_centroid)
                norm_product = np.linalg.norm(word_emb) * np.linalg.norm(target_centroid)

                if norm_product > 0:
                    alignment = dot_product / norm_product
                else:
                    alignment = 0.5

                word_scores.append((idx, alignment, clean_word))

        # Find word with lowest alignment (excluding first/last)
        substitutable = [ws for ws in word_scores if 0 < ws[0] < len(words) - 1 and ws[2] is not None]
        if not substitutable:
            return None

        substitutable.sort(key=lambda x: x[1])
        worst_idx, worst_score, worst_word = substitutable[0]

        # Only substitute if alignment is poor
        if worst_score >= 0.4:
            return None

        # Find a better word (similar approach to semantic correction)
        from ..database import WordRecord

        with get_session() as session:
            original_record = session.query(WordRecord).filter_by(lemma=worst_word).first()
            if not original_record:
                return None

            # Get candidates with same POS and syllable count
            candidates = session.query(WordRecord).join(
                Semantics, WordRecord.lemma == Semantics.lemma
            ).filter(
                WordRecord.pos_primary == original_record.pos_primary,
                WordRecord.syllable_count == original_record.syllable_count,
                WordRecord.lemma != worst_word,
                Semantics.embedding.isnot(None)
            ).limit(30).all()

            if not candidates:
                return None

            # Score candidates by alignment with target centroid
            best_candidate = None
            best_alignment = worst_score

            for candidate in candidates:
                cand_sem = session.query(Semantics).filter_by(lemma=candidate.lemma).first()
                if not cand_sem or not cand_sem.embedding:
                    continue

                cand_emb = np.array(cand_sem.embedding)
                dot_product = np.dot(cand_emb, target_centroid)
                norm_product = np.linalg.norm(cand_emb) * np.linalg.norm(target_centroid)

                if norm_product > 0:
                    alignment = dot_product / norm_product

                    if alignment > best_alignment:
                        best_alignment = alignment
                        best_candidate = candidate.lemma

            if best_candidate and best_alignment > worst_score + 0.1:
                # Substitute
                modified_words = words.copy()
                original_word = words[worst_idx]

                # Preserve capitalization
                if original_word[0].isupper():
                    best_candidate = best_candidate.capitalize()

                # Preserve punctuation
                punctuation = ''
                for char in original_word[::-1]:
                    if char in '.,!?;:\'\"':
                        punctuation = char + punctuation
                    else:
                        break

                modified_words[worst_idx] = best_candidate + punctuation
                return ' '.join(modified_words)

        return None

    def _balance_emotional_intensity(self, lines: List[str]) -> List[str]:
        """
        Balance emotional intensity across poem.

        Analyzes affect distribution and adjusts to create appropriate
        emotional arc (build-up, climax, resolution).

        Args:
            lines: Original lines

        Returns:
            Modified lines with balanced emotional intensity
        """
        if not self.spec.affect_profile:
            return lines

        # Analyze affect intensity per line
        intensities = []

        with get_session() as session:
            for line in lines:
                words = [w.strip('.,!?;:\'\"').lower() for w in line.split()]
                affect_count = 0
                total_count = 0

                for word in words:
                    sem = session.query(Semantics).filter_by(lemma=word).first()
                    if sem and sem.affect_tags:
                        total_count += 1
                        if self.spec.affect_profile in sem.affect_tags:
                            affect_count += 1

                intensity = affect_count / total_count if total_count > 0 else 0.5
                intensities.append(intensity)

        # Check if intensity distribution is balanced
        # Ideal: gradual build-up in first half, peak in middle, resolution in last quarter
        avg_intensity = np.mean(intensities)

        # If overall intensity is too low, no adjustment needed
        if avg_intensity < 0.3:
            logger.debug(f"Emotional intensity low ({avg_intensity:.2f}), no balancing needed")
            return lines

        # Check for extreme spikes or drops
        if len(intensities) > 4:
            # Look for sudden drops in intensity
            for i in range(1, len(intensities)):
                if intensities[i-1] - intensities[i] > 0.4:
                    # Sudden drop - could adjust line i to maintain flow
                    logger.debug(f"Sudden intensity drop at line {i}: {intensities[i-1]:.2f} -> {intensities[i]:.2f}")

        # For now, just log the analysis
        # Full implementation would adjust word choices to smooth intensity curve
        logger.debug(f"Emotional intensity distribution: min={min(intensities):.2f}, "
                    f"max={max(intensities):.2f}, avg={avg_intensity:.2f}")

        return lines
