"""
Resume Scorer - Core matching logic
Semantic and skill-based resume-to-job compatibility analysis
"""

import re
import pdfplumber
import numpy as np
from typing import Dict, List, Tuple
from sentence_transformers import SentenceTransformer


class ResumeJobMatcher:

    # Initialize the matcher with embedding model and skill mappings
    def __init__(self):
        
        # Load pre-trained sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        # Skill aliases for normalization (common variations → standard name)
        self.skill_aliases = {
            'js': 'javascript',
            'jsx': 'javascript',
            'ts': 'typescript',
            'react.js': 'react',
            'reactjs': 'react',
            'node.js': 'nodejs',
            'node': 'nodejs',
            'py': 'python',
            'ml': 'machine learning',
            'ai': 'artificial intelligence',
            'dl': 'deep learning',
            'nlp': 'natural language processing',
            'postgresql': 'sql',
            'postgres': 'sql',
            'mysql': 'sql',
            'mongodb': 'nosql',
            'dynamodb': 'nosql',
            'aws': 'cloud computing',
            'azure': 'cloud computing',
            'gcp': 'cloud computing',
            'kubernetes': 'k8s',
            'k8': 'k8s',
            'docker': 'containerization',
            'llm': 'large language models',
            'llms': 'large language models',
            'gpt': 'large language models',
            'tf': 'tensorflow',
            'pytorch': 'deep learning',
            'keras': 'deep learning',
            'sklearn': 'scikit-learn',
            'rest': 'rest api',
            'graphql api': 'graphql',
            'ci/cd': 'continuous integration',
        }

        # Comprehensive list of technical skills
        self.common_skills = [
            # Languages
            'python', 'java', 'javascript', 'typescript',
            'c++', 'c#', 'go', 'rust', 'ruby', 'php',
            
            # Frontend
            'react', 'angular', 'vue', 'svelte',
            'html', 'css', 'tailwind', 'bootstrap',
            
            # Backend
            'nodejs', 'django', 'flask', 'fastapi',
            'spring', 'express', 'asp.net',
            
            # Databases
            'sql', 'nosql', 'mongodb', 'postgresql',
            'mysql', 'dynamodb', 'redis',
            
            # DevOps & Cloud
            'docker', 'containerization', 'k8s',
            'aws', 'azure', 'gcp', 'cloud computing',
            'ci/cd', 'continuous integration',
            'jenkins', 'gitlab',
            
            # Data & ML
            'machine learning', 'deep learning',
            'data science', 'natural language processing',
            'tensorflow', 'pytorch',
            'scikit-learn', 'pandas', 'numpy',
            'large language models',
            
            # APIs & Protocols
            'rest api', 'graphql', 'websocket',
            'grpc', 'soap',
            
            # Tools & Methods
            'git', 'agile', 'scrum', 'kanban',
            'linux', 'unix', 'shell', 'bash',
            'jira', 'confluence',
            
            # Soft Skills (for semantic matching)
            'communication', 'leadership', 'problem solving',
            'teamwork', 'collaboration'
        ]

        # Section weights for final scoring
        self.section_weights = {
            'skills': 0.20,
            'experience': 0.35,
            'projects': 0.25,
            'education': 0.20
        }

    # Extract text from pdf
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"

        except Exception as e:
            raise Exception(f"Error extracting PDF: {str(e)}")

        return text

    # Normalize text for semantic and skill analysis
    # Normalize by converting to lowercase, remove whitespaces, standarize skills
    def normalize_text(self, text: str) -> str:
        # Convert to lowercase
        text = text.lower()

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep + and # for C++, C#
        text = re.sub(r'[^\w\s\+\#\.]', ' ', text)

        # Apply skill normalization
        for alias, standard in self.skill_aliases.items():
            text = text.replace(alias, standard)

        return text.strip()

    # Extract logical resume sections using regex patterns
    def extract_sections(self, text: str) -> Dict[str, str]:
        normalized = text.lower()

        section_patterns = {
            'skills': r'(skills|technical\s+skills|competencies)(.*?)(experience|work|projects|education|$)',
            'experience': r'(experience|work\s+experience|employment)(.*?)(projects|education|skills|$)',
            'projects': r'(projects|personal\s+projects|portfolio)(.*?)(education|experience|skills|$)',
            'education': r'(education|academic)(.*?)(experience|projects|skills|$)'
        }

        sections = {}

        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, normalized, re.DOTALL | re.IGNORECASE)
            sections[section_name] = match.group(2) if match else ""

        return sections

    # Extract standardized technical skills from text
    def extract_skills(self, text: str) -> List[str]:
        normalized_text = self.normalize_text(text)
        found_skills = []

        for skill in self.common_skills:
            # Use word boundaries for accurate matching
            if re.search(r'\b' + re.escape(skill) + r'\b', normalized_text):
                found_skills.append(skill)

        return sorted(list(set(found_skills)))


    def extract_years_of_experience(self, text: str) -> float:
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of)?\s*experience',
            r'experience[:\s]+(\d+)\+?\s*years?',
            r'(\d+)\s*yrs',
            r'(\d{4})\s*[-–]\s*(?:present|current)',
        ]

        years = []

        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                try:
                    year_value = int(match)
                    if 0 < year_value < 60:
                        years.append(year_value)
                except ValueError:
                    continue

        return max(years) if years else 0

    # Generate normalized embedding vector using sentence transformer
    def get_embedding(self, text: str) -> np.ndarray:
        embedding = self.model.encode([text])[0]

        # L2 normalization
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding

    # Compute cosine similarity between two texts using embeddings
    def semantic_similarity(self, text1: str, text2: str) -> float:
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        similarity = np.dot(emb1, emb2)

        # Normalize from [-1, 1] to [0, 1]
        similarity = (similarity + 1) / 2

        return float(similarity)


    # Calculate skill overlap using Jaccard similarity
    def calculate_skill_match(
        self,
        resume_skills: List[str],
        job_skills: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        if not job_skills:
            return 1.0, resume_skills, []

        resume_set = set(resume_skills)
        job_set = set(job_skills)

        matched = list(resume_set.intersection(job_set))
        missing = list(job_set.difference(resume_set))

        # Jaccard similarity
        score = len(matched) / len(job_set) if job_set else 1.0

        return score, sorted(matched), sorted(missing)


    # Compare each resume section independently against job description
    def calculate_section_scores(
        self,
        resume_sections: Dict[str, str],
        job_description: str
    ) -> Dict[str, float]:
        
        scores = {}
        for section, content in resume_sections.items():
            if content.strip() and len(content.strip()) > 10:
                # Only score if section has meaningful content
                score = self.semantic_similarity(content, job_description)
            else:
                score = 0.0

            scores[section] = round(score * 100, 2)

        return scores

    # Generate actionable, explainable recommendations
    def generate_recommendations(
        self,
        missing_skills: List[str],
        section_scores: Dict[str, float],
        overall_score: float
    ) -> List[str]:
        recommendations = []

        # Skill-based recommendations
        if missing_skills and len(missing_skills) > 0:
            top_missing = ', '.join(missing_skills[:3])
            recommendations.append(
                f"Add experience with: {top_missing}"
            )

        # Section-specific recommendations
        if section_scores.get('skills', 0) < 60:
            recommendations.append(
                "Expand technical skills section with role-specific technologies"
            )

        if section_scores.get('experience', 0) < 60:
            recommendations.append(
                "Strengthen work experience descriptions with measurable impact and technical details"
            )

        if section_scores.get('projects', 0) < 50:
            recommendations.append(
                "Add relevant technical or domain-specific projects"
            )

        if section_scores.get('education', 0) < 50:
            recommendations.append(
                "Highlight relevant coursework or certifications"
            )

        # Overall assessment
        if overall_score < 50:
            recommendations.append(
                "This role may not be a strong fit - consider building more relevant skills"
            )
        elif overall_score < 70:
            recommendations.append(
                "You're on the right track - focus on the areas above to improve match"
            )
        else:
            recommendations.append(
                "Strong fit! Your profile aligns well with this role"
            )

        return recommendations


    # Main compatibility calculation pipeline.
    # Combines semantic matching, skill analysis, and section scoring.
    def calculate_compatibility(
        self,
        resume_text: str,
        job_description: str
    ) -> Dict:
        # Normalize texts
        resume_normalized = self.normalize_text(resume_text)
        job_normalized = self.normalize_text(job_description)

        # Extract structured sections from resume
        resume_sections = self.extract_sections(resume_text)

        # Extract skills
        resume_skills = self.extract_skills(resume_normalized)
        job_skills = self.extract_skills(job_normalized)

        # Calculate skill overlap (Jaccard similarity)
        skill_score, matched_skills, missing_skills = self.calculate_skill_match(
            resume_skills,
            job_skills
        )

        # Calculate overall semantic similarity
        semantic_score = self.semantic_similarity(
            resume_normalized,
            job_normalized
        )

        # Calculate section-specific scores
        section_scores = self.calculate_section_scores(
            resume_sections,
            job_normalized
        )

        # Weighted section contribution
        weighted_section_score = 0
        for section, score in section_scores.items():
            weight = self.section_weights.get(section, 0)
            weighted_section_score += (score / 100) * weight

        # Final weighted score (Semantic Alignment, Skill Match, Section Alignment)
        final_score = 0.35 * semantic_score + 0.35 * skill_score + 0.30 * weighted_section_score

        final_score_percent = round(final_score * 100, 2)

        # Extract experience
        years_experience = self.extract_years_of_experience(resume_text)

        # Generate recommendations
        recommendations = self.generate_recommendations(
            missing_skills,
            section_scores,
            final_score_percent
        )

        # Return comprehensive result
        return {
            'overall_score': final_score_percent,
            'semantic_similarity': round(semantic_score * 100, 2),
            'skill_match_score': round(skill_score * 100, 2),
            'section_scores': section_scores,
            'experience_years': years_experience,
            'skills': {
                'matched': matched_skills,
                'missing': missing_skills,
                'resume_skills': resume_skills,
                'job_skills': job_skills
            },
            'recommendations': recommendations
        }
    

if __name__ == '__main__':
    matcher = ResumeJobMatcher()

    sample_resume = """
    Senior Python Developer with 5+ years of experience
    
    Skills: Python, Django, Flask, React, Docker, AWS, PostgreSQL, REST API
    
    Experience:
    - Built scalable NLP systems using PyTorch and FastAPI
    - Led team of 3 developers on machine learning pipeline
    - Deployed containerized applications to AWS using Docker and Kubernetes
    
    Projects:
    - NLP-based chatbot using transformers and FAISS
    - Real-time data pipeline with Kafka and PySpark
    
    Education: BS Computer Science
    """

    sample_jd = """
    We're hiring a Machine Learning Engineer!
    
    Required Skills:
    - Python, PyTorch, TensorFlow
    - NLP and Deep Learning experience
    - Docker and Kubernetes for containerization
    - AWS or GCP cloud experience
    
    Nice to have:
    - FastAPI for model serving
    - Redis for caching
    - Kubernetes orchestration
    
    Responsibilities:
    - Develop and deploy ML models
    - Optimize inference performance
    - Collaborate with data science team
    """

    result = matcher.calculate_compatibility(sample_resume, sample_jd)

    print("\n")
    print("COMPATIBILITY ANALYSIS")
    print("="*60)
    print(f"\nOverall Score: {result['overall_score']}%")
    print(f"\nBreakdown:")
    print(f"  - Semantic Similarity: {result['semantic_similarity']}%")
    print(f"  - Skill Match: {result['skill_match_score']}%")
    print(f"\nSection Scores:")
    for section, score in result['section_scores'].items():
        print(f"  - {section.capitalize()}: {score}%")
    print(f"\nExperience: {result['experience_years']} years")
    print(f"\nMatched Skills: {', '.join(result['skills']['matched']) or 'None'}")
    print(f"\nMissing Skills: {', '.join(result['skills']['missing']) or 'None'}")
    print(f"\nRecommendations:")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"  {i}. {rec}")
    print("\n")