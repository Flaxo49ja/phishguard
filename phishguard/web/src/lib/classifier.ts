/**
 * Phishing URL Classifier
 * Runs the REAL model trained in Python on 107,355 real URLs
 * (PhishTank + Tranco + ealvaradob benign) and exported to JSON.
 *
 * No in-browser training, no synthetic data — inference is identical
 * to the Python CLI pipeline (see modelLoader.ts).
 */

import { extractFeatures, getFeatureRisk, FEATURE_DESCRIPTIONS } from './features';
import { predictWithRealModel, LR_MODEL, REAL_METRICS, RF_IMPORTANCES } from './modelLoader';
import { SAMPLE_URLS as _SAMPLE_URLS } from './sampleUrls';

export { _SAMPLE_URLS as SAMPLE_URLS };
export { LR_MODEL, REAL_METRICS, RF_IMPORTANCES };

export interface ClassificationResult {
  verdict: 'PHISHING' | 'LEGITIMATE';
  probability: number;
  confidence: 'high' | 'medium' | 'low';
  topContributingFeatures: { feature: string; risk: string; value: number | boolean | string; contribution: number }[];
  allFeatures: Record<string, { value: number | boolean | string; risk: string }>;
  featureContributions: { feature: string; contribution: number; value: number }[];
  benignBaselineProbability: number;
}

/**
 * Kept as a no-op for backward compatibility — the model is pre-trained
 * and exported, so there is nothing to initialize anymore.
 */
export function initializeModel(): Promise<null> {
  return Promise.resolve(null);
}

/**
 * Classify a URL using the real exported pipeline.
 */
export function classifyUrl(url: string): ClassificationResult {
  const prediction = predictWithRealModel(url);
  const { probability, features, contributions, benignBaselineProbability } = prediction;

  // Determine verdict (same threshold as the Python CLI)
  const verdict = probability >= LR_MODEL.threshold ? 'PHISHING' : 'LEGITIMATE';

  // Confidence based on distance from decision boundary
  const distance = Math.abs(probability - 0.5);
  const confidence = distance > 0.3 ? 'high' : distance > 0.15 ? 'medium' : 'low';

  // Top contributing features (sorted by absolute contribution)
  const topContributingFeatures = contributions.slice(0, 5).map((c) => ({
    feature: c.feature,
    risk: getFeatureRisk(c.feature, features[c.feature]),
    value: features[c.feature],
    contribution: c.contribution,
  }));

  // Build all features map
  const allFeaturesMap: Record<string, { value: number | boolean | string; risk: string }> = {};
  for (const [name, value] of Object.entries(features)) {
    allFeaturesMap[name] = { value, risk: getFeatureRisk(name, value) };
  }

  return {
    verdict,
    probability: Math.round(probability * 1000) / 1000,
    confidence,
    topContributingFeatures,
    allFeatures: allFeaturesMap,
    featureContributions: contributions,
    benignBaselineProbability,
  };
}

/**
 * Validate if input looks like a URL
 */
export function isValidUrl(input: string): boolean {
  if (!input || input.trim().length === 0) return false;
  const trimmed = input.trim();
  const urlPattern = /^(https?:\/\/)?([\w-]+\.)+[\w-]+(\/[\w\-./?%&=]*)?$/i;
  return urlPattern.test(trimmed);
}

/**
 * Get feature descriptions (re-exported for convenience)
 */
export { FEATURE_DESCRIPTIONS };
