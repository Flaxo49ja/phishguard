import { describe, it, expect } from 'vitest';
import golden from './check_url_golden.json';
import { classifyUrl } from './classifier';

interface GoldenEntry {
  raw_input: string;
  response: {
    url: string;
    verdict: string;
    phishing_probability: number;
    features: Record<string, number>;
    benign_baseline_probability: number;
  };
}

interface GoldenFile {
  model: string;
  threshold: number;
  entries: GoldenEntry[];
}

const file = golden as GoldenFile;

describe('classifier — golden master parity with Python CLI (LogisticRegression)', () => {
  it('fixture is the LR model at threshold 0.5', () => {
    expect(file.model).toBe('LogisticRegression');
    expect(file.threshold).toBe(0.5);
  });

  it.each(file.entries)('$raw_input', ({ raw_input, response }) => {
    const result = classifyUrl(raw_input);
    expect(result.probability).toBeCloseTo(response.phishing_probability, 3);
    expect(result.verdict).toBe(response.verdict);
    expect(result.benignBaselineProbability).toBeCloseTo(response.benign_baseline_probability, 3);
    for (const [name, value] of Object.entries(response.features)) {
      const actual = result.allFeatures[name]?.value;
      const normalized = typeof actual === 'boolean' ? (actual ? 1 : 0) : actual;
      expect(normalized).toBe(value);
    }
  });
});
