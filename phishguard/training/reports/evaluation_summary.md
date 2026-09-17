# Evaluation Summary — RandomForest

## Dataset

- Total URLs: 107355
- Phishing (positive): 48338 (45.0%)
- Legitimate (negative): 59017 (55.0%)
- Class imbalance ratio (phish/total): 0.450

## Metrics

| Metric       | Value   |
|--------------|---------|
| Precision    | 0.8885 |
| Recall       | 0.8872 |
| F1 Score     | 0.8878 |
| ROC-AUC      | 0.9545303158306595 |
| Model        | RandomForest |

## Confusion Matrix

|                     | Predicted Legit | Predicted Phish |
|---------------------|-----------------|-----------------|
| **Actual Legit**    | 10727 (TN)       | 1076 (FP)       |
| **Actual Phish**    | 1091 (FN)       | 8577 (TP)       |

## Precision/Recall Trade-off — Ethical Considerations

- **False Positives (FP = 1076):** Legitimate URLs flagged as phishing.
  Cost: *inconvenience* — a real site is blocked, users may lose trust
  or be unable to access a service. In high-stakes contexts (e.g. banking,
  healthcare portals) this can be severe.

- **False Negatives (FN = 1091):** Phishing URLs classified as legitimate.
  Cost: *security risk* — a user may be tricked into entering credentials
  or downloading malware. This is the more dangerous error type.

- **Recall = 0.8872** means we catch 88.7% of phishing URLs.
  With 1091 missed phishing URLs out of 48338 total, each miss
  represents a potential victim.

- **Precision = 0.8885** means when we flag a URL as phishing,
  we are correct 88.9% of the time. The remaining
  1076 false positives are a nuisance but far less costly than a miss.

- **Class imbalance** was handled with `class_weight="balanced"` during
  training. The dataset has a phishing ratio of 0.450,
  so the model is explicitly penalized for ignoring the minority (phishing) class.

### Recommendation

For a security tool where missing a phishing URL is worse than a false alarm,
we should *favor recall over precision*. This can be done by lowering the
decision threshold below 0.5, but that would increase false positives.

The current F1 = 0.8878 balances both concerns. For a production
deployment, consider:

1. A higher-recall operating point (threshold ~0.3–0.4) if the cost of a
   missed phishing URL is high (e.g. enterprise email gateway).
2. A human-in-the-loop review for URLs with probability 0.3–0.7, where the
   model is uncertain.
3. Regular retraining as phishing tactics evolve.

## Excluded Features

- **domain_age_flag deliberately excluded: requires WHOIS/network access and breaks the offline-only inference guarantee.**
