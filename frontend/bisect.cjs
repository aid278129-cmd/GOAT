const fs = require('fs');
const parser = require('@babel/parser');
const code = fs.readFileSync('E:/Zyntrix/frontend/src/components/pipeline/StandardsClausesView.jsx', 'utf8');
const lines = code.split('\n');

for (let i = 130; i < lines.length; i++) {
  try {
    const chunk = lines.slice(0, i).join('\n') + '\n    </div>\n  );\n}';
    parser.parse(chunk, { sourceType: 'module', plugins: ['jsx'] });
  } catch(e) {
    if (e.message.includes('Unexpected token, expected "}"')) {
      console.log('Error starts at line', i);
      break;
    }
  }
}
