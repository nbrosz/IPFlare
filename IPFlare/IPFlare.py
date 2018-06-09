
#!/usr/bin/python3

import argparse
import time
import ipgetter
import requests
import logging
import logging.handlers
import sys

LOG_FILENAME = "./ipflare.log"
LOG_LEVEL = logging.INFO  # Could be e.g. "DEBUG" or "WARNING"

latest_ip = None

#constants
def BASE_URL():
    return "https://api.cloudflare.com/client/v4/"

def main():
    global LOG_FILENAME
    global LOG_LEVEL

    parser = argparse.ArgumentParser()
    parser.add_argument("email",
                        help="the email for Cloudflare")
    parser.add_argument("key",
                        help="the key for Cloudflare")
    parser.add_argument("zone",
                        help="the zone for Cloudflare")
    parser.add_argument("names", 
                        help="update the given comma-separted list of DNS record names")
    parser.add_argument("-i", "--interval",
                        help="interval in minutes to re-run the update",
                        type=int)
    parser.add_argument("-l", "--log",
                        help="location to put logs")

    args = parser.parse_args()

    dns_names = args.names.split(",")
    if (args.log):
        LOG_FILENAME = args.log

    # Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
    # Give the logger a unique name (good practice)
    logger = logging.getLogger(__name__)
    # Set the log level to LOG_LEVEL
    logger.setLevel(LOG_LEVEL)
    # Format each log message like this
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')

    # Output to console as well
    consolehandler = logging.StreamHandler(sys.stdout)
    consolehandler.setFormatter(formatter)
    logger.addHandler(consolehandler)

    # Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
    filehandler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
    # Attach the formatter to the handler
    filehandler.setFormatter(formatter)
    # Attach the handler to the logger
    logger.addHandler(filehandler)

    # Make a class we can use to capture stdout and sterr in the log
    class CustomLogger(object):
            def __init__(self, logger, level):
                    """Needs a logger and a logger level."""
                    self.logger = logger
                    self.level = level

            def write(self, message):
                    # Only log if there is a message (not just a new line)
                    if message.rstrip() != "":
                            self.logger.log(self.level, message.rstrip())

    # Replace stdout with logging to file at INFO level
    sys.stdout = CustomLogger(logger, logging.INFO)
    # Replace stderr with logging to file at ERROR level
    sys.stderr = CustomLogger(logger, logging.ERROR)

    while True:
        update_dns(args.email, args.key, args.zone, dns_names)
        if not args.interval:
            break
        print("Waiting for {0} minute{1} before attempting another update...".format(args.interval, "" if args.interval == 1 else "s"))
        time.sleep(args.interval * 60)


def update_dns(email, key, zone, names):
    # update logic goes here
    global latest_ip
    records_updated = False
    public_ip = get_public_ip()
    logger = logging.getLogger(__name__)

    if public_ip != latest_ip:
        zone_id = get_zone_id(email, key, zone)

        for name in names:
            record_ip, record = get_record_ip_id(email, key, zone_id, name)
            if (record_ip != public_ip):
                log_message = "DNS record {0} with IP {1} doesn't match public IP {2}. Updating...".format(record["id"], record_ip, public_ip)
                print(log_message)
                #logger.info(log_message)
                update_successful = update_record_ip(email, key, zone_id, record["id"], record, public_ip)
                log_message = "DNS record updated successfully" if update_successful else "DNS record failed to update"
                print(log_message)
                #logger.info(log_message)
                records_updated = True

        latest_ip = public_ip
    
    if not records_updated:
        print("No updates necessary")

    return


def get_public_ip():
    # retrieve the current public IP address
    current_ip = ipgetter.myip()
    return current_ip


def get_record_ip_id(email, key, zone_id, name):
    # retrieve IP for the current record to determine if it needs to be updated
    request_headers = get_request_headers(email, key)
    response_json = requests.get("{0}zones/{1}/dns_records?type=A&name={2}".format(BASE_URL(), zone_id, name), headers=request_headers).json()
    if response_json["success"]:
        response_record = response_json["result"][0]
        return response_record["content"], response_record

    return None


def update_record_ip(email, key, zone_id, record_id, record, ip):
    # update IP for the current record
    request_headers = get_request_headers(email, key)
    request_data = {"type": "A", "name": record["name"], "content": ip, "proxied": record["proxied"]}
    response_json = requests.put("{0}zones/{1}/dns_records/{2}".format(BASE_URL(), zone_id, record_id), headers=request_headers, json=request_data).json()

    return response_json["success"]


def get_zone_id(email, key, zone):
    # retrieve the zone ID
    request_headers = get_request_headers(email, key)
    response_json = requests.get("{0}zones?name={1}&status=active".format(BASE_URL(), zone), headers=request_headers).json()

    if response_json["success"]:
        return response_json["result"][0]["id"]

    return None


def get_request_headers(email, key):
    return {"Content-Type": "application/json", "X-Auth-Email": email, "X-Auth-Key": key}


if __name__ == "__main__":
    main()