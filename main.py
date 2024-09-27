from scheduler import start_scheduler, run_one_time_scrape

if __name__ == "__main__":
    # errors = red
    # gui = blue
    # scheduler = green
    # redis = yellow    
    # scrape = magenta
    tasks = [
        ("software_developer", "sarasota"),
        ("software_engineer", "sarasota"),
        ("software_developer", "tampa"),
        ("software_engineer", "tampa")
    ]
    run_every_minutes = 3
    staggering_minutes = 5

    start_scheduler(tasks, run_every_minutes, staggering_minutes)
    # run_one_time_scrape("software_development", "tampa")