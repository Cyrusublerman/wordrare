# WordRare Web Interface - Quick Start

Get the WordRare web application running in under 5 minutes!

## Local Development (Fastest)

### Step 1: Install Dependencies

```bash
# Main dependencies
pip install -r requirements.txt

# Web dependencies
pip install -r web/requirements.txt
```

### Step 2: Initialize Database

```bash
python scripts/setup_databases.py
```

### Step 3: Run the Application

```bash
cd web
python app.py
```

🎉 **Done!** Visit http://localhost:5000

---

## Deploy to the Cloud (5 minutes)

### Option 1: Heroku (Recommended for beginners)

```bash
# Install Heroku CLI (if needed)
brew tap heroku/brew && brew install heroku  # macOS
# or download from: https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create and deploy
heroku create my-wordrare-app
git push heroku main

# Open in browser
heroku open
```

**Cost**: Free tier available (550 hours/month)

---

### Option 2: Railway (Fastest deployment)

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your WordRare repository
4. Click "Deploy"

**Cost**: $5 free credit, then ~$5/month

**Done in**: ~2 minutes

---

### Option 3: Render (Great free tier)

1. Go to https://render.com/
2. Click "New +" → "Web Service"
3. Connect GitHub repo
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `cd web && gunicorn app:app`
6. Click "Create Web Service"

**Cost**: Free tier (750 hours/month)

**Done in**: ~3 minutes

---

## Using the Web Interface

### Generate a Poem

1. **Select Form**: Choose Haiku, Sonnet, or Villanelle
2. **Enter Theme**: e.g., "nature", "love", "mystery"
3. **Adjust Rarity**: Slide between common (0.0) and rare (1.0) words
4. **Set Temperature**: Control randomness (0.0 = deterministic, 1.0 = creative)
5. **Click "Generate Poem"**

### Try Presets

Click any preset button:
- **Melancholic Nature**: Sad nature haiku with rare words
- **Joyful Simple**: Happy haiku with common words
- **Mysterious Archaic**: Mysterious sonnet with very rare words

### Explore Dictionary

1. Select a part of speech (noun, verb, etc.)
2. Click "Search" to find rare words
3. Click "Random Word" for inspiration

### Quality Metrics

After generation, view:
- **Meter Score**: How well it matches the meter pattern
- **Rhyme Score**: Rhyme scheme compliance
- **Semantic Score**: Theme coherence
- **Overall Score**: Combined quality

---

## Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
pip install -r web/requirements.txt
```

### "Database not found" error
```bash
python scripts/setup_databases.py
```

### Port 5000 already in use
```bash
# Change port in web/app.py:
app.run(host='0.0.0.0', port=5001)
```

### Slow generation
This is normal! Complex forms like sonnets take 5-10 seconds.
- Haiku: ~1 second
- Sonnet: ~5 seconds
- Villanelle: ~8 seconds

---

## Next Steps

### Populate the Database (Optional)

For better results, populate the database with rare words:

```bash
# Scrape Phrontistery (takes ~5 minutes)
python -m src.ingestion.phrontistery_scraper

# Enrich with definitions (takes ~30 minutes, requires API key)
export WORDNIK_API_KEY=your_key_here
python -m src.ingestion.dictionary_enricher

# Build semantic layer (takes ~10 minutes)
python -m src.semantic.word_record_builder
```

### Get a Wordnik API Key (Optional)

For dictionary definitions:
1. Sign up at https://www.wordnik.com/signup
2. Get API key at https://developer.wordnik.com/
3. Set environment variable:
   ```bash
   export WORDNIK_API_KEY=your_key_here
   ```

### Deploy to Production

See [WEB_DEPLOYMENT.md](WEB_DEPLOYMENT.md) for detailed deployment guides including:
- Custom domains
- HTTPS/SSL
- Database scaling (PostgreSQL)
- Performance optimization
- Monitoring

---

## Example Session

```bash
# Terminal 1: Start server
$ cd web && python app.py
 * Running on http://127.0.0.1:5000

# Terminal 2: Test API
$ curl http://localhost:5000/api/health
{"status": "healthy", "service": "WordRare API"}

$ curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"form": "haiku", "theme": "nature"}'

{
  "success": true,
  "poem": {
    "text": "Ancient willows weep\nMist-draped stones remember lost\nWhispers of the dawn",
    "form": "haiku"
  },
  "metrics": {
    "meter": {"score": 0.85},
    "rhyme": {"score": 0.0},
    "semantic": {"score": 0.78},
    "total_score": 0.54
  }
}
```

---

## API Reference

### Generate Poem
```bash
POST /api/generate
Content-Type: application/json

{
  "form": "haiku",
  "theme": "nature",
  "affect_profile": "melancholic",
  "min_rarity": 0.3,
  "max_rarity": 0.9,
  "temperature": 0.7
}
```

### Search Words
```bash
GET /api/words/search?pos=noun&min_rarity=0.8&limit=10
```

### Random Word
```bash
GET /api/words/random
```

---

## Tips for Best Results

1. **Start with Haiku**: Fastest and most reliable
2. **Use Presets**: Great starting points
3. **Adjust Rarity Gradually**: Start at 0.3-0.7, then experiment
4. **Higher Temperature = More Creative**: But less consistent
5. **Populate Database**: For better word variety

---

## Support

- **Documentation**: See [WEB_DEPLOYMENT.md](WEB_DEPLOYMENT.md)
- **Issues**: Check the console/logs for error messages
- **API Testing**: Use browser DevTools Network tab

---

**Enjoy generating rare poetry!** 🎭📝
