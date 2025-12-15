// WordRare Web Interface JavaScript

const API_BASE = '/api';

// DOM Elements
const generateBtn = document.getElementById('generate-btn');
const formSelect = document.getElementById('form-select');
const themeInput = document.getElementById('theme-input');
const affectSelect = document.getElementById('affect-select');
const minRaritySlider = document.getElementById('min-rarity');
const maxRaritySlider = document.getElementById('max-rarity');
const temperatureSlider = document.getElementById('temperature');
const loading = document.getElementById('loading');
const poemDisplay = document.getElementById('poem-display');
const metricsDisplay = document.getElementById('metrics-display');
const actionButtons = document.getElementById('action-buttons');
const copyBtn = document.getElementById('copy-btn');
const newBtn = document.getElementById('new-btn');
const searchBtn = document.getElementById('search-btn');
const randomBtn = document.getElementById('random-btn');
const wordSearch = document.getElementById('word-search');
const posFilter = document.getElementById('pos-filter');
const wordResults = document.getElementById('word-results');

// Current poem text
let currentPoemText = '';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateRarityLabel();
    updateTemperatureLabel();
    attachEventListeners();
});

// Event Listeners
function attachEventListeners() {
    generateBtn.addEventListener('click', generatePoem);
    copyBtn.addEventListener('click', copyToClipboard);
    newBtn.addEventListener('click', resetForm);
    searchBtn.addEventListener('click', searchWords);
    randomBtn.addEventListener('click', getRandomWord);

    minRaritySlider.addEventListener('input', updateRarityLabel);
    maxRaritySlider.addEventListener('input', updateRarityLabel);
    temperatureSlider.addEventListener('input', updateTemperatureLabel);

    // Preset buttons
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            loadPreset(btn.dataset.preset);
        });
    });

    // Enter key for word search
    wordSearch.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchWords();
    });
}

// Update Labels
function updateRarityLabel() {
    const min = parseFloat(minRaritySlider.value);
    const max = parseFloat(maxRaritySlider.value);

    // Ensure min <= max
    if (min > max) {
        minRaritySlider.value = max;
    }

    document.getElementById('rarity-value').textContent =
        `${minRaritySlider.value} - ${maxRaritySlider.value}`;
}

function updateTemperatureLabel() {
    document.getElementById('temperature-value').textContent =
        parseFloat(temperatureSlider.value).toFixed(2);
}

// Generate Poem
async function generatePoem() {
    // Show loading
    loading.style.display = 'block';
    poemDisplay.innerHTML = '';
    metricsDisplay.style.display = 'none';
    actionButtons.style.display = 'none';
    generateBtn.disabled = true;

    // Prepare request
    const request = {
        form: formSelect.value,
        theme: themeInput.value || 'nature',
        affect_profile: affectSelect.value,
        min_rarity: parseFloat(minRaritySlider.value),
        max_rarity: parseFloat(maxRaritySlider.value),
        temperature: parseFloat(temperatureSlider.value)
    };

    try {
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(request)
        });

        const data = await response.json();

        if (data.success) {
            displayPoem(data.poem);
            displayMetrics(data.metrics);
            actionButtons.style.display = 'flex';
        } else {
            showError(data.error || 'Failed to generate poem');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Network error. Please check your connection.');
    } finally {
        loading.style.display = 'none';
        generateBtn.disabled = false;
    }
}

// Display Poem
function displayPoem(poem) {
    currentPoemText = poem.text;

    poemDisplay.innerHTML = `
        <div class="poem-text">${poem.text}</div>
        <p style="margin-top: 20px; text-align: right; color: #999; font-style: italic;">
            — ${poem.form} (${poem.run_id})
        </p>
    `;
}

// Display Metrics
function displayMetrics(metrics) {
    metricsDisplay.style.display = 'block';

    // Update bars and values
    updateMetric('meter', metrics.meter.score);
    updateMetric('rhyme', metrics.rhyme.score);
    updateMetric('semantic', metrics.semantic.score);
    updateMetric('total', metrics.total_score);
}

function updateMetric(name, value) {
    const percentage = (value * 100).toFixed(0);
    document.getElementById(`${name}-bar`).style.width = `${percentage}%`;
    document.getElementById(`${name}-value`).textContent = `${percentage}%`;
}

// Copy to Clipboard
function copyToClipboard() {
    navigator.clipboard.writeText(currentPoemText).then(() => {
        const originalText = copyBtn.textContent;
        copyBtn.textContent = 'Copied!';
        setTimeout(() => {
            copyBtn.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Reset Form
function resetForm() {
    poemDisplay.innerHTML = '<p class="placeholder">Your generated poem will appear here.</p>';
    metricsDisplay.style.display = 'none';
    actionButtons.style.display = 'none';
    currentPoemText = '';
}

// Load Preset
function loadPreset(preset) {
    const presets = {
        melancholic_nature: {
            form: 'haiku',
            theme: 'nature',
            affect: 'melancholic',
            minRarity: 0.5,
            maxRarity: 0.95,
            temperature: 0.6
        },
        joyful_simple: {
            form: 'haiku',
            theme: 'joy',
            affect: 'joyful',
            minRarity: 0.1,
            maxRarity: 0.4,
            temperature: 0.8
        },
        mysterious_archaic: {
            form: 'sonnet',
            theme: 'mystery',
            affect: 'mysterious',
            minRarity: 0.85,
            maxRarity: 1.0,
            temperature: 0.7
        }
    };

    const config = presets[preset];
    if (!config) return;

    formSelect.value = config.form;
    themeInput.value = config.theme;
    affectSelect.value = config.affect;
    minRaritySlider.value = config.minRarity;
    maxRaritySlider.value = config.maxRarity;
    temperatureSlider.value = config.temperature;

    updateRarityLabel();
    updateTemperatureLabel();
}

// Search Words
async function searchWords() {
    const pos = posFilter.value;
    const minRarity = parseFloat(minRaritySlider.value);

    wordResults.innerHTML = '<p class="placeholder">Searching...</p>';

    try {
        const params = new URLSearchParams();
        if (pos) params.append('pos', pos);
        params.append('min_rarity', minRarity);
        params.append('limit', '10');

        const response = await fetch(`${API_BASE}/words/search?${params}`);
        const data = await response.json();

        if (data.success && data.words.length > 0) {
            displayWords(data.words);
        } else {
            wordResults.innerHTML = '<p class="placeholder">No words found.</p>';
        }
    } catch (error) {
        console.error('Error:', error);
        wordResults.innerHTML = '<p class="placeholder">Error searching words.</p>';
    }
}

// Get Random Word
async function getRandomWord() {
    wordResults.innerHTML = '<p class="placeholder">Getting random word...</p>';

    try {
        const response = await fetch(`${API_BASE}/words/random`);
        const data = await response.json();

        if (data.success) {
            displayWords([data.word]);
        } else {
            wordResults.innerHTML = '<p class="placeholder">No words available.</p>';
        }
    } catch (error) {
        console.error('Error:', error);
        wordResults.innerHTML = '<p class="placeholder">Error getting word.</p>';
    }
}

// Display Words
function displayWords(words) {
    wordResults.innerHTML = words.map(word => `
        <div class="word-card">
            <h4>${word.lemma}</h4>
            <div class="word-meta">
                <strong>${word.pos}</strong> |
                ${word.syllables} syllable${word.syllables !== 1 ? 's' : ''} |
                Rarity: ${(word.rarity * 100).toFixed(0)}%
            </div>
            <div class="word-definition">${word.definition || 'No definition available.'}</div>
            ${word.domain_tags && word.domain_tags.length > 0 ? `
                <div class="tags">
                    ${word.domain_tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
            ` : ''}
        </div>
    `).join('');
}

// Show Error
function showError(message) {
    poemDisplay.innerHTML = `
        <p style="color: #e74c3c; text-align: center;">
            <strong>Error:</strong> ${message}
        </p>
    `;
}
