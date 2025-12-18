"""
Integration tests for end-to-end poem generation.

Tests the complete pipeline from database setup through final poem output.
"""

import pytest
import logging
from typing import List

from src.generation import (
    GenerationSpec,
    PoemGenerator,
    create_default_spec
)
from src.forms import FormLibrary, MeterEngine, SoundEngine
from src.metrics import MetricsAnalyzer
from src.database import get_session, WordRecord

logger = logging.getLogger(__name__)


class TestEndToEndGeneration:
    """Test complete generation pipeline."""

    @pytest.fixture
    def generator(self):
        """Create poem generator."""
        return PoemGenerator()

    @pytest.fixture
    def form_library(self):
        """Create form library."""
        return FormLibrary()

    @pytest.fixture
    def metrics_analyzer(self):
        """Create metrics analyzer."""
        return MetricsAnalyzer()

    def test_haiku_generation(self, generator):
        """Test haiku generation."""
        spec = create_default_spec(form='haiku', theme='nature')

        poem = generator.generate(spec)

        assert poem is not None
        assert poem.text
        assert poem.spec.form == 'haiku'
        assert poem.run_id

        # Should have 3 lines
        lines = poem.text.strip().split('\n')
        assert len(lines) == 3

        logger.info(f"Generated haiku:\n{poem.text}")

    def test_sonnet_generation(self, generator):
        """Test sonnet generation."""
        spec = create_default_spec(form='sonnet', theme='love')

        poem = generator.generate(spec)

        assert poem is not None
        assert poem.text
        assert poem.spec.form == 'sonnet'

        # Should have 14 lines
        lines = poem.text.strip().split('\n')
        assert len([l for l in lines if l.strip()]) == 14

        logger.info(f"Generated sonnet:\n{poem.text}")

    def test_villanelle_generation(self, generator):
        """Test villanelle generation."""
        spec = create_default_spec(form='villanelle', theme='time')

        poem = generator.generate(spec)

        assert poem is not None
        assert poem.text
        assert poem.spec.form == 'villanelle'

        # Should have 19 lines
        lines = poem.text.strip().split('\n')
        assert len([l for l in lines if l.strip()]) == 19

        logger.info(f"Generated villanelle:\n{poem.text}")

    def test_preset_melancholic_nature(self, generator):
        """Test melancholic nature preset."""
        spec = GenerationSpec.preset_melancholic_nature()

        poem = generator.generate(spec)

        assert poem is not None
        assert poem.text
        assert 'nature' in spec.domain_tags
        assert spec.affect_profile == 'melancholic'

    def test_preset_joyful_simple(self, generator):
        """Test joyful simple preset."""
        spec = GenerationSpec.preset_joyful_simple()

        poem = generator.generate(spec)

        assert poem is not None
        assert poem.text
        assert spec.affect_profile == 'joyful'
        assert spec.max_rarity < 0.8  # Should prefer common words

    def test_preset_mysterious_archaic(self, generator):
        """Test mysterious archaic preset."""
        spec = GenerationSpec.preset_mysterious_archaic()

        poem = generator.generate(spec)

        assert poem is not None
        assert poem.text
        assert spec.min_rarity > 0.7  # Should prefer rare words

    def test_meter_validation(self, generator, form_library, metrics_analyzer):
        """Test meter compliance in generated poems."""
        spec = create_default_spec(form='sonnet', theme='nature')
        poem = generator.generate(spec)

        lines = [l.strip() for l in poem.text.split('\n') if l.strip()]

        # Get form spec
        form = form_library.get_form('sonnet')
        form_spec = {
            'meter': form.meter_pattern,
            'rhyme_pattern': form.rhyme_pattern
        }

        metrics = metrics_analyzer.analyze_poem(lines, form_spec)

        # Meter score should be reasonable
        assert metrics.meter.score >= 0.3  # At least 30%
        assert 0.0 <= metrics.meter.foot_accuracy <= 1.0

        logger.info(f"Meter score: {metrics.meter.score:.2f}, "
                   f"Foot accuracy: {metrics.meter.foot_accuracy:.2%}")

    def test_rhyme_validation(self, generator, form_library, metrics_analyzer):
        """Test rhyme compliance in generated poems."""
        spec = create_default_spec(form='sonnet', theme='nature')
        poem = generator.generate(spec)

        lines = [l.strip() for l in poem.text.split('\n') if l.strip()]

        # Get form spec
        form = form_library.get_form('sonnet')
        form_spec = {
            'meter': form.meter_pattern,
            'rhyme_pattern': form.rhyme_pattern
        }

        metrics = metrics_analyzer.analyze_poem(lines, form_spec)

        # Rhyme score should be reasonable
        assert metrics.rhyme.score >= 0.3  # At least 30%
        assert 0.0 <= metrics.rhyme.density <= 1.0

        logger.info(f"Rhyme score: {metrics.rhyme.score:.2f}, "
                   f"Density: {metrics.rhyme.density:.2%}")

    def test_semantic_coherence(self, generator, form_library, metrics_analyzer):
        """Test semantic coherence in generated poems."""
        spec = create_default_spec(form='haiku', theme='nature')
        poem = generator.generate(spec)

        lines = [l.strip() for l in poem.text.split('\n') if l.strip()]

        # Get form spec
        form = form_library.get_form('haiku')
        form_spec = {
            'meter': form.meter_pattern,
            'rhyme_pattern': form.rhyme_pattern
        }

        metrics = metrics_analyzer.analyze_poem(lines, form_spec)

        # Semantic score should be reasonable
        assert metrics.semantic.score >= 0.3  # At least 30%
        assert 0.0 <= metrics.semantic.theme_coherence <= 1.0

        logger.info(f"Semantic score: {metrics.semantic.score:.2f}, "
                   f"Theme coherence: {metrics.semantic.theme_coherence:.2%}")

    def test_custom_constraint_weights(self, generator):
        """Test custom constraint weights."""
        spec = create_default_spec(form='haiku', theme='nature')

        # Emphasize rhyme over meter
        spec.constraint_weights['rhyme'] = 0.5
        spec.constraint_weights['meter'] = 0.1

        poem = generator.generate(spec)

        assert poem is not None
        assert poem.text

    def test_rarity_range(self, generator):
        """Test rarity range constraints."""
        # High rarity words
        spec_rare = create_default_spec(form='haiku', theme='nature')
        spec_rare.min_rarity = 0.8
        spec_rare.max_rarity = 1.0

        poem_rare = generator.generate(spec_rare)
        assert poem_rare is not None

        # Low rarity words
        spec_common = create_default_spec(form='haiku', theme='nature')
        spec_common.min_rarity = 0.0
        spec_common.max_rarity = 0.3

        poem_common = generator.generate(spec_common)
        assert poem_common is not None

        # Poems should be different
        assert poem_rare.text != poem_common.text

    def test_temperature_variation(self, generator):
        """Test temperature effects on generation."""
        # Deterministic (temp=0)
        spec_det = create_default_spec(form='haiku', theme='nature')
        spec_det.temperature = 0.0

        poem1 = generator.generate(spec_det)
        poem2 = generator.generate(spec_det)

        # Should generate identical poems
        assert poem1.text == poem2.text

        # Random (temp=1)
        spec_rand = create_default_spec(form='haiku', theme='nature')
        spec_rand.temperature = 1.0

        poem3 = generator.generate(spec_rand)
        poem4 = generator.generate(spec_rand)

        # Likely to be different (not guaranteed)
        # Just check they're valid
        assert poem3 is not None
        assert poem4 is not None


class TestDatabaseIntegration:
    """Test database operations."""

    def test_database_connectivity(self):
        """Test database session creation."""
        with get_session() as session:
            assert session is not None

    def test_word_record_query(self):
        """Test querying word records."""
        with get_session() as session:
            # Query any word
            word = session.query(WordRecord).first()

            # May be None if database is empty
            if word:
                assert hasattr(word, 'lemma')
                assert hasattr(word, 'pos_primary')
                assert hasattr(word, 'syllable_count')
                logger.info(f"Sample word: {word.lemma} ({word.pos_primary})")

    def test_word_record_filters(self):
        """Test filtering word records."""
        with get_session() as session:
            # Query with filters
            query = session.query(WordRecord).filter(
                WordRecord.pos_primary == 'noun',
                WordRecord.syllable_count == 2
            )

            results = query.limit(10).all()

            # May be empty if database not populated
            for word in results:
                assert word.pos_primary == 'noun'
                assert word.syllable_count == 2
                logger.info(f"2-syllable noun: {word.lemma}")


class TestFormValidation:
    """Test form specification validation."""

    @pytest.fixture
    def form_library(self):
        """Create form library."""
        return FormLibrary()

    def test_load_all_forms(self, form_library):
        """Test loading all form definitions."""
        forms = ['haiku', 'sonnet', 'villanelle']

        for form_id in forms:
            form = form_library.get_form(form_id)
            assert form is not None
            assert form.name
            assert form.total_lines > 0
            logger.info(f"Loaded form: {form.name} ({form.total_lines} lines)")

    def test_haiku_structure(self, form_library):
        """Test haiku structure."""
        haiku = form_library.get_form('haiku')

        assert haiku.total_lines == 3
        assert len(haiku.stanza_specs) == 1
        assert haiku.special_rules.get('syllable_pattern') == [5, 7, 5]

    def test_sonnet_structure(self, form_library):
        """Test sonnet structure."""
        sonnet = form_library.get_form('sonnet')

        assert sonnet.total_lines == 14
        assert len(sonnet.stanza_specs) == 4  # 3 quatrains + 1 couplet
        assert sonnet.rhyme_pattern == 'ABAB CDCD EFEF GG'

    def test_villanelle_structure(self, form_library):
        """Test villanelle structure."""
        villanelle = form_library.get_form('villanelle')

        assert villanelle.total_lines == 19
        assert len(villanelle.stanza_specs) == 6  # 5 tercets + 1 quatrain


class TestMeterEngine:
    """Test meter analysis."""

    @pytest.fixture
    def meter_engine(self):
        """Create meter engine."""
        return MeterEngine()

    def test_iambic_pentameter(self, meter_engine):
        """Test iambic pentameter analysis."""
        line = "Shall I compare thee to a summer's day"

        analysis = meter_engine.analyze_line(line, 'iambic_pentameter')

        assert analysis is not None
        assert analysis.syllable_count == 10
        assert 0.0 <= analysis.foot_accuracy <= 1.0

        logger.info(f"Iambic pentameter: {line}")
        logger.info(f"  Syllables: {analysis.syllable_count}")
        logger.info(f"  Foot accuracy: {analysis.foot_accuracy:.2%}")

    def test_iambic_tetrameter(self, meter_engine):
        """Test iambic tetrameter analysis."""
        line = "The curfew tolls the knell of day"

        analysis = meter_engine.analyze_line(line, 'iambic_tetrameter')

        assert analysis is not None
        assert 0.0 <= analysis.foot_accuracy <= 1.0


class TestSoundEngine:
    """Test sound and rhyme analysis."""

    @pytest.fixture
    def sound_engine(self):
        """Create sound engine."""
        return SoundEngine()

    def test_perfect_rhyme(self, sound_engine):
        """Test perfect rhyme detection."""
        match = sound_engine.check_rhyme('day', 'way')

        assert match is not None
        assert match.similarity >= 0.95  # Perfect rhyme threshold

        logger.info(f"Rhyme: day/way = {match.similarity:.2%} ({match.rhyme_type})")

    def test_slant_rhyme(self, sound_engine):
        """Test slant rhyme detection."""
        match = sound_engine.check_rhyme('love', 'move')

        assert match is not None
        # May be slant or no rhyme depending on phonetics

        logger.info(f"Rhyme: love/move = {match.similarity:.2%} ({match.rhyme_type})")

    def test_no_rhyme(self, sound_engine):
        """Test non-rhyming words."""
        match = sound_engine.check_rhyme('day', 'night')

        # Should have low similarity
        assert match is None or match.similarity < 0.7


def test_suite_summary():
    """Print test suite summary."""
    logger.info("=" * 70)
    logger.info("INTEGRATION TEST SUITE")
    logger.info("=" * 70)
    logger.info("Tests:")
    logger.info("  - End-to-end poem generation (haiku, sonnet, villanelle)")
    logger.info("  - Preset configurations")
    logger.info("  - Meter validation")
    logger.info("  - Rhyme validation")
    logger.info("  - Semantic coherence")
    logger.info("  - Database operations")
    logger.info("  - Form specifications")
    logger.info("  - Meter analysis")
    logger.info("  - Sound/rhyme analysis")
    logger.info("=" * 70)


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, '-v', '-s'])
