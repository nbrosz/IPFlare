
#!/usr/bin/python3

import argparse
import time

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
        time.sleep(args.interval * 60)


def update_dns(username, password, names):
    # update logic goes here
    return


if __name__ == "__main__":
    main()