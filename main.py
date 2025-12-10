import os
from pathlib import Path
import streamlit as st
from langchain_community.document_loaders import WebBaseLoader
from dotenv import load_dotenv

from chains import Chain
from portfolio import Portfolio
from utils import clean_text, send_email

# Load .env placed alongside this file (app/.env)
DOTENV_PATH = Path(__file__).with_name(".env")
load_dotenv(dotenv_path=DOTENV_PATH)


def show_success_page():
    """Display success page after email is sent."""
    st.title("✅ Email Sent Successfully")
    st.success("Your email has been sent successfully!")
    
    if st.button("Send Another Email"):
        st.session_state.email_sent = False
        st.session_state.email_generated = False
        st.rerun()


def create_streamlit_app(llm, portfolio, clean_text):
    # Check if email was sent - show success page
    if st.session_state.get('email_sent', False):
        show_success_page()
        return
    
    st.title("📧 Cold Mail Generator")
    
    # Initialize session state
    if 'email_generated' not in st.session_state:
        st.session_state.email_generated = False
    if 'generated_email' not in st.session_state:
        st.session_state.generated_email = ""
    if 'job_data' not in st.session_state:
        st.session_state.job_data = None
    
    url_input = st.text_input("Enter a URL:", value="Please enter the URL of the job posting", key="url_input")
    submit_button = st.button("Submit", key="submit_btn")

    # Generate email when Submit is clicked
    if submit_button:
        try:
            st.info("Loading the job posting... Please wait.")
            
            loader = WebBaseLoader([url_input])
            loader.requests_kwargs = {'timeout': 10}
            
            page_data = loader.load()
            
            if not page_data:
                st.error("Could not load the webpage. Please check the URL and try again.")
                st.session_state.email_generated = False
                return
            
            data = clean_text(page_data[0].page_content)
            st.success("Job posting loaded successfully!")
            
            portfolio.load_portfolio()
            jobs = llm.extract_jobs(data)
            
            if not jobs:
                st.warning("No jobs found in the provided URL.")
                st.session_state.email_generated = False
                return
            
            job = jobs[0]
            skills = job.get('skills', [])
            links = portfolio.query_links(skills)
            email = llm.write_email(job, links)
            
            st.session_state.email_generated = True
            st.session_state.generated_email = email
            st.session_state.job_data = job
            
        except Exception as e:
            st.error(f"An Error Occurred: {e}")
            st.info("💡 Troubleshooting tips:")
            st.write("1. Check your internet connection")
            st.write("2. Try a different job posting URL")
            st.write("3. Make sure the URL is accessible in your browser")
            st.session_state.email_generated = False

    # Display generated email if available
    if st.session_state.email_generated and st.session_state.generated_email:
        st.subheader("📧 Generated Email")
        st.code(st.session_state.generated_email, language='markdown')
        
        st.subheader("✉️ Send this email")
        recipient = st.text_input("Recipient email", key="recipient_email", value="")
        
        if st.button("Send email", key="send_email_button"):
            if not recipient:
                st.error("Please enter a recipient email address.")
            else:
                try:
                    smtp_host = os.getenv("SMTP_HOST")
                    smtp_port = int(os.getenv("SMTP_PORT", "587"))
                    smtp_user = os.getenv("SMTP_USER")
                    smtp_password = os.getenv("SMTP_PASSWORD")
                    from_email = os.getenv("SMTP_FROM") or smtp_user

                    if not all([smtp_host, smtp_user, smtp_password]):
                        missing = []
                        if not smtp_host: missing.append("SMTP_HOST")
                        if not smtp_user: missing.append("SMTP_USER")
                        if not smtp_password: missing.append("SMTP_PASSWORD")
                        st.error(f"SMTP settings are missing: {', '.join(missing)}")
                    else:
                        job = st.session_state.job_data
                        email = st.session_state.generated_email
                        subject = f"Cold email for {job.get('role', 'the opportunity')}"
                        
                        send_email(subject, email, recipient, smtp_host, smtp_port, smtp_user, smtp_password, from_email)
                        st.session_state.email_sent = True
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Failed to send email: {str(e)}")


if __name__ == "__main__":
    chain = Chain()
    portfolio = Portfolio()
    st.set_page_config(layout="wide", page_title="Cold Email Generator", page_icon="📧")
    create_streamlit_app(chain, portfolio, clean_text)

