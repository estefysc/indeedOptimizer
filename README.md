# Indeed Search Optimizer

## Introduction

### Project Description
The Indeed Search Optimizer is a Python-based tool designed to automate job searches on Indeed. scraping job postings based on specific queries and locations. It is particularly useful for gathering large sets of job data across various locations, which can then be analyzed or reported.

### Features
- **Automated Job Scraping**: Scrapes job listings from Indeed based on specified keywords, locations, and radius.
- **Data Handling**: Collects and stores job data, allowing for comparison between new and old job postings.
- **Reporting**: Generates reports highlighting only new job postings and key job characteristics.
- **Concurrency**: Utilizes asynchronous programming to handle multiple pages of job results efficiently.

## Installation Instructions

### Prerequisites
Before running the project, ensure you have the following installed in your WSL environment:
- Windows Subsystem for Linux (WSL) with a preferred Linux distribution (e.g., Ubuntu) 
- Virtual environment (optional but recommended)
- Python 3.7 or later
- Scrapfly API key

### Installation Steps
1. **Access WSL**:    
   Open your WSL terminal.

2. **Clone the Repository**:  
   Navigate to your working directory in WSL and clone the repository:  
   git clone https://github.com/yourusername/indeed-search-optimizer.git  
   cd indeed-search-optimizer

3. **Set Up the Virtual Environment**:  
    Set up a Python virtual environment to manage dependencies:  
    python3 -m venv venv  
    source venv/bin/activate

4. **Install Dependencies**:  
    Install the required Python packages using pip:  
    pip install -r requirements.txt

5. **Set Up Environment Variables**:  
    Create a .env file in the root directory of the project and add your Scrapfly API key:  
    API_KEY=your_scrapfly_api_key

## Usage
### How to Use the Project
Configure Search Parameters:  
Edit the main.py file to specify your desired job search queries, locations, and search radii. The scrape_search function in main.py accepts these parameters.  

Run the Scraper:  
Execute the script either in your IDE or in your WSL terminal to start scraping.

### Access the Data:
Scraped job data will be stored in the scrapped_data directory as JSON files. Reports on new job postings will also be generated in the same directory.

## Data Structure
The JSON data you've scraped from Indeed contains a wealth of information about a job posting. Below is an explanation of some of the more notable keys you might find useful:

- **adBlob**: A string likely containing encrypted or encoded data for internal tracking or state management.
- **adId**: A unique identifier for the advertisement itself.
- **advn**: An advertiser number, which could be a unique identifier for the entity that posted the job.
- **applyCount**: The number of applications that have been submitted for this job posting.
- **company**: The name of the company that has posted the job.
- **companyBrandingAttributes**: Contains URLs to the company's logo and a header image which might be used in the job advertisement.
- **companyOverviewLink**: A URL to the company's overview page on Indeed.
- **companyRating**: The average rating of the company given by reviewers.
- **companyReviewCount**: The number of reviews that contributed to the company rating.
- **createDate**: The timestamp (likely in milliseconds since the Unix epoch) when the job was posted.
- **displayTitle**: The title of the job as displayed in the listing.
- **estimatedSalary**: An object containing the salary range for the job, including minimum and maximum values and the type of salary (e.g., yearly).
- **formattedLocation**: The location of the job, formatted for display.
- **indeedApplyEnabled**: Indicates whether the job supports applying directly through Indeed's platform.
- **jobCardRequirementsModel**: Details specific requirements for the job, such as necessary skills or experience.
- **jobLocationCity**, **jobLocationState**, **jobLocationPostal**: Specific location details of the job.
- **link**: A URL to the specific job posting on Indeed.
- **remoteWorkModel**: Details about the remote work options available for the job, such as hybrid work.
- **snippet**: A brief HTML snippet describing the job, often containing key points or requirements.
- **title**: The official title of the job posting.

