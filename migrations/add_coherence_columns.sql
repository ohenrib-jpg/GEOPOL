-- Migration pour l'analyse cohérente par lots
-- Ajout des colonnes nécessaires à la table articles

-- 1. Ajout de la colonne pour marquer les articles harmonisés
ALTER TABLE articles ADD COLUMN harmonized INTEGER DEFAULT 0;

-- 2. Ajout de la colonne pour la taille du cluster
ALTER TABLE articles ADD COLUMN cluster_size INTEGER DEFAULT 1;

-- 3. Ajout de la colonne pour la confiance bayésienne
ALTER TABLE articles ADD COLUMN bayesian_confidence REAL;

-- 4. Ajout de la colonne pour le nombre d'évidences bayésiennes
ALTER TABLE articles ADD COLUMN bayesian_evidence_count INTEGER DEFAULT 0;

-- 5. Ajout de la colonne pour les métadonnées d'analyse
ALTER TABLE articles ADD COLUMN analysis_metadata TEXT;

-- 6. Création d'index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_articles_harmonized ON articles(harmonized);
CREATE INDEX IF NOT EXISTS idx_articles_cluster_size ON articles(cluster_size);
CREATE INDEX IF NOT EXISTS idx_articles_bayesian_confidence ON articles(bayesian_confidence);

-- 7. Création d'une vue pour les statistiques rapides
CREATE VIEW IF NOT EXISTS v_sentiment_statistics AS
SELECT 
    sentiment_type,
    COUNT(*) as count,
    AVG(sentiment_score) as avg_score,
    AVG(bayesian_confidence) as avg_confidence,
    SUM(CASE WHEN harmonized = 1 THEN 1 ELSE 0 END) as harmonized_count,
    AVG(cluster_size) as avg_cluster_size
FROM articles
GROUP BY sentiment_type;

-- 8. Création d'une vue pour les clusters
CREATE VIEW IF NOT EXISTS v_cluster_analysis AS
SELECT 
    cluster_size,
    COUNT(*) as article_count,
    COUNT(DISTINCT sentiment_type) as sentiment_diversity,
    AVG(bayesian_confidence) as avg_confidence
FROM articles
WHERE cluster_size > 1
GROUP BY cluster_size
ORDER BY cluster_size DESC;

-- 9. Mise à jour des articles existants (optionnel)
-- Initialiser harmonized à 0 pour tous les articles existants
UPDATE articles SET harmonized = 0 WHERE harmonized IS NULL;

-- 10. Initialiser cluster_size à 1 pour tous les articles existants
UPDATE articles SET cluster_size = 1 WHERE cluster_size IS NULL;

-- Vérification
SELECT 
    'Migration terminée' as status,
    COUNT(*) as total_articles,
    SUM(CASE WHEN harmonized = 1 THEN 1 ELSE 0 END) as harmonized_articles
FROM articles;