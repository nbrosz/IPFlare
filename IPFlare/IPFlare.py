
#!/usr/bin/python3

import argparse
import time
import ipgetter
import requests

latest_ip = None

#constants
def BASE_URL():
    return "https://api.cloudflare.com/client/v4/"

def main():

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

    args = parser.parse_args()

    dns_names = args.names.split(",")

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

    if public_ip != latest_ip:
        zone_id = get_zone_id(email, key, zone)

        for name in names:
            record_ip, record = get_record_ip_id(email, key, zone_id, name)
            if (record_ip != public_ip):
                print("DNS record {0} with IP {1} doesn't match public IP {2}. Updating...".format(record["id"], record_ip, public_ip))
                update_successful = update_record_ip(email, key, zone_id, record["id"], record, public_ip)
                print("DNS record updated successfully" if update_successful else "DNS record failed to update")
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