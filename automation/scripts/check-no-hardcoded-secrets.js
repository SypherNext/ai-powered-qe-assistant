#!/usr/bin/env node
// Fails with a non-zero exit code (and CI fails with it) if any staged
// test file contains a hardcoded secret-shaped string. Run this in CI
// against every file AI generated or touched, not just a sample.
// See the "AI Test Guardrails" lesson.

const fs = require('fs');

// Each pattern targets one common secret shape. Keep patterns narrow
// enough to avoid false-positiving on legitimate test fixtures (e.g. a
// test asserting that a 401 response body contains the word "password").
const SECRET_PATTERNS = [
  {
    name: 'Bearer token literal',
    regex: /Authorization\s*[:=]\s*['"`]Bearer\s+[A-Za-z0-9_\-.]{10,}['"`]/,
  },
  {
    name: 'sk- style API key literal',
    regex: /['"`]sk-[A-Za-z0-9]{16,}['"`]/,
  },
  {
    name: 'hardcoded password assignment',
    // Matches `password: "hunter2"` / `password = 'hunter2'` but not
    // `password: process.env.TEST_PASSWORD` or an empty-string check.
    regex: /password['"`]?\s*[:=]\s*['"`](?!\s*\$\{|process\.env)[^'"`\s]{4,}['"`]/i,
  },
];

function scanFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const findings = [];

  content.split('\n').forEach((line, index) => {
    for (const pattern of SECRET_PATTERNS) {
      if (pattern.regex.test(line)) {
        findings.push({
          file: filePath,
          line: index + 1,
          rule: pattern.name,
          snippet: line.trim(),
        });
      }
    }
  });

  return findings;
}

function main() {
  const targetFiles = process.argv.slice(2);
  if (targetFiles.length === 0) {
    console.error('Usage: node check-no-hardcoded-secrets.js <file1> <file2> ...');
    process.exit(2);
  }

  let allFindings = [];
  for (const file of targetFiles) {
    if (!fs.existsSync(file)) continue;
    allFindings = allFindings.concat(scanFile(file));
  }

  if (allFindings.length > 0) {
    console.error(`\nHardcoded secret check FAILED -- ${allFindings.length} finding(s):\n`);
    for (const finding of allFindings) {
      console.error(`  ${finding.file}:${finding.line}  [${finding.rule}]`);
      console.error(`    ${finding.snippet}\n`);
    }
    console.error('Replace hardcoded values with environment variables or a secrets manager reference, then re-run.');
    process.exit(1);
  }

  console.log(`Hardcoded secret check passed (${targetFiles.length} file(s) scanned).`);
  process.exit(0);
}

main();
