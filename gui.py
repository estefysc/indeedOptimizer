import tkinter as tk

from queue import Queue
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore
from logging_config import app_logger
from redis_utils import set_jobs_as_viewed, should_scrape_by_time

logger = app_logger.getChild('gui')

# Create a thread pool for processing GUI updates
alert_executor = ThreadPoolExecutor(max_workers=13)
gui_queue = Queue()
gui_thread_instance = None
open_alerts = {}

def gui_thread(queue):
    while True:
        message = queue.get()
        if message is None:
            break
        title, body, query, location, scraps_staggering_minutes = message
        if (query, location) not in open_alerts:
            open_alerts[(query, location)] = True
            alert_executor.submit(show_new_jobs_alert, title, body, query, location, scraps_staggering_minutes)

def start_gui_thread():
    global gui_thread_instance
    gui_thread_instance = Thread(target=gui_thread, args=(gui_queue,))
    gui_thread_instance.start()

def stop_gui_thread():
    global gui_thread_instance
    if gui_thread_instance:
        gui_queue.put(None)  # Signal the GUI thread to exit
        gui_thread_instance.join()
        alert_executor.shutdown(wait=True)
        gui_thread_instance = None

def show_new_jobs_alert(title, message, job_type, location, scraps_staggering_minutes):
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    try:
        alert_window = tk.Toplevel()
        alert_window.title(title)
        alert_window.geometry("300x150")

        # Add message to the window
        message_label = tk.Label(alert_window, text=message)
        message_label.pack()

        # Function to handle OK button click
        def on_ok():
            set_jobs_as_viewed(job_type, location)
            logger.info(Fore.YELLOW + f"Jobs set as viewed for {location}, {job_type}")
            alert_window.destroy()
            del open_alerts[(job_type, location)]  # Remove from open alerts
            should_scrape_time = should_scrape_by_time(job_type, location, scraps_staggering_minutes * 60)
            logger.info(Fore.YELLOW + f"Should scrape time after clicking ok: {should_scrape_time}")
            # asyncio.create_task(perform_scheduled_scrape(job_type, location, gui_queue, scraps_staggering_minutes))

        ok_button = tk.Button(alert_window, text="OK", command=on_ok)
        ok_button.pack(pady=10)

        logger.info(Fore.BLUE + f"Alert displayed: {title} - {message}")
        root.mainloop()

    except Exception as e:
        logger.error(Fore.RED + f"Failed to display alert or set jobs as viewed: {e}")
        print(Fore.RED + f"Alert (console fallback): {title} - {message}")