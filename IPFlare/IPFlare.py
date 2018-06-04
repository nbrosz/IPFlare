
#!/usr/bin/python3

import argparse
import time
import ipgetter

latest_ip = None

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("username",
                        help="the username for Cloudflare")
    parser.add_argument("password",
                        help="the password for Cloudflare")
    parser.add_argument("names", 
                        help="update the given comma-separted list of DNS record names")
    parser.add_argument("-i", "--interval",
                        help="interval in minutes to re-run the update",
                        type=int)

    args = parser.parse_args()

    dns_names = args.names.split(",")

    while True:
        update_dns(args.username, args.password, dns_names)
        if not args.interval:
            break
        print("Waiting for {0} minute{1} before attempting another update...".format(args.interval, "" if args.interval == 1 else "s"))
        time.sleep(args.interval * 60)


def update_dns(username, password, names):
    # update logic goes here
    global latest_ip
    public_ip = get_public_ip()
    print("IP is {0}".format(public_ip))

    if public_ip != latest_ip:
        print("IP don't match. Updating.")
        for name in names:
            record_ip = get_record_ip(username, password, name)
            if (record_ip != public_ip):
                update_record_ip(username, password, name, public_ip)

        latest_ip = public_ip
        print("IPs updated.")
    return


def get_public_ip():
    # retrieve the current public IP address
    current_ip = ipgetter.myip()
    return current_ip


def get_record_ip(username, password, name):
    # retrieve IP for the current record to determine if it needs to be updated
    return '0.0.0.0'


def update_record_ip(username, password, name, ip):
    # update IP for the current record
    return


if __name__ == "__main__":
    main()