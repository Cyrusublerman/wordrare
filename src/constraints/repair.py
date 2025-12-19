"""
Conflict detection and repair strategies.

Implements repair strategies from BuildGuide Section 3.3.
"""

import logging
from typing import List, Optional, Dict, Tuple
from enum import Enum
import numpy as np

from .constraint_model import Constraint, ConstraintModel, SteeringPolicy
from ..forms import MeterEngine, SoundEngine
from ..database import WordRecord, Semantics, get_session

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts."""
    RHYME = "rhyme"
    METER = "meter"
    SEMANTIC = "semantic"
    COHERENCE = "coherence"


class RepairStrategy(Enum):
    """Repair strategies in priority order."""
    LOCAL_SUBSTITUTION = "local_substitution"
    SLANT_RHYME_TOLERANCE = "slant_rhyme_tolerance"
    RHYME_CLASS_PIVOT = "rhyme_class_pivot"
    METER_MICRO_EDITS = "meter_micro_edits"
    SEMANTIC_CORRECTION = "semantic_correction"
    COHERENCE_SMOOTHING = "coherence_smoothing"
    STRUCTURAL_RELAXATION = "structural_relaxation"


class ConflictDetector:
    """Detects conflicts in generated lines."""

    def __init__(self):
        self.constraint_model = ConstraintModel()
        self.meter_engine = MeterEngine()
        self.sound_engine = SoundEngine()

    def detect_conflict(self, line: str, target_spec: Dict) -> Optional[ConflictType]:
        """
        Detect primary conflict type in a line.

        Args:
            line: Generated line
            target_spec: Target specifications

        Returns:
            Primary conflict type or None
        """
        constraints = self.constraint_model.evaluate_line(line, target_spec)
        violated = self.constraint_model.get_violated_constraints(
            list(constraints.values())
        )

        if not violated:
            return None

        # Return highest-priority violation
        primary = violated[0]

        if primary.name == 'rhyme':
            return ConflictType.RHYME
        elif primary.name == 'meter':
            return ConflictType.METER
        elif primary.name == 'semantics':
            return ConflictType.SEMANTIC
        elif primary.name == 'coherence':
            return ConflictType.COHERENCE

        return ConflictType.METER  # Default


class LineRepairer:
    """Repairs lines using various strategies."""

    def __init__(self, policy: SteeringPolicy = None):
        """
        Initialize repairer.

        Args:
            policy: Steering policy (defaults to loose_tercet)
        """
        self.policy = policy or SteeringPolicy.loose_tercet()
        self.meter_engine = MeterEngine()
        self.sound_engine = SoundEngine()
        self.detector = ConflictDetector()

    def repair_line(self, line: str, target_spec: Dict,
                   conflict: ConflictType) -> Optional[str]:
        """
        Repair a line based on conflict type.

        Args:
            line: Original line
            target_spec: Target specifications
            conflict: Type of conflict

        Returns:
            Repaired line or None
        """
        strategies = self._select_strategies(conflict)

        for strategy in strategies:
            repaired = self._apply_strategy(line, target_spec, strategy)

            if repaired and repaired != line:
                # Verify repair improved the line
                new_conflict = self.detector.detect_conflict(repaired, target_spec)

                if new_conflict is None or new_conflict != conflict:
                    logger.debug(f"Repair successful using {strategy.value}")
                    return repaired

        return None

    def _select_strategies(self, conflict: ConflictType) -> List[RepairStrategy]:
        """Select appropriate repair strategies for conflict type."""
        if conflict == ConflictType.RHYME:
            strategies = [
                RepairStrategy.LOCAL_SUBSTITUTION,
            ]

            if self.policy.allow_slant:
                strategies.append(RepairStrategy.SLANT_RHYME_TOLERANCE)

            if self.policy.allow_pivot:
                strategies.append(RepairStrategy.RHYME_CLASS_PIVOT)

            return strategies

        elif conflict == ConflictType.METER:
            return [
                RepairStrategy.METER_MICRO_EDITS,
                RepairStrategy.LOCAL_SUBSTITUTION
            ]

        elif conflict == ConflictType.SEMANTIC:
            return [
                RepairStrategy.SEMANTIC_CORRECTION,
                RepairStrategy.LOCAL_SUBSTITUTION
            ]

        else:  # COHERENCE
            return [
                RepairStrategy.COHERENCE_SMOOTHING,
                RepairStrategy.LOCAL_SUBSTITUTION
            ]

    def _apply_strategy(self, line: str, target_spec: Dict,
                       strategy: RepairStrategy) -> Optional[str]:
        """Apply a specific repair strategy."""
        if strategy == RepairStrategy.LOCAL_SUBSTITUTION:
            return self._local_substitution(line, target_spec)

        elif strategy == RepairStrategy.SLANT_RHYME_TOLERANCE:
            # Accept slant rhyme - no change needed
            return line

        elif strategy == RepairStrategy.METER_MICRO_EDITS:
            return self._meter_micro_edits(line, target_spec)

        elif strategy == RepairStrategy.SEMANTIC_CORRECTION:
            return self._semantic_correction(line, target_spec)

        # Other strategies not yet implemented
        return None

    def _local_substitution(self, line: str, target_spec: Dict) -> Optional[str]:
        """
        Substitute words while maintaining rhyme/meter.

        Args:
            line: Original line
            target_spec: Target specifications

        Returns:
            Modified line or None
        """
        words = line.split()

        if not words:
            return None

        # Try substituting each word
        for i in range(len(words) - 1):  # Don't substitute rhyme word
            original_word = words[i]

            # Find synonym with similar syllable count
            syllables = self.meter_engine.get_word_syllables(original_word)

            # Query database for alternatives
            with get_session() as session:
                candidates = session.query(WordRecord).filter(
                    WordRecord.syllable_count == syllables,
                    WordRecord.pos_primary == self._guess_pos(original_word)
                ).limit(10).all()

            if not candidates:
                continue

            # Try each candidate
            for candidate in candidates:
                test_words = words.copy()
                test_words[i] = candidate.lemma
                test_line = ' '.join(test_words)

                # Check if this improves the line
                conflict = self.detector.detect_conflict(test_line, target_spec)

                if conflict is None:
                    return test_line

        return None

    def _meter_micro_edits(self, line: str, target_spec: Dict) -> Optional[str]:
        """
        Make small edits to improve meter.

        Args:
            line: Original line
            target_spec: Target specifications

        Returns:
            Modified line or None
        """
        # Analyze current meter
        meter_name = target_spec.get('meter', 'iambic_pentameter')
        analysis = self.meter_engine.analyze_line(line, meter_name)

        # Get expected syllables from meter pattern
        meter_pattern = self.meter_engine.meter_patterns.get(meter_name)
        if not meter_pattern:
            return None

        expected_syllables = meter_pattern.expected_syllables

        # If too many syllables, try removing articles
        if analysis.syllable_count > expected_syllables:
            words = line.split()

            # Remove articles
            filtered = [w for w in words if w.lower() not in ['the', 'a', 'an']]

            if len(filtered) < len(words):
                return ' '.join(filtered)

        # If too few syllables, try adding articles
        elif analysis.syllable_count < expected_syllables:
            words = line.split()

            # Add article before first noun (simple heuristic)
            if words and words[0][0].isupper():
                return 'The ' + line

        return None

    def _semantic_correction(self, line: str, target_spec: Dict) -> Optional[str]:
        """
        Adjust semantic alignment by substituting words.

        Identifies words with low semantic alignment to theme and
        substitutes them with semantically similar words that better
        align with the target theme.

        Args:
            line: Original line
            target_spec: Target specifications (must include semantic_palette)

        Returns:
            Modified line with improved semantic alignment, or None if no improvement possible
        """
        semantic_palette = target_spec.get('semantic_palette')
        if not semantic_palette or 'word_pools' not in semantic_palette:
            return None

        # Extract words from line
        words = line.split()
        if len(words) < 2:
            return None

        # Get theme word embeddings from palette
        theme_words = []
        for motif_words in semantic_palette.get('word_pools', {}).values():
            theme_words.extend(motif_words[:10])

        if not theme_words:
            return None

        # Get theme embeddings
        theme_embeddings = []
        with get_session() as session:
            for word in theme_words[:30]:
                sem = session.query(Semantics).filter_by(lemma=word.lower()).first()
                if sem and sem.embedding:
                    theme_embeddings.append(np.array(sem.embedding))

        if len(theme_embeddings) < 5:
            return None  # Not enough theme data

        # Compute theme centroid
        theme_centroid = np.mean(theme_embeddings, axis=0)

        # Analyze each word's semantic alignment
        word_scores = []
        with get_session() as session:
            for idx, word in enumerate(words):
                clean_word = word.strip('.,!?;:\'\"').lower()
                if not clean_word:
                    continue

                sem = session.query(Semantics).filter_by(lemma=clean_word).first()
                if not sem or not sem.embedding:
                    word_scores.append((idx, 0.5, None))  # Neutral score for unknown words
                    continue

                # Compute cosine similarity to theme centroid
                word_emb = np.array(sem.embedding)
                dot_product = np.dot(word_emb, theme_centroid)
                norm_product = np.linalg.norm(word_emb) * np.linalg.norm(theme_centroid)

                if norm_product > 0:
                    similarity = dot_product / norm_product
                else:
                    similarity = 0.5

                word_scores.append((idx, similarity, clean_word))

        # Find word with lowest semantic alignment (but skip first and last words to preserve structure)
        substitutable = [ws for ws in word_scores if 0 < ws[0] < len(words) - 1 and ws[2] is not None]
        if not substitutable:
            return None

        substitutable.sort(key=lambda x: x[1])  # Sort by similarity (lowest first)
        worst_idx, worst_score, worst_word = substitutable[0]

        # Only substitute if alignment is poor (< 0.4)
        if worst_score >= 0.4:
            return None

        # Find a better alternative word
        with get_session() as session:
            # Get original word info for constraints
            original_sem = session.query(Semantics).filter_by(lemma=worst_word).first()
            original_record = session.query(WordRecord).filter_by(lemma=worst_word).first()

            if not original_record:
                return None

            # Find candidates with similar POS and syllable count
            candidates = session.query(WordRecord).join(
                Semantics, WordRecord.lemma == Semantics.lemma
            ).filter(
                WordRecord.pos_primary == original_record.pos_primary,
                WordRecord.syllable_count == original_record.syllable_count,
                WordRecord.lemma != worst_word,
                Semantics.embedding.isnot(None)
            ).limit(50).all()

            if not candidates:
                return None

            # Score each candidate by theme alignment
            best_candidate = None
            best_alignment = worst_score

            for candidate in candidates:
                cand_sem = session.query(Semantics).filter_by(lemma=candidate.lemma).first()
                if not cand_sem or not cand_sem.embedding:
                    continue

                # Compute alignment with theme
                cand_emb = np.array(cand_sem.embedding)
                dot_product = np.dot(cand_emb, theme_centroid)
                norm_product = np.linalg.norm(cand_emb) * np.linalg.norm(theme_centroid)

                if norm_product > 0:
                    alignment = dot_product / norm_product

                    if alignment > best_alignment:
                        best_alignment = alignment
                        best_candidate = candidate.lemma

            if best_candidate and best_alignment > worst_score + 0.1:  # Require meaningful improvement
                # Substitute the word
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

                modified_line = ' '.join(modified_words)
                logger.debug(f"Semantic correction: '{worst_word}' -> '{best_candidate}' "
                           f"(alignment {worst_score:.2f} -> {best_alignment:.2f})")
                return modified_line

        return None

    def _guess_pos(self, word: str) -> str:
        """Guess POS from word (simple heuristic)."""
        # Very simple heuristic
        if word.endswith('ly'):
            return 'adverb'
        elif word.endswith('ing'):
            return 'verb'
        elif word.endswith('ed'):
            return 'verb'
        else:
            return 'noun'


class IterativeRepairer:
    """Performs iterative repair with scoring."""

    def __init__(self, policy: SteeringPolicy = None):
        """
        Initialize iterative repairer.

        Args:
            policy: Steering policy
        """
        self.policy = policy or SteeringPolicy.loose_tercet()
        self.detector = ConflictDetector()
        self.repairer = LineRepairer(policy)
        self.constraint_model = ConstraintModel()

    def repair_with_iterations(self, line: str, target_spec: Dict) -> str:
        """
        Iteratively repair line until acceptable or max iterations.

        Implements the iteration loop from BuildGuide Section 3.5.

        Args:
            line: Original line
            target_spec: Target specifications

        Returns:
            Best line found
        """
        L0 = line
        constraints0 = self.constraint_model.evaluate_line(L0, target_spec)
        score0 = self.constraint_model.compute_utility(list(constraints0.values()))

        # Check if already acceptable
        if score0 >= 0.8:
            return L0

        best_line = L0
        best_score = score0

        # Iteration loop
        for iteration in range(self.policy.max_repairs):
            conflict = self.detector.detect_conflict(best_line, target_spec)

            if conflict is None:
                # No conflict - accept
                return best_line

            # Attempt repair
            L1 = self.repairer.repair_line(best_line, target_spec, conflict)

            if L1 is None:
                # Repair failed - keep current best
                break

            # Evaluate repaired line
            constraints1 = self.constraint_model.evaluate_line(L1, target_spec)
            score1 = self.constraint_model.compute_utility(list(constraints1.values()))

            # Accept if improved
            if score1 >= best_score:
                best_line = L1
                best_score = score1
                logger.debug(f"Iteration {iteration+1}: score improved to {score1:.2f}")
            else:
                # No improvement - stop
                break

        return best_line


def main():
    """CLI for repair testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Conflict detection and repair")
    parser.add_argument(
        '--line',
        type=str,
        required=True,
        help='Line to repair'
    )
    parser.add_argument(
        '--meter',
        type=str,
        default='iambic_pentameter',
        help='Target meter'
    )
    parser.add_argument(
        '--rhyme-word',
        type=str,
        help='Word to rhyme with'
    )
    parser.add_argument(
        '--policy',
        choices=['strict', 'loose', 'free'],
        default='loose',
        help='Steering policy'
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    # Select policy
    if args.policy == 'strict':
        policy = SteeringPolicy.strict_sonnet()
    elif args.policy == 'free':
        policy = SteeringPolicy.free_verse()
    else:
        policy = SteeringPolicy.loose_tercet()

    # Build target spec
    target_spec = {'meter': args.meter}
    if args.rhyme_word:
        target_spec['rhyme_word'] = args.rhyme_word

    # Detect conflict
    detector = ConflictDetector()
    conflict = detector.detect_conflict(args.line, target_spec)

    print(f"\nOriginal: '{args.line}'")
    print(f"Conflict: {conflict.value if conflict else 'None'}")

    if conflict:
        # Attempt repair
        repairer = IterativeRepairer(policy)
        repaired = repairer.repair_with_iterations(args.line, target_spec)

        print(f"Repaired: '{repaired}'")

        # Show improvement
        model = ConstraintModel()

        orig_constraints = model.evaluate_line(args.line, target_spec)
        orig_score = model.compute_utility(list(orig_constraints.values()))

        rep_constraints = model.evaluate_line(repaired, target_spec)
        rep_score = model.compute_utility(list(rep_constraints.values()))

        print(f"\nScore: {orig_score:.2f} → {rep_score:.2f}")


if __name__ == "__main__":
    main()
