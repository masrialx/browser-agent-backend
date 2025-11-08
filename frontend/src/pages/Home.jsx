/**
 * Home Page Component
 */
import React, { useState } from 'react';
import CodeEditor from '../components/CodeEditor';
import { generateCode, analyzeCode, refactorCode } from '../services/aiAgentService';

const Home = () => {
  const [code, setCode] = useState('');
  const [prompt, setPrompt] = useState('');
  const [language, setLanguage] = useState('python');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const response = await generateCode(prompt, language);
      setResult(response.data);
      setCode(response.data.code || '');
    } catch (error) {
      console.error('Error generating code:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!code) return;
    setLoading(true);
    try {
      const response = await analyzeCode(code, language);
      setResult(response.data);
    } catch (error) {
      console.error('Error analyzing code:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefactor = async () => {
    if (!code) return;
    setLoading(true);
    try {
      const response = await refactorCode(code, language, 'optimize');
      setResult(response.data);
      setCode(response.data.refactored_code || code);
    } catch (error) {
      console.error('Error refactoring code:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="home-container">
      <h1>AI Code Agent</h1>
      
      <div className="controls">
        <select 
          value={language} 
          onChange={(e) => setLanguage(e.target.value)}
        >
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
          <option value="typescript">TypeScript</option>
          <option value="java">Java</option>
        </select>
      </div>

      <div className="input-section">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe what code you want to generate..."
          rows={3}
        />
        <button onClick={handleGenerate} disabled={loading}>
          Generate Code
        </button>
      </div>

      <div className="editor-section">
        <CodeEditor 
          value={code} 
          onChange={setCode} 
          language={language}
        />
        <div className="editor-actions">
          <button onClick={handleAnalyze} disabled={loading || !code}>
            Analyze Code
          </button>
          <button onClick={handleRefactor} disabled={loading || !code}>
            Refactor Code
          </button>
        </div>
      </div>

      {result && (
        <div className="result-section">
          <h3>Results</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default Home;

