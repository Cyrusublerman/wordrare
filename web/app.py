"""
WordRare Web Application

Flask-based REST API for poem generation and exploration.
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import logging
import os
import sys
from typing import Dict, Any, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.generation import (
    PoemGenerator,
    GenerationSpec,
    create_default_spec
)
from src.ui import (
    DictionaryBrowser,
    SemanticViewer,
    FormDebugger
)
from src.forms import FormLibrary
from src.metrics import MetricsAnalyzer
from src.database import get_session, WordRecord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__,
            static_folder='static',
            template_folder='templates')
CORS(app)

# Initialize components
generator = PoemGenerator()
form_library = FormLibrary()
metrics_analyzer = MetricsAnalyzer()
dictionary_browser = DictionaryBrowser()
semantic_viewer = SemanticViewer()


@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'WordRare API'
    })


@app.route('/api/forms', methods=['GET'])
def get_forms():
    """Get available poetic forms."""
    try:
        forms = ['haiku', 'sonnet', 'villanelle']
        form_data = []

        for form_id in forms:
            form = form_library.get_form(form_id)
            form_data.append({
                'id': form_id,
                'name': form.name,
                'lines': form.total_lines,
                'meter': form.meter_pattern,
                'rhyme_pattern': form.rhyme_pattern
            })

        return jsonify({
            'success': True,
            'forms': form_data
        })
    except Exception as e:
        logger.error(f"Error getting forms: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/generate', methods=['POST'])
def generate_poem():
    """
    Generate a poem.

    Expected JSON body:
    {
        "form": "haiku",
        "theme": "nature",
        "affect_profile": "melancholic",
        "min_rarity": 0.3,
        "max_rarity": 0.9,
        "rarity_bias": 0.6,
        "temperature": 0.7,
        "constraint_weights": {
            "meter": 0.25,
            "rhyme": 0.25
        }
    }
    """
    try:
        data = request.get_json()

        # Create generation spec
        form = data.get('form', 'haiku')
        theme = data.get('theme', 'nature')

        # Use preset or custom spec
        preset = data.get('preset')
        if preset == 'melancholic_nature':
            spec = GenerationSpec.preset_melancholic_nature()
        elif preset == 'joyful_simple':
            spec = GenerationSpec.preset_joyful_simple()
        elif preset == 'mysterious_archaic':
            spec = GenerationSpec.preset_mysterious_archaic()
        else:
            spec = create_default_spec(form=form, theme=theme)

        # Override with custom parameters
        if 'affect_profile' in data:
            spec.affect_profile = data['affect_profile']
        if 'min_rarity' in data:
            spec.min_rarity = float(data['min_rarity'])
        if 'max_rarity' in data:
            spec.max_rarity = float(data['max_rarity'])
        if 'rarity_bias' in data:
            spec.rarity_bias = float(data['rarity_bias'])
        if 'temperature' in data:
            spec.temperature = float(data['temperature'])
        if 'constraint_weights' in data:
            spec.constraint_weights.update(data['constraint_weights'])

        # Generate poem
        logger.info(f"Generating {form} poem with theme '{theme}'")
        poem = generator.generate(spec)

        if not poem:
            return jsonify({
                'success': False,
                'error': 'Failed to generate poem'
            }), 500

        # Analyze quality
        lines = [l.strip() for l in poem.text.split('\n') if l.strip()]
        form_obj = form_library.get_form(form)
        form_spec = {
            'meter': form_obj.meter_pattern,
            'rhyme_pattern': form_obj.rhyme_pattern
        }

        metrics = metrics_analyzer.analyze_poem(lines, form_spec)

        return jsonify({
            'success': True,
            'poem': {
                'text': poem.text,
                'form': poem.form_id,
                'run_id': poem.run_id,
                'lines': lines
            },
            'metrics': {
                'meter': {
                    'score': metrics.meter.score,
                    'foot_accuracy': metrics.meter.foot_accuracy,
                    'stability': metrics.meter.stability
                },
                'rhyme': {
                    'score': metrics.rhyme.score,
                    'density': metrics.rhyme.density,
                    'strictness': metrics.rhyme.strictness
                },
                'semantic': {
                    'score': metrics.semantic.score,
                    'coherence': metrics.semantic.theme_coherence,
                    'depth': metrics.semantic.depth
                },
                'total_score': metrics.total_score
            }
        })

    except Exception as e:
        logger.error(f"Error generating poem: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/words/search', methods=['GET'])
def search_words():
    """
    Search words in dictionary.

    Query parameters:
    - pos: Part of speech
    - min_rarity: Minimum rarity (0.0-1.0)
    - max_rarity: Maximum rarity (0.0-1.0)
    - syllables: Syllable count
    - domain_tag: Domain tag
    - limit: Maximum results (default 20)
    """
    try:
        # Get query parameters
        filters = {}
        if 'pos' in request.args:
            filters['pos'] = request.args['pos']
        if 'min_rarity' in request.args:
            filters['min_rarity'] = float(request.args['min_rarity'])
        if 'max_rarity' in request.args:
            filters['max_rarity'] = float(request.args['max_rarity'])
        if 'syllables' in request.args:
            filters['syllables'] = int(request.args['syllables'])
        if 'domain_tag' in request.args:
            filters['domain_tag'] = request.args['domain_tag']

        limit = int(request.args.get('limit', 20))

        # Search
        results = dictionary_browser.search(**filters)
        results = results[:limit]

        # Format results
        words = []
        for word in results:
            words.append({
                'lemma': word.lemma,
                'pos': word.pos_primary,
                'definition': word.definition_primary or '',
                'rarity': word.rarity_score or 0.0,
                'syllables': word.syllable_count or 0,
                'domain_tags': word.domain_tags or [],
                'affect_tags': word.affect_tags or []
            })

        return jsonify({
            'success': True,
            'count': len(words),
            'words': words
        })

    except Exception as e:
        logger.error(f"Error searching words: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/words/random', methods=['GET'])
def random_word():
    """Get a random word."""
    try:
        with get_session() as session:
            # Get random word
            from sqlalchemy.sql.expression import func
            word = session.query(WordRecord).order_by(func.random()).first()

            if not word:
                return jsonify({
                    'success': False,
                    'error': 'No words in database'
                }), 404

            return jsonify({
                'success': True,
                'word': {
                    'lemma': word.lemma,
                    'pos': word.pos_primary,
                    'definition': word.definition_primary or '',
                    'rarity': word.rarity_score or 0.0,
                    'syllables': word.syllable_count or 0,
                    'ipa': word.ipa or '',
                    'domain_tags': word.domain_tags or [],
                    'affect_tags': word.affect_tags or []
                }
            })

    except Exception as e:
        logger.error(f"Error getting random word: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/concepts/neighbors', methods=['GET'])
def get_concept_neighbors():
    """
    Get neighboring concepts.

    Query parameters:
    - concept: Concept name
    - depth: Search depth (default 1)
    """
    try:
        concept = request.args.get('concept')
        if not concept:
            return jsonify({
                'success': False,
                'error': 'Concept parameter required'
            }), 400

        depth = int(request.args.get('depth', 1))

        # Get neighborhood
        result = semantic_viewer.show_neighborhood(concept, depth)

        return jsonify({
            'success': True,
            'concept': concept,
            'depth': depth,
            'neighbors': result
        })

    except Exception as e:
        logger.error(f"Error getting neighbors: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/debug', methods=['POST'])
def debug_poem():
    """
    Debug a poem.

    Expected JSON body:
    {
        "text": "poem text with newlines",
        "form": "haiku"
    }
    """
    try:
        data = request.get_json()
        text = data.get('text', '')
        form = data.get('form', 'haiku')

        lines = [l.strip() for l in text.split('\n') if l.strip()]

        # Get form spec
        form_obj = form_library.get_form(form)
        form_spec = {
            'meter': form_obj.meter_pattern,
            'rhyme_pattern': form_obj.rhyme_pattern
        }

        # Analyze
        metrics = metrics_analyzer.analyze_poem(lines, form_spec)

        return jsonify({
            'success': True,
            'metrics': {
                'meter': {
                    'score': metrics.meter.score,
                    'foot_accuracy': metrics.meter.foot_accuracy,
                    'syllable_deviation': metrics.meter.syllable_deviation,
                    'stability': metrics.meter.stability
                },
                'rhyme': {
                    'score': metrics.rhyme.score,
                    'density': metrics.rhyme.density,
                    'strictness': metrics.rhyme.strictness,
                    'pattern_match': metrics.rhyme.pattern_match
                },
                'semantic': {
                    'score': metrics.semantic.score,
                    'coherence': metrics.semantic.theme_coherence,
                    'depth': metrics.semantic.depth,
                    'diversity': metrics.semantic.vocab_diversity
                },
                'total_score': metrics.total_score
            }
        })

    except Exception as e:
        logger.error(f"Error debugging poem: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Run development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
