from scheduler import start_scheduler, run_one_time_scrape

if __name__ == "__main__":

    tasks = [
        ("job_title", "location"),
        ("job_title_2", "location_2"),
    ]
    run_every_minutes = 3
    staggering_minutes = 5

    start_scheduler(tasks, run_every_minutes, staggering_minutes)
    # run_one_time_scrape("software_development", "tampa")