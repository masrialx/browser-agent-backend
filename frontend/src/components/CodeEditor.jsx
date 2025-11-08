/**
 * Code Editor Component
 */
import React, { useState } from 'react';

const CodeEditor = ({ value, onChange, language = 'python' }) => {
  const [code, setCode] = useState(value || '');

  const handleChange = (e) => {
    const newCode = e.target.value;
    setCode(newCode);
    if (onChange) {
      onChange(newCode);
    }
  };

  return (
    <div className="code-editor">
      <textarea
        value={code}
        onChange={handleChange}
        className="code-textarea"
        placeholder={`Enter your ${language} code here...`}
        spellCheck={false}
      />
    </div>
  );
};

export default CodeEditor;

