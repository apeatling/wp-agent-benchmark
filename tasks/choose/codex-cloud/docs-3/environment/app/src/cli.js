#!/usr/bin/env node
// tidyup: remove old files from a folder.
const [, , dir, ...flags] = process.argv;
const has = f => flags.includes(f);
const value = f => { const i = flags.indexOf(f); return i >= 0 ? flags[i + 1] : undefined; };
if (!dir || has('--help')) {
  console.log('Usage: tidyup <folder> [--older-than 30d] [--larger-than 100mb] [--match "*.tmp"] [--dry-run]');
  process.exit(0);
}
console.log(`Would tidy ${dir}`, { olderThan: value('--older-than'), largerThan: value('--larger-than'), match: value('--match'), dryRun: has('--dry-run') });
