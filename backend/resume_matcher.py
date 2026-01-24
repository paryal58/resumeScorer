import re
import pdfplumber
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Dict, List, Tuple

class ResumeJobMatcher:
    def __init__(self):
        # Load pre-trained sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Skill standardization mapping
        self.skill_map = {
            'js': 'javascript',
            'react.js': 'react',
            'reactjs': 'react',
            'node.js': 'nodejs',
            'ml': 'machine learning',
            'ai': 'artificial intelligence',
            'postgresql': 'sql',
            'mysql': 'sql',
            'mongodb': 'nosql',
            'aws': 'cloud computing',
            'azure': 'cloud computing',
            'gcp': 'cloud computing',
        }
        
        # Common technical skills to extract
        self.common_skills = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#',
            'react', 'angular', 'vue', 'nodejs', 'django', 'flask',
            'sql', 'nosql', 'mongodb', 'postgresql', 'mysql',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp',
            'machine learning', 'deep learning', 'data science',
            'git', 'agile', 'scrum', 'rest api', 'graphql'
        ]
    
    # Extract text from pdfs
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except Exception as e:
            raise Exception(f"Error extracting PDF: {str(e)}")
        return text
    
    # Standarize text for more accurate matching
    def normalize_text(self, text: str) -> str:
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep + and # for C++, C#
        text = re.sub(r'[^\w\s\+\#\.]', ' ', text)
        
        # Standardize skills
        for old_skill, new_skill in self.skill_map.items():
            text = text.replace(old_skill, new_skill)
        
        return text.strip()
    
    # Extract skills to a list
    def extract_skills(self, text: str) -> List[str]:
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.common_skills:
            # Use word boundaries to match whole words
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                found_skills.append(skill)
        
        return list(set(found_skills))
    

    def extract_years_of_experience(self, text: str) -> float:
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of)?\s*experience',
            r'experience[:\s]+(\d+)\+?\s*years?',
            r'(\d+)\s*yrs'
        ]
        
        years = []
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            years.extend([int(m) for m in matches])
        
        return max(years) if years else 0
    
    # Calculate matches
    def calculate_skill_match(self, resume_skills: List[str], job_skills: List[str]) -> Tuple[float, List[str], List[str]]:
        if not job_skills:
            return 1.0, resume_skills, []
        
        resume_set = set(resume_skills)
        job_set = set(job_skills)
        
        matched_skills = list(resume_set.intersection(job_set))
        missing_skills = list(job_set.difference(resume_set))
        
        # Jaccard similarity
        if len(job_set) == 0:
            score = 1.0
        else:
            score = len(matched_skills) / len(job_set)
        
        return score, matched_skills, missing_skills
    
    # Normalize the text
    def get_embedding(self, text: str) -> np.ndarray:
        embedding = self.model.encode([text])[0]
        # L2 normalization
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding
    

    # Cosine similarity
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        similarity = np.dot(emb1, emb2)
        similarity = (similarity + 1) / 2
        return float(similarity)
    
    def calculate_compatibility(self, resume_text: str, job_description: str) -> Dict:
        # Normalize texts
        resume_normalized = self.normalize_text(resume_text)
        job_normalized = self.normalize_text(job_description)
        
        # Extract skills
        resume_skills = self.extract_skills(resume_normalized)
        job_skills = self.extract_skills(job_normalized)
        
        # Calculate skill match
        skill_score, matched_skills, missing_skills = self.calculate_skill_match(
            resume_skills, job_skills
        )
        
        # Calculate semantic similarity
        semantic_score = self.calculate_semantic_similarity(
            resume_normalized, job_normalized
        )
        
        # Extract experience
        years_experience = self.extract_years_of_experience(resume_text)
        
        # Weighted final score
        weights = {
            'skills': 0.5,      
            'semantic': 0.5,    
        }
        
        final_score = (
            weights['skills'] * skill_score +
            weights['semantic'] * semantic_score
        )
        
        # Convert to percentage
        final_score_percent = final_score * 100
        
        return {
            'overall_score': round(final_score_percent, 2),
            'breakdown': {
                'skill_match': round(skill_score * 100, 2),
                'semantic_similarity': round(semantic_score * 100, 2),
            },
            'skills': {
                'matched': matched_skills,
                'missing': missing_skills,
                'resume_skills': resume_skills,
                'job_skills': job_skills,
            },
            'experience_years': years_experience,
        }


if __name__ == "__main__":
    # Initialize matcher
    matcher = ResumeJobMatcher()
    
    job_description = """
    Value to be fed from frontend
    """
    
    resume_text = """
    Value to be fed from frontend
    """
    
    # Calculate compatibility
    result = matcher.calculate_compatibility(resume_text, job_description)
    
    # Print results
    print(f"Overall Compatibility: {result['overall_score']}%")
    print(f"\nBreakdown:")
    print(f"  Skill Match: {result['breakdown']['skill_match']}%")
    print(f"  Semantic Similarity: {result['breakdown']['semantic_similarity']}%")
    print(f"\nMatched Skills: {', '.join(result['skills']['matched'])}")
    print(f"Missing Skills: {', '.join(result['skills']['missing'])}")
    print(f"\nYears of Experience: {result['experience_years']}")