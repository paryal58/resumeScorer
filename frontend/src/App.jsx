import React, { useState } from 'react';
import { Upload, FileText, Briefcase, CheckCircle, XCircle, Loader2, } from 'lucide-react';
import './App.css';

export default function ResumeMatcherApp() {
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

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
      } else {
        setError('Resume processing failed, please try again later.');
      }
    } catch (err) {
      setError(
        'Couldn\'t reach backend. Please try again later.'
      );
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

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>Resume Alignment Checker</h1>
          <p>
            Upload your resume and paste a job description to see how well they
            match
          </p>
        </header>

        <div className="card">
          <div className="form-group">
            <label className="label">
              <FileText size={16} />
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
                  {resumeFile ? resumeFile.name : 'Click to upload PDF'}
                </span>
              </label>
            </div>
          </div>

          <div className="form-group">
            <label className="label">
              <Briefcase size={16} />
              Job Description
            </label>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description here..."
            />
          </div>

          {error && <div className="error-box">{error}</div>}

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="primary-button"
          >
            {loading ? (
              <>
                <Loader2 className="spin" size={18} />
                Analyzing...
              </>
            ) : (
              'Match Resume'
            )}
          </button>
        </div>

        {result && (
          <div className="card results">
            <h2>Compatibility Results</h2>

            <div className={`score-circle ${getScoreBg(result.overall_score)}`}>
              <span className={getScoreColor(result.overall_score)}>
                {result.overall_score}%
              </span>
            </div>

            <div className="grid">
              <div className="stat">
                <h3>Skill Match</h3>
                <p className={getScoreColor(result.breakdown.skill_match)}>
                  {result.breakdown.skill_match}%
                </p>
              </div>

              <div className="stat">
                <h3>Semantic Similarity</h3>
                <p
                  className={getScoreColor(
                    result.breakdown.semantic_similarity
                  )}
                >
                  {result.breakdown.semantic_similarity}%
                </p>
              </div>
            </div>

            {result.experience_years > 0 && (
              <div className="experience">
                <h3>Experience</h3>
                <p>{result.experience_years} years detected</p>
              </div>
            )}

            <div className="skills">
              {result.skills.matched.length > 0 && (
                <div>
                  <h3>
                    <CheckCircle size={18} className="icon-green" />
                    Matched Skills
                  </h3>
                  <div className="tags">
                    {result.skills.matched.map((skill, i) => (
                      <span key={i} className="tag green">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {result.skills.missing.length > 0 && (
                <div>
                  <h3>
                    <XCircle size={18} className="icon-red" />
                    Missing Skills
                  </h3>
                  <div className="tags">
                    {result.skills.missing.map((skill, i) => (
                      <span key={i} className="tag red">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
