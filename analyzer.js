// analyzer.js
// Dewey.Decimal: text statistics. Launcher for js/dewey.js; the algorithm is specified in spec/SPEC.md.
process.exitCode = require('./js/dewey').main(process.argv.slice(2));
