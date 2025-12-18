"""
Constraint model for multi-tier constraint satisfaction.

Implements the constraint framework from BuildGuide Section 3.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

from ..database import WordRecord, Semantics, get_session

logger = logging.getLogger(__name__)


class ConstraintTier(Enum):
    """Constraint priority tiers."""
    HARD = "hard"  # Structure - must be satisfied
    SOFT_HIGH = "soft_high"  # Rhyme, meter - highly desirable
    SOFT_MED = "soft_med"  # Theme, affect - moderately desirable
    SOFT_LOW = "soft_low"  # Devices, rarity - nice to have


@dataclass
class Constraint:
    """Represents a single constraint."""
    name: str
    tier: ConstraintTier
    weight: float
    score: float = 0.0  # 0.0 to 1.0
    satisfied: bool = False

    def evaluate(self) -> float:
        """
        Evaluate constraint contribution to overall score.

        Returns:
            Weighted score
        """
        return self.score * self.weight


class ConstraintModel:
    """Manages constraints and computes utility scores."""

    def __init__(self, weights: Dict[str, float] = None):
        """
        Initialize constraint model.

        Args:
            weights: Custom constraint weights
        """
        self.weights = weights or {
            'rhyme': 0.25,
            'meter': 0.25,
            'semantics': 0.20,
            'affect': 0.15,
            'coherence': 0.10,
            'style': 0.05
        }

        # Constraint tier mappings
        self.tier_map = {
            'structure': ConstraintTier.HARD,
            'rhyme': ConstraintTier.SOFT_HIGH,
            'meter': ConstraintTier.SOFT_HIGH,
            'semantics': ConstraintTier.SOFT_MED,
            'affect': ConstraintTier.SOFT_MED,
            'coherence': ConstraintTier.SOFT_MED,
            'style': ConstraintTier.SOFT_LOW,
            'devices': ConstraintTier.SOFT_LOW,
            'rarity': ConstraintTier.SOFT_LOW
        }

    def create_constraint(self, name: str, score: float,
                         tier: ConstraintTier = None) -> Constraint:
        """
        Create a constraint.

        Args:
            name: Constraint name
            score: Score value (0.0-1.0)
            tier: Priority tier (auto-detected if None)

        Returns:
            Constraint object
        """
        if tier is None:
            tier = self.tier_map.get(name, ConstraintTier.SOFT_LOW)

        weight = self.weights.get(name, 0.0)
        satisfied = score >= 0.7  # 70% threshold for satisfaction

        return Constraint(
            name=name,
            tier=tier,
            weight=weight,
            score=score,
            satisfied=satisfied
        )

    def compute_utility(self, constraints: List[Constraint]) -> float:
        """
        Compute overall utility score.

        U = Σ w_i · S_i

        Args:
            constraints: List of constraints

        Returns:
            Utility score (0.0-1.0)
        """
        total_weight = sum(c.weight for c in constraints)

        if total_weight == 0:
            return 0.0

        weighted_sum = sum(c.evaluate() for c in constraints)

        return weighted_sum / total_weight

    def _evaluate_semantic_constraint(self, line: str, semantic_palette: Dict) -> float:
        """
        Evaluate semantic coherence with theme.

        Args:
            line: Line text
            semantic_palette: Semantic palette with theme concepts

        Returns:
            Score (0.0-1.0) indicating semantic alignment
        """
        if not semantic_palette or 'word_pools' not in semantic_palette:
            return 0.5  # Neutral score if no palette

        # Extract words from line
        words = [w.strip('.,!?;:\'\"').lower() for w in line.split()]
        if not words:
            return 0.5

        # Get embeddings for line words
        line_embeddings = []
        with get_session() as session:
            for word in words:
                sem = session.query(Semantics).filter_by(lemma=word).first()
                if sem and sem.embedding:
                    line_embeddings.append(np.array(sem.embedding))

        if not line_embeddings:
            return 0.5  # No embeddings available

        # Get theme words from palette word pools
        theme_words = []
        for motif_words in semantic_palette.get('word_pools', {}).values():
            theme_words.extend(motif_words[:10])  # Top 10 from each pool

        if not theme_words:
            return 0.5

        # Get embeddings for theme words
        theme_embeddings = []
        with get_session() as session:
            for word in theme_words[:30]:  # Limit to 30 theme words
                sem = session.query(Semantics).filter_by(lemma=word).first()
                if sem and sem.embedding:
                    theme_embeddings.append(np.array(sem.embedding))

        if not theme_embeddings:
            return 0.5

        # Compute average theme centroid
        theme_centroid = np.mean(theme_embeddings, axis=0)

        # Compute similarity of each line word to theme centroid
        similarities = []
        for line_emb in line_embeddings:
            dot_product = np.dot(line_emb, theme_centroid)
            norm_product = np.linalg.norm(line_emb) * np.linalg.norm(theme_centroid)

            if norm_product > 0:
                similarity = dot_product / norm_product
                similarities.append(max(0.0, similarity))

        # Return average similarity
        return np.mean(similarities) if similarities else 0.5

    def _evaluate_affect_constraint(self, line: str, affect_profile: str) -> float:
        """
        Evaluate affect alignment with target profile.

        Args:
            line: Line text
            affect_profile: Target affect (e.g., "melancholic", "joyful")

        Returns:
            Score (0.0-1.0) indicating affect alignment
        """
        if not affect_profile:
            return 1.0  # No constraint if no target affect

        # Extract words from line
        words = [w.strip('.,!?;:\'\"').lower() for w in line.split()]
        if not words:
            return 0.5

        # Get affect tags for each word
        matching_count = 0
        total_count = 0

        with get_session() as session:
            for word in words:
                sem = session.query(Semantics).filter_by(lemma=word).first()
                if sem and sem.affect_tags:
                    total_count += 1
                    # Check if any affect tag matches the target profile
                    if affect_profile in sem.affect_tags:
                        matching_count += 1

        # If no words have affect tags, return neutral score
        if total_count == 0:
            return 0.5

        # Return proportion of words matching target affect
        return matching_count / total_count

    def evaluate_line(self, line: str, target_spec: Dict) -> Dict[str, Constraint]:
        """
        Evaluate all constraints for a line.

        Args:
            line: Line text
            target_spec: Target specifications (rhyme, meter, semantic_palette, affect_profile, etc.)

        Returns:
            Dictionary of constraint name -> Constraint
        """
        from ..forms import MeterEngine, SoundEngine

        constraints = {}

        # Meter constraint
        if 'meter' in target_spec:
            meter_engine = MeterEngine()
            analysis = meter_engine.analyze_line(line, target_spec['meter'])

            meter_score = 1.0 - analysis.stress_deviation
            constraints['meter'] = self.create_constraint('meter', meter_score)

        # Rhyme constraint (if applicable)
        if 'rhyme_word' in target_spec and target_spec['rhyme_word']:
            sound_engine = SoundEngine()
            words = line.split()

            if words:
                last_word = words[-1].strip('.,!?;:')
                match = sound_engine.check_rhyme(target_spec['rhyme_word'], last_word)

                rhyme_score = match.similarity if match else 0.0
                constraints['rhyme'] = self.create_constraint('rhyme', rhyme_score)

        # Semantic constraint
        if 'semantic_palette' in target_spec:
            semantic_score = self._evaluate_semantic_constraint(
                line, target_spec['semantic_palette']
            )
            constraints['semantics'] = self.create_constraint('semantics', semantic_score)
        else:
            # Default neutral score if no palette
            constraints['semantics'] = self.create_constraint('semantics', 0.5)

        # Affect constraint
        if 'affect_profile' in target_spec:
            affect_score = self._evaluate_affect_constraint(
                line, target_spec['affect_profile']
            )
            constraints['affect'] = self.create_constraint('affect', affect_score)
        else:
            # Default high score if no affect requirement
            constraints['affect'] = self.create_constraint('affect', 1.0)

        return constraints

    def check_hard_constraints(self, constraints: List[Constraint]) -> bool:
        """
        Check if all hard constraints are satisfied.

        Args:
            constraints: List of constraints

        Returns:
            True if all hard constraints satisfied
        """
        for constraint in constraints:
            if constraint.tier == ConstraintTier.HARD and not constraint.satisfied:
                return False

        return True

    def get_violated_constraints(self, constraints: List[Constraint],
                                 min_score: float = 0.7) -> List[Constraint]:
        """
        Get list of violated constraints.

        Args:
            constraints: List of constraints
            min_score: Minimum score to be considered satisfied

        Returns:
            List of violated constraints
        """
        violated = []

        for constraint in constraints:
            if constraint.score < min_score:
                violated.append(constraint)

        # Sort by tier priority, then weight
        tier_order = {
            ConstraintTier.HARD: 0,
            ConstraintTier.SOFT_HIGH: 1,
            ConstraintTier.SOFT_MED: 2,
            ConstraintTier.SOFT_LOW: 3
        }

        violated.sort(key=lambda c: (tier_order[c.tier], -c.weight))

        return violated


class SteeringPolicy:
    """Defines behavior for constraint satisfaction."""

    def __init__(self, name: str, allow_slant: bool = True,
                 allow_pivot: bool = False, allow_breaks: bool = False,
                 max_repairs: int = 5):
        """
        Initialize steering policy.

        Args:
            name: Policy name
            allow_slant: Allow slant rhyme
            allow_pivot: Allow rhyme-class pivot
            allow_breaks: Allow controlled form-breaking
            max_repairs: Maximum repair iterations
        """
        self.name = name
        self.allow_slant = allow_slant
        self.allow_pivot = allow_pivot
        self.allow_breaks = allow_breaks
        self.max_repairs = max_repairs

    @classmethod
    def strict_sonnet(cls) -> 'SteeringPolicy':
        """Strict sonnet policy."""
        return cls(
            name="strict_sonnet",
            allow_slant=False,
            allow_pivot=False,
            allow_breaks=False,
            max_repairs=10
        )

    @classmethod
    def loose_tercet(cls) -> 'SteeringPolicy':
        """Loose tercet policy."""
        return cls(
            name="loose_tercet",
            allow_slant=True,
            allow_pivot=True,
            allow_breaks=False,
            max_repairs=5
        )

    @classmethod
    def free_verse(cls) -> 'SteeringPolicy':
        """Free verse policy."""
        return cls(
            name="free_verse",
            allow_slant=True,
            allow_pivot=True,
            allow_breaks=True,
            max_repairs=3
        )


def main():
    """CLI for constraint model testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Constraint model utilities")
    parser.add_argument(
        '--line',
        type=str,
        help='Line to evaluate'
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

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    model = ConstraintModel()

    if args.line:
        target_spec = {'meter': args.meter}

        if args.rhyme_word:
            target_spec['rhyme_word'] = args.rhyme_word

        constraints = model.evaluate_line(args.line, target_spec)

        print(f"\nConstraint Evaluation for: '{args.line}'")
        print("=" * 60)

        for name, constraint in constraints.items():
            status = "✓" if constraint.satisfied else "✗"
            print(f"{status} {name.upper()}: {constraint.score:.2f} "
                  f"(weight={constraint.weight:.2f}, tier={constraint.tier.value})")

        utility = model.compute_utility(list(constraints.values()))
        print(f"\nOverall Utility: {utility:.2f}")

        violated = model.get_violated_constraints(list(constraints.values()))

        if violated:
            print("\nViolated Constraints:")
            for c in violated:
                print(f"  - {c.name}: {c.score:.2f}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
