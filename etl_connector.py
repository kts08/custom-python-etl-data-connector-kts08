import os
import requests
import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()
mongo_uri = os.getenv("MONGO_URI")
mongo_db = os.getenv("MONGO_DB")

# MongoDB connection
client = MongoClient(mongo_uri)
db = client[mongo_db]
collection = db["rdap_raw"]

def extract(domain):
    url = f"https://rdap.org/domain/{domain}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching RDAP data for {domain}: {e}")
        return None

def transform(raw_data):
    if not raw_data:
        return None
    transformed = {
        "domainName": raw_data.get("ldhName"),
        "registrar": raw_data.get("registrar", {}).get("name") if isinstance(raw_data.get("registrar"), dict) else None,
        "status": raw_data.get("status", []),
        "nameServers": [ns.get("ldhName") for ns in raw_data.get("nameservers", []) if "ldhName" in ns],
        "events": {
            "created": next((e["eventDate"] for e in raw_data.get("events", []) if e["eventAction"] == "registration"), None),
            "updated": next((e["eventDate"] for e in raw_data.get("events", []) if e["eventAction"] == "last changed"), None)
        },
        "ingestedAt": datetime.datetime.utcnow().isoformat()
    }
    return transformed

def load(data):
    if data:
        collection.insert_one(data)
        print(f"Data for {data['domainName']} inserted successfully.")
    else:
        print("No data to load.")

def run_etl(domain_list):
    for domain in domain_list:
        raw = extract(domain)
        transformed = transform(raw)
        load(transformed)

if __name__ == "__main__":
    domains = ["google.com", "ssn.edu.in", "openai.com"]
    run_etl(domains)
