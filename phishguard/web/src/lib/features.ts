/**
 * URL Feature Extraction Module
 * Pure lexical/structural analysis - NO network calls
 *
 * TypeScript port of the Python `src/features.py` module — kept strictly
 * behavior-compatible so that features computed here match the ones the
 * exported model was trained on. If features.py changes, update this file
 * and re-export the model (python src/export_model.py).
 */

// Known URL shortener domains — mirrors SHORTENER_DOMAINS in features.py
const URL_SHORTENERS = new Set([
  'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'buff.ly',
  'shorturl.at', 'is.gd', 'sourc.in', 'cli.gs', 'tr.im', 'v.gd',
  'tiny.cc', 'snip.ly', 'cutt.ly', 'adf.ly', 'shorte.st', 'bc.vc',
  'da.gd', 'qr.io', 'rb.gy', '0.gp', 'alturls.com', 'xxa.me',
  'bcz.im', 'shoort.com', 'short.link', 'b23.tv',
  'u.to', 'vzt.url', 'shorturl.ms', 'twurl.cc', 'p.tl',
]);

// Common TLDs checked by tld_in_subdomain — mirrors features.py
const COMMON_TLDS = new Set([
  'com', 'net', 'org', 'edu', 'gov', 'mil', 'int',
  'ru', 'cn', 'de', 'fr', 'uk', 'nl', 'au', 'ca',
  'jp', 'kr', 'br', 'it', 'es', 'pl', 'in', 'za',
  'info', 'biz', 'name', 'pro', 'mobi', 'co', 'io',
  'app', 'dev', 'xyz', 'club', 'online', 'site',
  'shop', 'tech', 'top', 'download', 'loan', 'work',
]);

// IPv4 with octet range validation — mirrors _IPV4_REGEX in features.py
const IPV4_REGEX =
  /^(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)$/;

/**
 * Calculate Shannon entropy of a string (rounded to 4 decimals, like Python).
 */
export function urlEntropy(url: string): number {
  if (url.length === 0) return 0;
  const freq: Record<string, number> = {};
  for (const char of url) {
    freq[char] = (freq[char] || 0) + 1;
  }
  let entropy = 0;
  const len = url.length;
  for (const char in freq) {
    const p = freq[char] / len;
    if (p > 0) {
      entropy -= p * Math.log2(p);
    }
  }
  return round4(entropy);
}

function round4(x: number): number {
  return Math.round(x * 10000) / 10000;
}

/**
 * Parse URL components — mirrors Python's urllib.parse.urlparse semantics,
 * which differ from the WHATWG URL API in ways that matter for parity:
 *   - 'https://google.com'   -> path ''   (WHATWG gives '/')
 *   - hostname is lowercased, userinfo (@) and :port stripped
 *   - no normalization of the raw string (no added trailing slash)
 */
function parseUrl(url: string): {
  scheme: string;
  hostname: string;
  path: string;
  full: string;
} {
  let normalized = url.trim();
  if (!normalized.startsWith('http://') && !normalized.startsWith('https://') && !normalized.startsWith('ftp://')) {
    normalized = 'http://' + normalized;
  }

  try {
    // scheme
    const schemeMatch = normalized.match(/^([a-zA-Z][a-zA-Z0-9+.\-]*):/);
    const scheme = schemeMatch ? schemeMatch[1].toLowerCase() : 'http';
    let rest = schemeMatch ? normalized.slice(schemeMatch[0].length) : normalized;

    // authority (netloc)
    let netloc = '';
    if (rest.startsWith('//')) {
      rest = rest.slice(2);
      const stop = rest.search(/[/?#]/);
      netloc = stop === -1 ? rest : rest.slice(0, stop);
      rest = stop === -1 ? '' : rest.slice(stop);
    }

    // path: everything up to ? or # (verbatim, no trailing-slash injection)
    const qOrF = rest.search(/[?#]/);
    const path = qOrF === -1 ? rest : rest.slice(0, qOrF);

    // hostname: strip userinfo (up to LAST @), :port, and IPv6 brackets; lowercase
    let host = netloc;
    const at = host.lastIndexOf('@');
    if (at !== -1) host = host.slice(at + 1);
    if (host.startsWith('[')) {
      const end = host.indexOf(']');
      host = end === -1 ? host.slice(1) : host.slice(1, end);
    } else {
      const colon = host.indexOf(':');
      if (colon !== -1) host = host.slice(0, colon);
    }

    return { scheme, hostname: host.toLowerCase(), path, full: normalized };
  } catch {
    return { scheme: 'http', hostname: normalized, path: '', full: normalized };
  }
}

/**
 * Check if hostname is a valid IPv4 address (octets range-checked).
 */
export function hasIpAddress(hostname: string): boolean {
  return IPV4_REGEX.test(hostname);
}

/**
 * tld_in_subdomain with the ccTLD exemption (e.g. 'co' in bbc.co.uk does NOT
 * fire, but 'com' in paypal.com.verify-login.ru does) — mirrors features.py.
 */
export function tldInSubdomain(hostname: string): boolean {
  const parts = hostname.toLowerCase().split('.').filter(Boolean);
  if (parts.length < 3) return false;

  const final = parts[parts.length - 1];
  for (let i = 0; i < parts.length - 1; i++) {
    const part = parts[i];
    if (!COMMON_TLDS.has(part)) continue;
    // Skip ccTLD second-level labels: 'co' in bbc.co.uk
    if (i === parts.length - 2 && final.length === 2) continue;
    return true;
  }
  return false;
}

/**
 * Extract all features from a URL — same 18 features, same semantics as
 * Python's extract_features().
 */
export function extractFeatures(url: string): Record<string, number | boolean> {
  const parsed = parseUrl(url);
  const { scheme, hostname, path, full } = parsed;

  // 1. url_length (normalized URL — matches the Python CLI, which prepends
  //    the scheme before extraction)
  const urlLength = full.length;

  // 2. hostname_length
  const hostnameLength = hostname.length;

  // 3. path_length (path only — no query/fragment)
  const pathLength = path.length;

  // 4. num_dots
  const numDots = countChars(full, '.');

  // 5. num_hyphens
  const numHyphens = countChars(full, '-');

  // 6. num_underscores
  const numUnderscores = countChars(full, '_');

  // 7. num_slashes
  const numSlashes = countChars(full, '/');

  // 8. num_digits
  const numDigits = countMatching(full, (c) => c >= '0' && c <= '9');

  // 9. num_special_chars — exactly the set '@%=&?#+$,' from features.py
  const specialChars = new Set('@%=&?#+$,'.split(''));
  const numSpecialChars = countMatching(full, (c) => specialChars.has(c));

  // 10. has_at_symbol
  const hasAtSymbol = full.includes('@');

  // 11. has_ip_address
  const hasIp = hasIpAddress(hostname);

  // 12. num_subdomains (segments beyond registered domain + TLD)
  const hostParts = hostname.split('.').filter(Boolean);
  const numSubdomains = hostParts.length <= 2 ? 0 : hostParts.length - 2;

  // 13. uses_https
  const usesHttps = scheme === 'https';

  // 14. has_https_token_in_path — literal 'https' in the path only
  const hasHttpsTokenInPath = path.toLowerCase().includes('https');

  // 15. is_shortened_url
  const hostLower = hostname.toLowerCase();
  const isShortenedUrl =
    URL_SHORTENERS.has(hostLower) ||
    [...URL_SHORTENERS].some((s) => hostLower.endsWith('.' + s));

  // 16. url_entropy
  const entropy = urlEntropy(full);

  // 17. tld_in_subdomain (with ccTLD exemption)
  const tldInSub = tldInSubdomain(hostname);

  // 18. digit_letter_ratio (0 when there are no letters — mirrors Python)
  const letters = countMatching(full, (c) => /[a-zA-Z]/.test(c));
  const digitLetterRatio = letters === 0 ? 0 : round4(numDigits / letters);

  return {
    url_length: urlLength,
    hostname_length: hostnameLength,
    path_length: pathLength,
    num_dots: numDots,
    num_hyphens: numHyphens,
    num_underscores: numUnderscores,
    num_slashes: numSlashes,
    num_digits: numDigits,
    num_special_chars: numSpecialChars,
    has_at_symbol: hasAtSymbol,
    has_ip_address: hasIp,
    num_subdomains: numSubdomains,
    uses_https: usesHttps,
    has_https_token_in_path: hasHttpsTokenInPath,
    is_shortened_url: isShortenedUrl,
    url_entropy: entropy,
    tld_in_subdomain: tldInSub,
    digit_letter_ratio: digitLetterRatio,
  };
}

function countChars(s: string, ch: string): number {
  let n = 0;
  for (const c of s) if (c === ch) n++;
  return n;
}

function countMatching(s: string, pred: (c: string) => boolean): number {
  let n = 0;
  for (const c of s) if (pred(c)) n++;
  return n;
}

/**
 * Get feature descriptions for display
 */
export const FEATURE_DESCRIPTIONS: Record<string, string> = {
  url_length: 'Total length of the URL string',
  hostname_length: 'Length of the hostname portion',
  path_length: 'Length of the path portion',
  num_dots: 'Number of dots (.) in the URL',
  num_hyphens: 'Number of hyphens (-) in the URL',
  num_underscores: 'Number of underscores (_) in the URL',
  num_slashes: 'Number of slashes (/) in the URL',
  num_digits: 'Number of digit characters',
  num_special_chars: 'Count of special characters (@, %, =, &, etc.)',
  has_at_symbol: 'Contains @ symbol (used to hide real destination)',
  has_ip_address: 'Hostname is a raw IP address instead of domain',
  num_subdomains: 'Number of subdomains (excessive = suspicious)',
  uses_https: 'Uses HTTPS protocol',
  has_https_token_in_path: 'Path contains "https" (deceptive)',
  is_shortened_url: 'Uses a known URL shortening service',
  url_entropy: 'Shannon entropy of URL string (high = random-looking)',
  tld_in_subdomain: 'TLD found in subdomain (e.g., paypal.com.evil.ru)',
  digit_letter_ratio: 'Ratio of digits to letters in URL',
};

/**
 * Get risk indicator for each feature
 */
export function getFeatureRisk(featureName: string, value: number | boolean | string): 'high' | 'medium' | 'low' | 'neutral' {
  switch (featureName) {
    case 'url_length':
      return (value as number) > 75 ? 'high' : (value as number) > 50 ? 'medium' : 'low';
    case 'hostname_length':
      return (value as number) > 30 ? 'high' : (value as number) > 20 ? 'medium' : 'low';
    case 'num_dots':
      return (value as number) > 4 ? 'high' : (value as number) > 2 ? 'medium' : 'low';
    case 'num_hyphens':
      return (value as number) > 3 ? 'high' : (value as number) > 1 ? 'medium' : 'low';
    case 'num_underscores':
      return (value as number) > 2 ? 'high' : (value as number) > 0 ? 'medium' : 'low';
    case 'num_digits':
      return (value as number) > 10 ? 'high' : (value as number) > 5 ? 'medium' : 'low';
    case 'num_special_chars':
      return (value as number) > 5 ? 'high' : (value as number) > 2 ? 'medium' : 'low';
    case 'has_at_symbol':
      return value ? 'high' : 'neutral';
    case 'has_ip_address':
      return value ? 'high' : 'neutral';
    case 'num_subdomains':
      return (value as number) > 3 ? 'high' : (value as number) > 1 ? 'medium' : 'low';
    case 'uses_https':
      return value ? 'low' : 'medium';
    case 'has_https_token_in_path':
      return value ? 'high' : 'neutral';
    case 'is_shortened_url':
      return value ? 'medium' : 'neutral';
    case 'url_entropy':
      return (value as number) > 4.0 ? 'high' : (value as number) > 3.5 ? 'medium' : 'low';
    case 'tld_in_subdomain':
      return value ? 'high' : 'neutral';
    case 'digit_letter_ratio':
      return (value as number) > 0.5 ? 'high' : (value as number) > 0.2 ? 'medium' : 'low';
    default:
      return 'neutral';
  }
}
