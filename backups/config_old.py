from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URI = 'postgresql://adobi@localhost/adobi'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

# Initialize PromptManager with OpenAI API key
api_key= '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'
