import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, Briefcase, CheckCircle, XCircle, Loader2, AlertCircle, ArrowDown } from 'lucide-react';
import './App.css';

export default function ResumeMatcherApp() {
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const resultsRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      setResumeFile(file);
      setError(null);
    } else {
      setError('Only PDF files are supported.');
    }
  };

  const handleSubmit = async () => {
    if (!resumeFile || !jobDescription.trim()) {
      setError('Please provide both resume and job description.');
      return;
    }

    // mark as submitted so the upload form can be hidden while processing
    setSubmitted(true);

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('resume', resumeFile);
    formData.append('job_description', jobDescription);

    try {
      const response = await fetch('http://localhost:8000/api/match', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        setResult(data.data);
        // Scroll to results after a short delay to ensure render
        setTimeout(() => {
          resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
      } else {
        setError(data.error || 'Resume processing failed, please try again later.');
        setSubmitted(false);
      }
    } catch (err) {
      setError(
        'Couldn\'t reach backend. Make sure the Flask server is running at http://localhost:8000'
      );
      setSubmitted(false);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 70) return 'score-green';
    if (score >= 50) return 'score-yellow';
    return 'score-red';
  };

  const getScoreBg = (score) => {
    if (score >= 70) return 'score-bg-green';
    if (score >= 50) return 'score-bg-yellow';
    return 'score-bg-red';
  };

  const getScoreInterpretation = (score) => {
    if (score >= 80) return '🎯 Excellent Fit';
    if (score >= 70) return '✅ Good Fit';
    if (score >= 50) return '⚠️ Moderate Fit';
    return '❌ Poor Fit';
  };

  return (
    <div className="app">
      <div className="container">
        <header className="header">
            <div className="header-content">
              <h1>Resume Scorer</h1>
              <p>
                Upload your resume and paste a job description to see how well they align
              </p>
            </div>
        </header>

          {!submitted && (
            <div className="card input-card">
              <div className="form-group">
            <label className="label">
              <FileText size={18} />
              Upload Resume (PDF)
            </label>

            <div className="upload-box">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                id="resume-upload"
                hidden
              />
              <label htmlFor="resume-upload" className="upload-label">
                <Upload size={48} />
                <span>
                  {resumeFile ? (
                    <><strong>{resumeFile.name}</strong> ✓</>
                  ) : (
                    'Click to upload PDF'
                  )}
                </span>
              </label>
            </div>
              </div>

              <div className="form-group">
            <label className="label">
              <Briefcase size={18} />
              Job Description
            </label>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description here..."
              className="textarea"
            />
          </div>

          {error && (
            <div className="error-box">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={loading || !resumeFile || !jobDescription.trim()}
            className="primary-button"
          >
            {loading ? (
              <>
                <Loader2 className="spin" size={20} />
                Analyzing Resume...
              </>
            ) : (
              <>
                <CheckCircle size={20} />
                Match Resume
              </>
            )}
          </button>

              {loading && (
                <div className="loading-info">
                  <p>Processing your resume and analyzing compatibility...</p>
                  <p className="text-sm">This may take 2-3 seconds</p>
                </div>
              )}
            </div>
          )}

        {result && (
          <div className="card results-card" ref={resultsRef}>
            <div className="results-header">
              <h2>Compatibility Analysis</h2>
              <p className="interpretation">{getScoreInterpretation(result.overall_score)}</p>
            </div>

            {/* Overall Score Circle */}
            <div className="score-container">
              <div className={`score-circle ${getScoreBg(result.overall_score)}`}>
                <span className={getScoreColor(result.overall_score)}>
                  {result.overall_score}%
                </span>
              </div>
              <p className="score-label">Overall Compatibility</p>
            </div>

            {/* Main Metrics Grid */}
            <div className="grid">
              <div className="stat">
                <h3>Semantic Similarity</h3>
                <p className={getScoreColor(result.semantic_similarity)}>
                  {result.semantic_similarity}%
                </p>
                <small>Content alignment</small>
              </div>

              <div className="stat">
                <h3>Skill Match</h3>
                <p className={getScoreColor(result.skill_match_score)}>
                  {result.skill_match_score}%
                </p>
                <small>Required skills</small>
              </div>
            </div>

            {/* Section Scores */}
            <div className="section-scores">
              <h3>📍 Section Breakdown</h3>
              <div className="section-grid">
                {Object.entries(result.section_scores).map(([section, score]) => (
                  <div key={section} className={`section-stat ${getScoreColor(score)}`}>
                    <p className="section-name">
                      {section.charAt(0).toUpperCase() + section.slice(1)}
                    </p>
                    <p className="section-score">{score}%</p>
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: `${score}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Experience */}
            {result.experience_years > 0 && (
              <div className="experience">
                <h3>Experience</h3>
                <p className="exp-years">{result.experience_years} years</p>
              </div>
            )}

            {/* Skills Section */}
            <div className="skills">
              {result.skills.matched.length > 0 && (
                <div className="skill-group">
                  <h3>
                    <CheckCircle size={20} className="icon-green" />
                    Matched Skills <span className="count">{result.skills.matched.length}</span>
                  </h3>
                  <div className="tags">
                    {result.skills.matched.map((skill, i) => (
                      <span key={i} className="tag green">
                        ✓ {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {result.skills.missing.length > 0 && (
                <div className="skill-group">
                  <h3>
                    <XCircle size={20} className="icon-red" />
                    Skills to Develop <span className="count">{result.skills.missing.length}</span>
                  </h3>
                  <div className="tags">
                    {result.skills.missing.map((skill, i) => (
                      <span key={i} className="tag red">
                        ✕ {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Recommendations */}
            {result.recommendations && result.recommendations.length > 0 && (
              <div className="recommendations">
                <h3>💡 Recommendations</h3>
                <ul className="rec-list">
                  {result.recommendations.map((rec, i) => (
                    <li key={i} className="rec-item">{rec}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Action Buttons */}
            <div className="action-buttons">
              <button
                onClick={() => {
                  setResult(null);
                  setResumeFile(null);
                  setJobDescription('');
                  setError(null);
                  setSubmitted(false);
                }}
                className="secondary-button"
              >
                Try Another Resume
              </button>
              <button
                onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                className="secondary-button"
              >
                Back to Top
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}