"""
Semantic tagging system - rule-based and embedding-based.

Derives domain tags, affect tags, imagery tags, and theme tags.
"""

import logging
from typing import List, Dict, Set, Optional
import re
from tqdm import tqdm
import numpy as np

from ..database import Semantics, Lexico, get_session
from .embedder import SemanticEmbedder

logger = logging.getLogger(__name__)


class SemanticTagger:
    """Tags words with domain, affect, imagery, and theme labels."""

    def __init__(self, use_embeddings: bool = True):
        """
        Initialize SemanticTagger.

        Args:
            use_embeddings: Whether to use embedding-based tagging
        """
        # Initialize tag seed sets
        self.domain_keywords = self._init_domain_keywords()
        self.affect_keywords = self._init_affect_keywords()
        self.imagery_keywords = self._init_imagery_keywords()
        self.theme_keywords = self._init_theme_keywords()
        self.register_keywords = self._init_register_keywords()

        # Initialize embedder for similarity-based tagging
        self.use_embeddings = use_embeddings
        self.embedder = None
        self.tag_embeddings = {}

        if use_embeddings:
            try:
                self.embedder = SemanticEmbedder()
                if self.embedder.model:
                    self._compute_tag_embeddings()
                else:
                    logger.warning("Embedder model not available - falling back to rule-based only")
                    self.use_embeddings = False
            except Exception as e:
                logger.warning(f"Could not initialize embedder: {e} - falling back to rule-based only")
                self.use_embeddings = False

    def _init_domain_keywords(self) -> Dict[str, List[str]]:
        """Initialize domain keyword mappings."""
        return {
            'medical': ['disease', 'symptom', 'treatment', 'anatomy', 'body', 'health',
                       'medicine', 'diagnosis', 'patient', 'physician', 'surgery'],
            'botanical': ['plant', 'flower', 'tree', 'leaf', 'root', 'seed', 'bloom',
                         'botanical', 'flora', 'vegetation', 'foliage'],
            'zoological': ['animal', 'beast', 'creature', 'fauna', 'species', 'mammal',
                          'bird', 'insect', 'reptile', 'fish'],
            'nautical': ['ship', 'sea', 'ocean', 'sailing', 'maritime', 'vessel',
                        'navigation', 'marine', 'sailor', 'port', 'wave'],
            'architectural': ['building', 'structure', 'column', 'arch', 'construction',
                            'edifice', 'architecture', 'design', 'facade'],
            'musical': ['music', 'sound', 'melody', 'rhythm', 'harmony', 'note',
                       'instrument', 'composition', 'musical'],
            'religious': ['god', 'divine', 'sacred', 'holy', 'religious', 'spiritual',
                         'worship', 'prayer', 'faith', 'church', 'temple'],
            'legal': ['law', 'legal', 'court', 'justice', 'contract', 'statute',
                     'judgment', 'tribunal', 'attorney'],
            'astronomical': ['star', 'planet', 'celestial', 'cosmos', 'astronomy',
                           'heavenly', 'solar', 'lunar', 'constellation'],
            'geological': ['rock', 'stone', 'mineral', 'earth', 'geological',
                          'sediment', 'crystal', 'formation'],
        }

    def _init_affect_keywords(self) -> Dict[str, List[str]]:
        """Initialize affect/emotion keyword mappings."""
        return {
            'melancholic': ['sad', 'sorrow', 'grief', 'melancholy', 'mournful', 'dejected',
                          'despondent', 'gloomy', 'doleful', 'wistful'],
            'joyful': ['happy', 'joy', 'delight', 'cheerful', 'merry', 'jubilant',
                      'elated', 'gleeful', 'blissful', 'ecstatic'],
            'fearful': ['fear', 'terror', 'dread', 'anxiety', 'frightening', 'scary',
                       'alarming', 'terrifying', 'ominous'],
            'angry': ['anger', 'rage', 'fury', 'wrath', 'indignant', 'irate',
                     'enraged', 'furious', 'wrathful'],
            'peaceful': ['peace', 'calm', 'serene', 'tranquil', 'placid', 'still',
                        'quiet', 'gentle', 'soothing'],
            'mysterious': ['mystery', 'enigma', 'obscure', 'cryptic', 'arcane',
                          'hidden', 'secret', 'esoteric'],
            'romantic': ['love', 'romance', 'passion', 'affection', 'tender',
                        'amorous', 'devoted', 'enamored'],
            'contemplative': ['thought', 'reflection', 'meditation', 'ponder',
                            'contemplation', 'introspection', 'musing'],
        }

    def _init_imagery_keywords(self) -> Dict[str, List[str]]:
        """Initialize imagery keyword mappings."""
        return {
            'visual': ['see', 'look', 'sight', 'view', 'visible', 'color', 'light',
                      'dark', 'bright', 'shadow', 'gleam', 'appearance'],
            'auditory': ['hear', 'sound', 'noise', 'voice', 'echo', 'silence',
                        'whisper', 'loud', 'quiet', 'resound'],
            'tactile': ['touch', 'feel', 'texture', 'rough', 'smooth', 'soft',
                       'hard', 'tangible', 'grasp'],
            'olfactory': ['smell', 'scent', 'odor', 'fragrance', 'aroma', 'perfume',
                         'stench', 'redolent'],
            'gustatory': ['taste', 'flavor', 'sweet', 'bitter', 'sour', 'savory',
                         'palatable', 'delicious'],
            'kinesthetic': ['move', 'motion', 'movement', 'dance', 'flow', 'swift',
                          'slow', 'graceful', 'agile'],
        }

    def _init_theme_keywords(self) -> Dict[str, List[str]]:
        """Initialize theme keyword mappings."""
        return {
            'nature': ['nature', 'natural', 'wild', 'wilderness', 'landscape',
                      'environment', 'earth', 'world'],
            'death': ['death', 'mortality', 'dying', 'mortal', 'deceased', 'demise',
                     'perish', 'fatal', 'grave', 'tomb'],
            'time': ['time', 'temporal', 'moment', 'eternity', 'past', 'present',
                    'future', 'age', 'duration', 'ephemeral'],
            'beauty': ['beauty', 'beautiful', 'lovely', 'fair', 'aesthetic',
                      'elegant', 'graceful', 'splendid'],
            'decay': ['decay', 'rot', 'deteriorate', 'decline', 'wither',
                     'crumble', 'erosion', 'ruin'],
            'power': ['power', 'strength', 'force', 'might', 'potent',
                     'dominance', 'authority', 'control'],
            'transformation': ['change', 'transform', 'metamorphosis', 'transition',
                             'evolution', 'transmute', 'convert'],
            'isolation': ['alone', 'solitary', 'isolated', 'lonely', 'separate',
                         'remote', 'detached', 'secluded'],
        }

    def _init_register_keywords(self) -> Dict[str, List[str]]:
        """Initialize register keyword mappings for extracting from labels."""
        return {
            'archaic': ['archaic', 'obsolete', 'dated', 'old-fashioned', 'historical'],
            'formal': ['formal', 'literary', 'technical', 'learned'],
            'informal': ['informal', 'colloquial', 'slang', 'vulgar', 'derogatory'],
            'poetic': ['poetic', 'rhetorical', 'figurative'],
            'rare': ['rare', 'uncommon', 'unusual'],
            'dialectal': ['dialect', 'regional', 'scottish', 'irish', 'american', 'british'],
        }

    def _compute_tag_embeddings(self):
        """Compute average embeddings for each tag category."""
        if not self.embedder or not self.embedder.model:
            return

        logger.info("Computing tag embeddings...")

        all_categories = {
            'domain': self.domain_keywords,
            'affect': self.affect_keywords,
            'imagery': self.imagery_keywords,
            'theme': self.theme_keywords
        }

        for category, tag_dict in all_categories.items():
            self.tag_embeddings[category] = {}

            for tag, keywords in tag_dict.items():
                # Encode all keywords and average
                keyword_text = ' '.join(keywords)
                embedding = self.embedder.encode(keyword_text)

                if embedding:
                    self.tag_embeddings[category][tag] = embedding

        logger.info(f"Tag embeddings computed for {sum(len(d) for d in self.tag_embeddings.values())} tags")

    def extract_register_tags(self, labels: List[str]) -> List[str]:
        """
        Extract register tags from lexico usage labels.

        Args:
            labels: Usage labels from lexico

        Returns:
            List of register tags
        """
        register_tags = set()
        labels_lower = ' '.join(labels).lower()

        for register, keywords in self.register_keywords.items():
            for keyword in keywords:
                if keyword in labels_lower:
                    register_tags.add(register)
                    break

        return list(register_tags)

    def rule_based_tag(self, word: str, definitions: List[str],
                      labels: List[str], examples: List[str] = None) -> Dict[str, List[str]]:
        """
        Apply rule-based tagging using keyword matching.

        Args:
            word: The word
            definitions: Definition strings
            labels: Usage labels
            examples: Example sentences

        Returns:
            Dictionary of tags by category
        """
        # Combine all text for analysis
        text = ' '.join([word] + definitions + labels)
        if examples:
            text += ' ' + ' '.join(examples[:3])

        text_lower = text.lower()

        tags = {
            'domain': set(),
            'affect': set(),
            'imagery': set(),
            'theme': set(),
            'register': set()
        }

        # Match domain tags
        for domain, keywords in self.domain_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    tags['domain'].add(domain)
                    break  # One match is enough

        # Match affect tags
        for affect, keywords in self.affect_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    tags['affect'].add(affect)
                    break

        # Match imagery tags
        for imagery, keywords in self.imagery_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    tags['imagery'].add(imagery)
                    break

        # Match theme tags
        for theme, keywords in self.theme_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    tags['theme'].add(theme)
                    break

        # Extract register tags from labels
        register_tags = self.extract_register_tags(labels)
        tags['register'].update(register_tags)

        return {k: list(v) for k, v in tags.items()}

    def embedding_based_tag(self, word_embedding: List[float],
                           tag_category: str,
                           threshold: float = 0.5) -> List[str]:
        """
        Apply embedding-based tagging using similarity to seed words.

        Args:
            word_embedding: Embedding vector for the word
            tag_category: Category to tag ('domain', 'affect', 'imagery', 'theme')
            threshold: Similarity threshold for tagging

        Returns:
            List of tags
        """
        if not self.use_embeddings or not word_embedding:
            return []

        if tag_category not in self.tag_embeddings:
            return []

        tags = []
        word_emb = np.array(word_embedding)

        # Compare to each tag's embedding
        for tag, tag_embedding in self.tag_embeddings[tag_category].items():
            tag_emb = np.array(tag_embedding)

            # Compute cosine similarity
            dot_product = np.dot(word_emb, tag_emb)
            norm_product = np.linalg.norm(word_emb) * np.linalg.norm(tag_emb)

            if norm_product > 0:
                similarity = dot_product / norm_product

                if similarity >= threshold:
                    tags.append(tag)

        return tags

    def tag_word(self, lemma: str, lexico_data: Dict,
                semantics_data: Dict = None) -> Dict[str, List[str]]:
        """
        Tag a word using both rule-based and embedding-based methods.

        Args:
            lemma: The word
            lexico_data: Dictionary data
            semantics_data: Existing semantics data (optional)

        Returns:
            Dictionary of tags
        """
        definitions = lexico_data.get('definitions', [])
        labels = lexico_data.get('labels_raw', [])
        examples = lexico_data.get('examples', [])

        # Rule-based tagging
        rule_tags = self.rule_based_tag(lemma, definitions, labels, examples)

        # Embedding-based tagging (if embedding available)
        embedding_tags = {
            'domain': [],
            'affect': [],
            'imagery': [],
            'theme': []
        }

        if self.use_embeddings and semantics_data and 'embedding' in semantics_data:
            word_embedding = semantics_data['embedding']

            if word_embedding:
                # Tag each category with embeddings (lower threshold for complementary tagging)
                for category in ['domain', 'affect', 'imagery', 'theme']:
                    emb_tags = self.embedding_based_tag(word_embedding, category, threshold=0.6)
                    embedding_tags[category] = emb_tags

        # Combine rule-based and embedding-based tags (union)
        combined_tags = {
            'domain_tags': list(set(rule_tags['domain'] + embedding_tags['domain'])),
            'affect_tags': list(set(rule_tags['affect'] + embedding_tags['affect'])),
            'imagery_tags': list(set(rule_tags['imagery'] + embedding_tags['imagery'])),
            'theme_tags': list(set(rule_tags['theme'] + embedding_tags['theme'])),
            'register_tags': rule_tags['register']  # Register comes only from rule-based
        }

        return combined_tags

    def tag_from_lexico(self, limit: Optional[int] = None, batch_size: int = 100):
        """
        Tag words from lexico table.

        Args:
            limit: Maximum number of words to tag
            batch_size: Number of words to process before committing
        """
        with get_session() as session:
            query = session.query(Lexico)

            if limit:
                query = query.limit(limit)

            lexico_entries = query.all()

        logger.info(f"Tagging {len(lexico_entries)} words...")

        tagged = 0
        batch_count = 0

        with get_session() as session:
            for entry in tqdm(lexico_entries, desc="Tagging words"):
                lexico_data = {
                    'definitions': entry.definitions,
                    'examples': entry.examples,
                    'labels_raw': entry.labels_raw or []
                }

                # Get existing semantics data (for embedding)
                existing_sem = session.query(Semantics).filter_by(lemma=entry.lemma).first()
                semantics_data = None

                if existing_sem and existing_sem.embedding:
                    semantics_data = {'embedding': existing_sem.embedding}

                # Tag the word
                tags = self.tag_word(entry.lemma, lexico_data, semantics_data)

                # Update semantics table
                if existing_sem:
                    # Update tags
                    existing_sem.domain_tags = tags['domain_tags']
                    existing_sem.affect_tags = tags['affect_tags']
                    existing_sem.imagery_tags = tags['imagery_tags']
                    existing_sem.theme_tags = tags['theme_tags']
                    existing_sem.register_tags = tags['register_tags']
                else:
                    # Create new entry
                    semantics_entry = Semantics(
                        lemma=entry.lemma,
                        domain_tags=tags['domain_tags'],
                        affect_tags=tags['affect_tags'],
                        imagery_tags=tags['imagery_tags'],
                        theme_tags=tags['theme_tags'],
                        register_tags=tags['register_tags'],
                        embedding=None,
                        synonyms=[],
                        antonyms=[],
                        hypernyms=[],
                        hyponyms=[]
                    )
                    session.add(semantics_entry)

                tagged += 1
                batch_count += 1

                # Commit in batches
                if batch_count >= batch_size:
                    session.commit()
                    batch_count = 0
                    logger.debug(f"Committed batch at {tagged} words")

            # Commit remaining
            if batch_count > 0:
                session.commit()
                logger.debug("Committed final batch")

        logger.info(f"Tagging complete: {tagged} words tagged")

    def get_tag_statistics(self) -> Dict:
        """
        Get statistics about tag distribution.

        Returns:
            Dictionary of tag counts
        """
        with get_session() as session:
            all_semantics = session.query(Semantics).all()

        stats = {
            'domain': {},
            'affect': {},
            'imagery': {},
            'theme': {}
        }

        for sem in all_semantics:
            for tag in sem.domain_tags or []:
                stats['domain'][tag] = stats['domain'].get(tag, 0) + 1

            for tag in sem.affect_tags or []:
                stats['affect'][tag] = stats['affect'].get(tag, 0) + 1

            for tag in sem.imagery_tags or []:
                stats['imagery'][tag] = stats['imagery'].get(tag, 0) + 1

            for tag in sem.theme_tags or []:
                stats['theme'][tag] = stats['theme'].get(tag, 0) + 1

        return stats


def main():
    """Command-line interface for tagging."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Tag words semantically")
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of words to tag'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show tag statistics'
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    tagger = SemanticTagger()

    if args.stats:
        stats = tagger.get_tag_statistics()
        print("\nTag Statistics:")
        print(json.dumps(stats, indent=2))
    else:
        tagger.tag_from_lexico(limit=args.limit)


if __name__ == "__main__":
    main()
