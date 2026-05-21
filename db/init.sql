
-- Table des avis bruts
CREATE TABLE IF NOT EXISTS raw_reviews (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    source VARCHAR(50),
    checksum VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table des avis traites
CREATE TABLE IF NOT EXISTS processed_reviews (
    id SERIAL PRIMARY KEY,
    raw_id INTEGER REFERENCES raw_reviews(id) ON DELETE CASCADE,
    cleaned_text TEXT,
    sentiment VARCHAR(10),
    confidence FLOAT,
    model_version VARCHAR(50),
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table feedback
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    raw_id INTEGER REFERENCES raw_reviews(id) ON DELETE CASCADE,
    corrected_sentiment VARCHAR(10),
    user_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table des resultats agreges
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    source VARCHAR(50),
    total_reviews INTEGER DEFAULT 0,
    positive_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table des mots-cles
CREATE TABLE IF NOT EXISTS keywords (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL UNIQUE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO keywords (keyword, active) VALUES 
    ('restaurant Tunis', true),
    ('service client', true),
    ('qualite produit', true)
ON CONFLICT (keyword) DO NOTHING;

-- Table des parametres
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO settings (key, value, description) VALUES 
    ('neutral_threshold', '0.6', 'Seuil de confiance pour la categorie neutre'),
    ('active_model', 'distilbert-base-uncased-finetuned-sst-2-english', 'Modele actif pour l analyse'),
    ('batch_size', '16', 'Taille des lots pour l inference')
ON CONFLICT (key) DO NOTHING;

-- Table des logs
CREATE TABLE IF NOT EXISTS analysis_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    model_name VARCHAR(100),
    total_processed INTEGER,
    avg_confidence FLOAT,
    avg_latency_ms FLOAT,
    status VARCHAR(20)
);
