// analyzer.js
// Dewey.Decimal 📚
// A text analysis toolkit for decision-ready insights.

const fs = require('fs');
const Sentiment = require('sentiment');
const readability = require('text-readability');

function analyzeText(filePath) {
    const text = fs.readFileSync(filePath, 'utf8');

    // Basic counts
    const words = text.split(/\s+/);
    const wordCount = words.length;
    const charCount = text.length;

    // Most common words
    const freq = {};
    words.forEach(w => {
        w = w.toLowerCase().replace(/[^a-z]/g, '');
        if (w) freq[w] = (freq[w] || 0) + 1;
    });
    const commonWords = Object.entries(freq)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([w]) => w);

    // Sentiment
    const sentiment = new Sentiment();
    const sentimentScore = sentiment.analyze(text).score;
    let tone = "Neutral";
    if (sentimentScore > 0) tone = "Positive";
    if (sentimentScore < 0) tone = "Negative";

    // Readability (Flesch-Kincaid)
    const grade = readability.fleschKincaidGradeLevel(text);

    // Print results
    console.log(`📊 Analysis of: ${filePath}`);
    console.log(`Words: ${wordCount}`);
    console.log(`Characters: ${charCount}`);
    console.log("Most common words:", commonWords);
    console.log(`Sentiment: ${tone}`);
    console.log(`Readability (Grade Level): ${grade}`);
}

// CLI
if (process.argv.length < 3) {
    console.log("Usage: node analyzer.js <file>");
} else {
    analyzeText(process.argv[2]);
}
