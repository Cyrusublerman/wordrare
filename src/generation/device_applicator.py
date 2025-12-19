"""
Poetic device applicator - applies devices to enhance generated poems.

Implements enjambment, caesura, internal rhyme, metaphor bridges, and motif recurrence.
"""

import logging
import random
from typing import List, Dict, Optional, Tuple
import re

from ..forms import GrammarEngine, SoundEngine
from ..database import WordRecord, Semantics, get_session
from .generation_spec import GenerationSpec

logger = logging.getLogger(__name__)


class DeviceApplicator:
    """Applies poetic devices to poem lines."""

    def __init__(self, spec: GenerationSpec, semantic_palette: Dict):
        """
        Initialize DeviceApplicator.

        Args:
            spec: Generation specification
            semantic_palette: Semantic palette with theme concepts and motifs
        """
        self.spec = spec
        self.semantic_palette = semantic_palette
        self.grammar_engine = GrammarEngine()
        self.sound_engine = SoundEngine()

        # Device configuration from spec
        self.device_profile = spec.device_profile or {}
        self.enjambment_strength = self.device_profile.get('enjambment', 0.0)
        self.caesura_strength = self.device_profile.get('caesura', 0.0)
        self.internal_rhyme_strength = self.device_profile.get('internal_rhyme', 0.0)
        self.metaphor_strength = self.device_profile.get('metaphor', 0.0)
        self.motif_strength = spec.motif_density

    def apply_devices(self, lines: List[str]) -> List[str]:
        """
        Apply all enabled devices to poem lines.

        Args:
            lines: Original poem lines

        Returns:
            Modified lines with devices applied
        """
        if not lines:
            return lines

        logger.info(f"Applying devices: enjambment={self.enjambment_strength:.2f}, "
                   f"caesura={self.caesura_strength:.2f}, "
                   f"internal_rhyme={self.internal_rhyme_strength:.2f}, "
                   f"metaphor={self.metaphor_strength:.2f}, "
                   f"motif={self.motif_strength:.2f}")

        # Apply enjambment (modifies line breaks)
        if self.enjambment_strength > 0:
            lines = self._apply_enjambment(lines)

        # Apply caesura (adds mid-line pauses)
        if self.caesura_strength > 0:
            lines = self._apply_caesura(lines)

        # Apply internal rhyme
        if self.internal_rhyme_strength > 0:
            lines = self._apply_internal_rhyme(lines)

        # Apply metaphor bridges
        if self.metaphor_strength > 0:
            lines = self._apply_metaphor_bridges(lines)

        # Apply motif recurrence
        if self.motif_strength > 0:
            lines = self._apply_motif_recurrence(lines)

        return lines

    def _apply_enjambment(self, lines: List[str]) -> List[str]:
        """
        Apply enjambment by breaking syntax across line boundaries.

        Args:
            lines: Original lines

        Returns:
            Modified lines with enjambment
        """
        if len(lines) < 2:
            return lines

        # Determine how many enjambments to apply
        num_enjambments = int(len(lines) * self.enjambment_strength * 0.3)
        num_enjambments = max(1, min(num_enjambments, len(lines) // 2))

        # Identify candidate line pairs for enjambment
        candidates = []
        for i in range(len(lines) - 1):
            line = lines[i]
            next_line = lines[i + 1]

            # Skip if line already ends with enjambment indicators
            if line.rstrip().endswith((',', ';', '—', '--')):
                continue

            # Analyze syntax to find good break points
            analysis = self.grammar_engine.analyze_line_syntax(line)
            if analysis['word_count'] >= 4:
                candidates.append(i)

        if not candidates:
            return lines

        # Apply enjambment to selected lines
        modified_lines = lines.copy()
        selected = random.sample(candidates, min(num_enjambments, len(candidates)))

        for line_idx in selected:
            line = modified_lines[line_idx]

            # Remove terminal punctuation to create enjambment effect
            line = line.rstrip('.,!?;:')

            # Optionally add enjambment marker (dash or comma)
            if random.random() < 0.3:
                line += ','

            modified_lines[line_idx] = line
            logger.debug(f"Applied enjambment at line {line_idx}")

        return modified_lines

    def _apply_caesura(self, lines: List[str]) -> List[str]:
        """
        Apply caesura (mid-line pauses) using punctuation.

        Args:
            lines: Original lines

        Returns:
            Modified lines with caesura
        """
        # Determine how many caesuras to apply
        num_caesuras = int(len(lines) * self.caesura_strength * 0.4)
        num_caesuras = max(1, min(num_caesuras, len(lines)))

        modified_lines = lines.copy()
        candidates = list(range(len(lines)))
        random.shuffle(candidates)

        applied = 0
        for line_idx in candidates:
            if applied >= num_caesuras:
                break

            line = modified_lines[line_idx]
            words = line.split()

            # Need at least 6 words for meaningful caesura
            if len(words) < 6:
                continue

            # Find mid-point (slight variation around center)
            mid_point = len(words) // 2
            variation = random.randint(-1, 1)
            insert_pos = max(2, min(len(words) - 3, mid_point + variation))

            # Check if there's already punctuation nearby
            if any(words[i].rstrip('.,!?;:—') != words[i]
                   for i in range(max(0, insert_pos - 1), min(len(words), insert_pos + 2))):
                continue

            # Insert caesura marker (em dash, semicolon, or comma)
            markers = ['—', ';', ',', ',']  # Weighted toward comma
            marker = random.choice(markers)

            words[insert_pos - 1] = words[insert_pos - 1].rstrip('.,!?;:') + marker

            modified_lines[line_idx] = ' '.join(words)
            applied += 1
            logger.debug(f"Applied caesura at line {line_idx}, position {insert_pos}")

        return modified_lines

    def _apply_internal_rhyme(self, lines: List[str]) -> List[str]:
        """
        Apply internal rhyme within lines.

        Args:
            lines: Original lines

        Returns:
            Modified lines with internal rhyme
        """
        # Determine how many internal rhymes to apply
        num_rhymes = int(len(lines) * self.internal_rhyme_strength * 0.5)
        num_rhymes = max(1, min(num_rhymes, len(lines)))

        modified_lines = lines.copy()
        candidates = list(range(len(lines)))
        random.shuffle(candidates)

        applied = 0
        for line_idx in candidates:
            if applied >= num_rhymes:
                break

            line = modified_lines[line_idx]
            words = [w.strip('.,!?;:\'\"') for w in line.split()]

            # Need at least 5 words for internal rhyme
            if len(words) < 5:
                continue

            # Get rhyme key for last word
            last_word = words[-1].lower()
            rhyme_key = self.sound_engine.get_rhyme_key(last_word)

            if not rhyme_key:
                continue

            # Try to find a word in middle of line that rhymes
            for i in range(2, len(words) - 2):
                word = words[i].lower()
                word_rhyme_key = self.sound_engine.get_rhyme_key(word)

                if word_rhyme_key and word_rhyme_key == rhyme_key:
                    # Already has internal rhyme!
                    applied += 1
                    logger.debug(f"Found existing internal rhyme at line {line_idx}: {word} / {last_word}")
                    break
            else:
                # Try to substitute a mid-line word with a rhyming alternative
                mid_word_idx = len(words) // 2
                mid_word = words[mid_word_idx].lower()

                # Find rhyming alternatives
                with get_session() as session:
                    rhyming_words = session.query(WordRecord).filter(
                        WordRecord.rhyme_key == rhyme_key,
                        WordRecord.lemma != last_word,
                        WordRecord.lemma != mid_word,
                        WordRecord.rarity_score >= self.spec.min_rarity,
                        WordRecord.rarity_score <= self.spec.max_rarity
                    ).limit(10).all()

                if rhyming_words:
                    # Pick a random rhyming word
                    new_word = random.choice(rhyming_words).lemma
                    original_word = line.split()[mid_word_idx]

                    # Preserve capitalization
                    if original_word[0].isupper():
                        new_word = new_word.capitalize()

                    # Replace in line
                    line_words = line.split()
                    line_words[mid_word_idx] = new_word
                    modified_lines[line_idx] = ' '.join(line_words)

                    applied += 1
                    logger.debug(f"Applied internal rhyme at line {line_idx}: {new_word} / {last_word}")

        return modified_lines

    def _apply_metaphor_bridges(self, lines: List[str]) -> List[str]:
        """
        Apply metaphor bridges from semantic palette.

        Args:
            lines: Original lines

        Returns:
            Modified lines with metaphor bridges
        """
        metaphor_bridges = self.semantic_palette.get('metaphor_bridges', [])

        if not metaphor_bridges:
            logger.debug("No metaphor bridges in palette")
            return lines

        # Determine how many metaphors to apply
        num_metaphors = int(len(lines) * self.metaphor_strength * 0.3)
        num_metaphors = max(1, min(num_metaphors, len(metaphor_bridges), len(lines)))

        # Select random metaphor bridges
        selected_bridges = random.sample(metaphor_bridges, num_metaphors)

        modified_lines = lines.copy()
        line_indices = list(range(len(lines)))
        random.shuffle(line_indices)

        for bridge_idx, (source_concept, target_concept) in enumerate(selected_bridges):
            if bridge_idx >= len(line_indices):
                break

            line_idx = line_indices[bridge_idx]

            # Get words for both concepts
            source_words = self._get_concept_words(source_concept, limit=5)
            target_words = self._get_concept_words(target_concept, limit=5)

            if not source_words or not target_words:
                continue

            # Try to insert both words into the line
            line = modified_lines[line_idx]
            words = line.split()

            # Simple approach: append metaphor phrase to line
            source_word = random.choice(source_words)
            target_word = random.choice(target_words)

            # Create metaphor phrase (simple patterns)
            patterns = [
                f"like {source_word} in {target_word}",
                f"as {source_word} to {target_word}",
                f"{source_word} of {target_word}",
            ]
            metaphor_phrase = random.choice(patterns)

            # Insert into line (if space allows - rough heuristic)
            if len(words) < 10:
                modified_lines[line_idx] = f"{line.rstrip('.,!?;:')} {metaphor_phrase}"
                logger.debug(f"Applied metaphor bridge at line {line_idx}: {source_concept} -> {target_concept}")

        return modified_lines

    def _apply_motif_recurrence(self, lines: List[str]) -> List[str]:
        """
        Apply motif recurrence by reinforcing theme words.

        Args:
            lines: Original lines

        Returns:
            Modified lines with enhanced motif recurrence
        """
        motifs = self.semantic_palette.get('motifs', [])
        word_pools = self.semantic_palette.get('word_pools', {})

        if not motifs or not word_pools:
            logger.debug("No motifs in palette for recurrence")
            return lines

        # Collect motif words
        all_motif_words = []
        for motif_id in motifs:
            if motif_id in word_pools:
                all_motif_words.extend(word_pools[motif_id][:5])

        if not all_motif_words:
            return lines

        # Determine how many recurrences to apply
        num_recurrences = int(len(lines) * self.motif_strength * 0.4)
        num_recurrences = max(1, min(num_recurrences, len(lines)))

        modified_lines = lines.copy()
        line_indices = list(range(len(lines)))
        random.shuffle(line_indices)

        applied = 0
        for line_idx in line_indices:
            if applied >= num_recurrences:
                break

            line = modified_lines[line_idx]
            words = line.split()

            # Only apply if line is not too long
            if len(words) >= 10:
                continue

            # Pick a random motif word
            motif_word = random.choice(all_motif_words)

            # Simple approach: append or prepend motif word
            if random.random() < 0.5:
                # Append
                modified_lines[line_idx] = f"{line.rstrip('.,!?;:')} {motif_word}"
            else:
                # Prepend (capitalize first word)
                modified_lines[line_idx] = f"{motif_word.capitalize()} {line}"

            applied += 1
            logger.debug(f"Applied motif recurrence at line {line_idx}: {motif_word}")

        return modified_lines

    def _get_concept_words(self, concept_id: int, limit: int = 5) -> List[str]:
        """
        Get words associated with a concept.

        Args:
            concept_id: Concept node ID
            limit: Maximum words to return

        Returns:
            List of words
        """
        # Check word pools first
        word_pools = self.semantic_palette.get('word_pools', {})
        if concept_id in word_pools:
            return word_pools[concept_id][:limit]

        # Otherwise return empty
        return []
