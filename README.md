# Indeed Search Optimizer

## Introduction

### Project Description
The Indeed Search Optimizer is a Python-based tool designed to automate job searches on Indeed. It scraps job postings based on specific queries and locations. This tool only displays new job postings since your last search by storing job keys each time pages are scraped. As a result, only new job keys are reported. However, note that sometimes an old posting may be reposted with a new job key, causing the same job to appear again. This does not happen frequently.

### Features
- **Automated Job Scraping**: Scrapes job listings from Indeed based on specified keywords, locations, and radius.
- **Data Handling**: Collects and stores job data, allowing for comparison between new and old job postings.
- **Reporting**: Generates reports highlighting only new job postings and key job characteristics.
- **Scheduler**: Manages periodic scraping tasks with configurable frequency and staggering.
- **GUI Notifications**: Displays notifications for newly found jobs.
- **Redis Integration**: Uses Redis for state management and scheduling of scraping tasks.
- **Enhanced Logging**: Provides detailed logs for debugging and monitoring.

## Installation Instructions

### Prerequisites
- Windows Subsystem for Linux 2 (WSL 2) Ubuntu with WSLg - check the [official WSLg GitHub repository](https://github.com/microsoft/wslg) 
- Python 3.7 or later
- Scrapfly API key
- Redis

### Installation Steps (Without Docker)
1. **Access WSL**:    
   Open your WSL terminal.

2. **Clone the Repository**:  
   Clone the repo and cd the root folder:   
   `cd indeedOptimizer`

3. **Set Up the Virtual Environment**:  
    Set up a Python virtual environment to manage dependencies:  
    `python3 -m venv .venv`  
    `source .venv/bin/activate`

4. **Install Dependencies**:  
    Install the required Python packages using pip:  
    `pip install -r requirements.txt`

5. **Set Up Environment Variables**:  
    Create a .env file in the root directory of the project and add your Scrapfly API key:  
    `API_KEY=your_scrapfly_api_key`

6. **Ensure Redis is Running**:
    Make sure Redis is installed and running on your system.

### Installation Steps (With Docker)

This assumes that docker is installed and running 

1. **Open terminal**:    
   Open your WSL, Linux, or OSX terminal.

2. **Clone the Repository**:  
   Clone the repo and cd the root folder:   
   `cd indeedOptimizer`

3. **Set Up Environment Variables**:  
    Create a .env file in the root directory of the project and add your Scrapfly API key:  
    `API_KEY=your_scrapfly_api_key`

4. **Run docker compose**:  
    `docker compose up`  



## Usage
### How to Use the Project
1. Configure Search Parameters:  
   Edit the `main.py` file to specify your desired job search queries, locations, and the staggering_minutes between each task scrap. The `start_scheduler` function in `main.py` accepts these parameters. For example:

   ```python
   tasks = [
       ("software_developer", "sarasota"),
       ("software_engineer", "sarasota"),
       ("python_developer", "sarasota"),
       ("php_developer", "sarasota"),
       ("software_developer", "tampa"),
       ("software_engineer", "tampa"),
       ("python_developer", "tampa"),
       ("php_developer", "tampa"),
       ("software_developer", "miami"),
       ("software_engineer", "miami"),
       ("software", "sarasota"),
       ("software_developer", "remote"),
       ("software_engineer", "remote")
   ]
   run_every_minutes = 3
   staggering_minutes = 5

   start_scheduler(tasks, run_every_minutes, staggering_minutes)
   ```

2. Run the Scraper:  
   Execute the script in your WSL terminal:
   ```
   python main.py
   ```

   The program will now run continuously, performing scrapes based on the configured schedule and displaying notifications for new jobs found.

### Access the Data:
- Scraped job data will be stored in the `scrapped_data` directory as JSON files. 
- Reports on new job postings will also be generated in the same directory.
- Logs are stored in the `logs` directory.

## New Features

### Redis Integration
- Redis is now used for state management and scheduling of scraping tasks.
- Ensure Redis is installed and running on your system.

### Scheduler
- The program now includes a scheduler for managing periodic scraping tasks.
- Users can configure the frequency of scrapes and the staggering time between tasks in the `main.py` file.

### GUI Notifications
- When new jobs are found, the program displays GUI notifications.
- Users can interact with these notifications to mark jobs as viewed.

### Enhanced Logging
- A new logging system provides detailed logs for debugging and monitoring.
- Logs are stored in the `logs` directory.

## Data Structure
The JSON data you scrape from Indeed contains a wealth of information about each job posting. Notably, the organicApplyStartCount is a piece of information not available directly on the website. This data point can help you be more strategic when applying for jobs. Below is an explanation of some of the more notable keys you might find useful:

- **adBlob**: A string likely containing encrypted or encoded data for internal tracking or state management.
- **adId**: A unique identifier for the advertisement itself.
- **advn**: An advertiser number, which could be a unique identifier for the entity that posted the job.
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
- **organicApplyStartCount**: The number of organic (non-sponsored) applications started for this job.
- **remoteWorkModel**: Details about the remote work options available for the job, such as hybrid work.
- **snippet**: A brief HTML snippet describing the job, often containing key points or requirements.
- **title**: The official title of the job posting.

## Keys Included in the Final Report

The following keys are included in the final report generated by the scraper:

- **company**: The name of the company that has posted the job.
- **companyRating**: The average rating of the company given by reviewers.
- **companyReviewCount**: The number of reviews that contributed to the company rating.
- **createDate**: The timestamp (likely in milliseconds since the Unix epoch) when the job was posted.
- **displayTitle**: The title of the job as displayed in the listing.
- **estimatedSalary**: An object containing the salary range for the job, including minimum and maximum values and the type of salary (e.g., yearly).
- **expired**: A boolean value indicating whether the job posting has expired.
- **formattedLocation**: The location of the job, formatted for display.
- **formattedRelativeTime**: A human-readable string indicating how long ago the job was posted (e.g., "3 days ago").
- **hiringMultipleCandidatesModel**: Information about whether the employer is hiring multiple candidates for this position.
- **jobCardRequirementsModel**: Details specific requirements for the job, such as necessary skills or experience.
- **jobkey**: A unique identifier for the job posting.
- **link**: A URL to the specific job posting on Indeed.
- **newJob**: A boolean value indicating whether this is a newly posted job.
- **organicApplyStartCount**: The number of organic (non-sponsored) applications started for this job.
- **remoteLocation**: Information about the remote work location, if applicable.
- **remoteWorkModel**: Details about the remote work options available for the job, such as hybrid work.
- **taxonomyAttributes**: Classification attributes for the job, which might include industry, job type, or other categorizations.
- **title**: The official title of the job posting.
- **urgentlyHiring**: A boolean value indicating whether the employer is urgently trying to fill this position.