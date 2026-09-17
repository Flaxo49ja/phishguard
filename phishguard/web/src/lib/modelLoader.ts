/**
 * Model Loader — runs the REAL trained LogisticRegression pipeline in the browser.
 *
 * The model was trained in Python (scikit-learn) on 107,355 real URLs
 * (PhishTank verified phishing + Tranco top-10k + ealvaradob benign deep links)
 * and exported to JSON by training/src/export_model.py.
 *
 * Inference here is mathematically identical to the Python pipeline:
 *   z = bias + sum_i( w_i * (x_i - mean_i) / std_i )
 *   p = sigmoid(z)
 */

import lrModelJson from '../model/lrModel.json';
import rfImportancesJson from '../model/rfFeatureImportances.json';
import { extractFeatures } from './features';

export interface ExportedModel {
  kind: string;
  featureNames: string[];
  scaler: { means: number[]; stds: number[] };
  weights: number[];
  bias: number;
  threshold: number;
  meta: {
    /** Metrics live in the top-level `metrics` block, read from reports/training_report.json at export time. */
    source: string;
    trainedOn: string;
    exportedAt: string;
  };
  /** Full training metrics blob — see phishing-detector/src/export_model.py. */
  metrics: {
    datasetLabel: string;
    nSamples: number | null;
    nPhishing: number | null;
    nLegitimate: number | null;
    testSetSize: number | null;
    logisticRegression: {
      precision: number | null;
      recall: number | null;
      f1: number | null;
      rocAuc: number | null;
      cvF1?: string;
    };
    randomForest: {
      precision: number | null;
      recall: number | null;
      f1: number | null;
      rocAuc: number | null;
      cvF1?: string;
      confusion?: { tn: number; fp: number; fn: number; tp: number };
    };
  } | null;
}

export interface Contribution {
  feature: string;
  value: number;
  /** base_prob - prob_without_this_feature (positive = pushed toward phishing) */
  contribution: number;
}

export interface RealPrediction {
  probability: number;
  features: Record<string, number | boolean>;
  contributions: Contribution[];
  benignBaselineProbability: number;
}

export const LR_MODEL = lrModelJson as ExportedModel;
export const RF_IMPORTANCES = rfImportancesJson as {
  kind: string;
  note: string;
  testF1: number | null;
  testRocAuc: number | null;
  importances: Record<string, number>;
};

/**
 * Real metrics from the Python training run — derived from the exported JSON
 * (which export_model.py reads live from reports/training_report.json), so
 * numbers can never drift from the trained model. Falls back to zeros/nulls
 * if the export was made without a training report.
 */
export interface ModelMetrics {
  precision: number | null;
  recall: number | null;
  f1: number | null;
  rocAuc: number | null;
  cvF1?: string;
  confusion?: { tn: number; fp: number; fn: number; tp: number };
}

export const REAL_METRICS: {
  dataset: { name: string; totalUrls: number; phishing: number; legitimate: number; testSetSize: number };
  logisticRegression: ModelMetrics;
  randomForest: ModelMetrics;
} = {
  dataset: {
    name: LR_MODEL.metrics?.datasetLabel ?? 'unknown dataset',
    totalUrls: LR_MODEL.metrics?.nSamples ?? 0,
    phishing: LR_MODEL.metrics?.nPhishing ?? 0,
    legitimate: LR_MODEL.metrics?.nLegitimate ?? 0,
    testSetSize: LR_MODEL.metrics?.testSetSize ?? 0,
  },
  logisticRegression: LR_MODEL.metrics?.logisticRegression ?? {
    precision: null,
    recall: null,
    f1: null,
    rocAuc: null,
  },
  randomForest: LR_MODEL.metrics?.randomForest ?? {
    precision: null,
    recall: null,
    f1: null,
    rocAuc: null,
  },
};

// Benign-typical reference values — mirrors _BENIGN_REFERENCE in check_url.py
const BENIGN_REFERENCE: Record<string, number> = {
  url_length: 45.0,
  hostname_length: 15.0,
  path_length: 10.0,
  num_dots: 2.0,
  num_hyphens: 0.0,
  num_underscores: 0.0,
  num_slashes: 2.0,
  num_digits: 0.0,
  num_special_chars: 0.0,
  has_at_symbol: 0.0,
  has_ip_address: 0.0,
  num_subdomains: 1.0,
  uses_https: 1.0,
  has_https_token_in_path: 0.0,
  is_shortened_url: 0.0,
  url_entropy: 3.3,
  tld_in_subdomain: 0.0,
  digit_letter_ratio: 0.03,
};

function sigmoid(z: number): number {
  const clamped = Math.max(-500, Math.min(500, z));
  return 1 / (1 + Math.exp(-clamped));
}

/** Feature vector in the model's feature order, as plain numbers. */
function featureVector(features: Record<string, number | boolean>): number[] {
  return LR_MODEL.featureNames.map((name) => {
    const v = features[name];
    return typeof v === 'boolean' ? (v ? 1 : 0) : (v as number);
  });
}

/** Probability from a raw (unstandardized) feature vector. */
function predictRawVector(x: number[]): number {
  let z = LR_MODEL.bias;
  for (let j = 0; j < x.length; j++) {
    const standardized = (x[j] - LR_MODEL.scaler.means[j]) / LR_MODEL.scaler.stds[j];
    z += LR_MODEL.weights[j] * standardized;
  }
  return sigmoid(z);
}

/**
 * Classify a URL with the real exported pipeline and explain the verdict
 * via one-at-a-time occlusion (same method as the Python CLI):
 * contribution_i = p(full) - p(feature_i set to benign-typical value).
 */
export function predictWithRealModel(url: string): RealPrediction {
  const features = extractFeatures(url);
  const x = featureVector(features);
  const baseProb = predictRawVector(x);

  const contributions: Contribution[] = LR_MODEL.featureNames.map((name, j) => {
    const ref = BENIGN_REFERENCE[name];
    if (ref === undefined) {
      return { feature: name, value: x[j], contribution: 0 };
    }
    const xc = [...x];
    xc[j] = ref;
    const p = predictRawVector(xc);
    return {
      feature: name,
      value: x[j],
      contribution: Math.round((baseProb - p) * 10000) / 10000,
    };
  });

  contributions.sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));

  // Probability if every feature were benign-typical (counterfactual URL)
  const benignX = LR_MODEL.featureNames.map((n) => BENIGN_REFERENCE[n] ?? 0);
  const benignProb = predictRawVector(benignX);

  return {
    probability: baseProb,
    features,
    contributions,
    benignBaselineProbability: benignProb,
  };
}
