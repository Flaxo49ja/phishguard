import { describe, it, expect } from 'vitest';
import { extractFeatures, urlEntropy, hasIpAddress, tldInSubdomain } from './features';

describe('extractFeatures — python parity', () => {
  it('google.com: bare homepage shape', () => {
    const f = extractFeatures('https://www.google.com');
    expect(f.url_length).toBe(22);
    expect(f.hostname_length).toBe(14);
    expect(f.path_length).toBe(0);
    expect(f.num_dots).toBe(2);
    expect(f.num_subdomains).toBe(1);
    expect(f.uses_https).toBe(true);
    expect(f.url_entropy).toBe(3.6635);
  });

  it('no scheme: prepends http:// like the CLI', () => {
    const f = extractFeatures('bit.ly/3xample');
    expect(f.url_length).toBe(21);
    expect(f.is_shortened_url).toBe(true);
    expect(f.uses_https).toBe(false);
  });

  it('@ handling: hostname is after the LAST @', () => {
    const f = extractFeatures('http://user@legitimate-looking.com@phishing-site.net');
    expect(f.hostname_length).toBe(17); // phishing-site.net
    expect(f.has_at_symbol).toBe(true);
  });

  it('ccTLD exemption: bbc.co.uk does not fire tld_in_subdomain', () => {
    expect(tldInSubdomain('www.bbc.co.uk')).toBe(false);
  });

  it('tld_in_subdomain fires on paypal.com.evil.ru', () => {
    expect(tldInSubdomain('paypal.com.evil.ru')).toBe(true);
  });

  it('raw IPv4 hostname detected with octet validation', () => {
    expect(hasIpAddress('192.168.1.1')).toBe(true);
    expect(hasIpAddress('999.1.1.1')).toBe(false);
    expect(hasIpAddress('example.com')).toBe(false);
  });

  it('entropy matches python rounding to 4 decimals', () => {
    expect(urlEntropy('https://www.google.com')).toBe(3.6635);
  });

  it('digit_letter_ratio counts only letters (http = 4 letters)', () => {
    const f = extractFeatures('http://192.168.1.1');
    expect(f.digit_letter_ratio).toBe(2); // 8 digits / 4 letters in 'http'
  });
});
