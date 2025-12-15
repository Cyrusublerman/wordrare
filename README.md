# WordRare - Rare Poem Generation System

A sophisticated procedural poetry generation system that creates poems using rare words enriched with phonetic, semantic, and poetic-structure metadata.

## Overview

WordRare generates high-quality poetry by combining:
- **Rare-word lexicon** from Phrontistery and other curated sources
- **Semantic intelligence** using embeddings and concept graphs
- **Phonetic analysis** for rhyme, meter, and sound devices
- **Poetic form engines** supporting sonnets, villanelles, haiku, and more
- **Constraint-based generation** with iterative refinement

## Features

### Core Capabilities
- Procedural poem generation with configurable forms and themes
- Rarity-based word selection for unique vocabulary
- Semantic coherence through concept graphs and embeddings
- Meter validation and repair (iambic, trochaic, anapestic, etc.)
- Rhyme classification (perfect, slant, internal)
- Sound device detection (alliteration, assonance, consonance)

### Poetic Forms Supported
- Sonnet (Shakespearean, Petrarchan)
- Villanelle
- Haiku
- Tanka
- Limerick
- Blank verse
- Free verse
- Custom forms via JSON specification

### Quality Metrics
- Meter accuracy and stability
- Rhyme density and strictness
- Semantic coherence and motif stability
- Information depth (rarity scoring)
- Multi-technique layering

## Project Structure

```
wordrare/
├── src/
│   ├── ingestion/          # Data scraping and enrichment
│   ├── semantic/           # Embeddings, tagging, concept graph
│   ├── phonetics/          # IPA, rhyme, meter analysis
│   ├── forms/              # Poetic form specifications
│   ├── generation/         # Poem generation engine
│   ├── constraints/        # Constraint model and repair
│   ├── metrics/            # Ranking and evaluation
│   └── ui/                 # Browsers, viewers, debuggers
├── data/
│   ├── raw/                # Source data (wordlists, corpora)
│   ├── processed/          # Enriched WORD_RECORDs
│   └── forms/              # Form specifications (JSON)
├── databases/              # SQLite/PostgreSQL databases
├── reports/                # Phase completion reports
├── tests/
├── BUildguide.md          # Detailed system architecture
├── IMPLEMENTATION_PLAN.md # Phase-by-phase implementation guide
└── README.md              # This file
```

## Getting Started

### Prerequisites
- Python 3.9+
- SQLite or PostgreSQL
- Node.js (for UI components)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/wordrare.git
cd wordrare

# Install Python dependencies
pip install -r requirements.txt

# Set up databases
python scripts/setup_databases.py

# Download required data sources
python scripts/download_data.py
```

### Quick Start

```python
from wordrare import PoemGenerator

# Initialize generator
generator = PoemGenerator()

# Generate a sonnet about nature
poem = generator.generate(
    form="sonnet",
    theme="nature",
    rarity_bias=0.7,
    affect_profile="contemplative"
)

print(poem.text)
print(f"Meter score: {poem.metrics.M_score}")
print(f"Rhyme score: {poem.metrics.R_score}")
```

## Documentation

- **[BuildGuide.md](BUildguide.md)** - Complete system architecture and design
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - Development roadmap
- **[API Documentation](docs/api.md)** - API reference (coming soon)
- **[Examples](examples/)** - Sample poems and usage patterns (coming soon)

## Data Sources

### Tier 1 (Required)
- [Phrontistery](http://phrontistery.info/) - Rare word lexicon
- [CMU Pronouncing Dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict) - Phonetics
- [Google Books Ngram](https://books.google.com/ngrams) - Frequency data
- Sentence-transformers - Semantic embeddings

### Tier 2 (Recommended)
- [Wordnik API](https://www.wordnik.com/) - Dictionary enrichment
- [Wiktionary](https://www.wiktionary.org/) - Archaic/obscure entries
- [WordNet](https://wordnet.princeton.edu/) - Lexical relations

## Development Status

Current implementation phase: **Phase 1 - Foundation & Data Pipeline**

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed progress and [reports/](reports/) for phase completion summaries.

## Architecture

The system is built around a unified **WORD_RECORD** structure that powers:
1. **Rarity-based selection** - Configurable preference for uncommon vocabulary
2. **Semantic coherence** - Thematic consistency via embeddings and concept graphs
3. **Meter/rhyme/sound devices** - Phonetic analysis for poetic structure

Key architectural decisions:
- Deterministic engines for structural validation
- LLM-assisted micro-editing with strict constraints
- Iterative repair with configurable quality/creativity tradeoffs

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Phrontistery for rare word collections
- CMU for the Pronouncing Dictionary
- classify-poetry project for form specifications
- Masterclass prosody resources

## Contact

Project maintained by [Your Name]
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com
