from scheduler import start_scheduler, run_one_time_scrape
import os

if __name__ == "__main__":

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
        ("software", "sarasota")
        # ("software_developer", "remote"),
        # ("software_engineer", "remote"),
        # ("cobol", "tampa"),
        # ("cobol", "remote"),
        # ("cobol", "miami")
    ]
    run_every_minutes = 3
    staggering_minutes = 5

    # Check that the number of searches is within limits for threads - The tasks of displaying an alert and waiting for user input
    # are IO-bound tasks (not CPU intensive). In this case, it is usually ok to have 2 to 3 times the number of logical processors.
    logical_processors = os.cpu_count() 
    max_possible_threads = logical_processors * 2.5
    # The number 2 represents the main thread and the GUI thread
    max_possible_alert_workers = max_possible_threads - 2

    if len(tasks) <= max_possible_alert_workers:
        print("The amount of searches is within safe limits.. starting scrap")
        # Each task represents a gui alert thread
        start_scheduler(tasks, run_every_minutes, staggering_minutes, len(tasks))
    else:
        print("The amount of searches is not within limits.. not scraping. \nReduce your job searches and try again.")
        exit()

    # run_one_time_scrape("software_development", "tampa")
