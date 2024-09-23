from flask import Flask, render_template, request, jsonify
from langchain_community.document_loaders import WebBaseLoader
from chains import Chain
from portfolio import Portfolio
from utils import clean_text

app = Flask(__name__)

# Initialize your objects
chain = Chain()
portfolio = Portfolio()

@app.route('/')
def index():
    # Render the web page for form submission
    return render_template('index.html')

@app.route('/generate_email', methods=['POST'])
def generate_email():
    try:
        # Check if the request is JSON (for Postman) or form-data (for web app)
        if request.is_json:
            # JSON request from Postman
            data = request.get_json()
            url_input = data.get('url')
        else:
            # Form-data request from the web app
            url_input = request.form.get('url')

        if not url_input:
            return jsonify({'error': 'URL is required.'}), 400

        # Load and clean the content from the URL
        loader = WebBaseLoader([url_input])
        page_content = loader.load().pop().page_content
        cleaned_data = clean_text(page_content)

        # Load portfolio and extract job postings
        portfolio.load_portfolio()
        jobs = chain.extract_jobs(cleaned_data)

        # Generate emails for the jobs found
        emails = []
        for job in jobs:
            skills = job.get('skills', [])
            links = portfolio.query_links(skills)
            email = chain.write_mail(job, links)
            emails.append(email)

        # Return the emails in JSON format for both Postman and web app
        if request.is_json:
            return jsonify({'emails': emails})
        else:
            return render_template('result.html', emails=emails)

    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            return render_template('error.html', error_message=str(e))

if __name__ == "__main__":
    app.run(debug=True)
