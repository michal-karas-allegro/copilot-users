import asyncio
import csv
import logging
from dataclasses import dataclass
import httpx

PEOPLE_API_URL = "https://people.allegrogroup.com/api/people"

GITHUB_RUNNER_GATEWAY_URL = "https://github-runner-gateway-dev.allegrogroup.com"

AUTH_TOKEN = "your_auth_token"  # from https://auth-service-self-service.allegrogroup.com/token/

CONCURRENCY_LIMIT = 20

CSV_FILE_NAME = "copilot_people_data.csv"

logging.basicConfig(level=logging.INFO)


@dataclass
class PeopleResponse:
    personNumber: str
    name: str
    email: str
    position: str
    has_license: bool


async def fetch_person_license(
    client: httpx.AsyncClient, semaphore: asyncio.Semaphore, person: dict
) -> PeopleResponse:
    person_number = person["personNumber"]
    url = f"{GITHUB_RUNNER_GATEWAY_URL}/copilot/billing/budgets/user?personNumber={person_number}"
    has_license = False

    async with semaphore:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                has_license = data.get("exists", False)
            else:
                logging.warning(
                    f"Failed status {response.status_code} for personNumber: {person_number}"
                )
        except Exception as e:
            logging.error(f"Error fetching data for {person_number}: {e}")

    return PeopleResponse(
        personNumber=person_number,
        name=person.get("displayName", ""),
        email=person.get("email", ""),
        position=person.get("title", ""),
        has_license=has_license,
    )


async def main():
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        logging.info("Fetching people list...")
        people_response = await client.get(PEOPLE_API_URL)
        people_list = people_response.json()

        logging.info(f"Processing {len(people_list)} users concurrently...")
        tasks = [fetch_person_license(client, semaphore, person) for person in people_list]
        people_data = await asyncio.gather(*tasks)

    with open(CSV_FILE_NAME, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["personNumber", "name", "email", "position", "has_license"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for person in people_data:
            writer.writerow(person.__dict__)

    logging.info(f"Successfully exported data to {CSV_FILE_NAME}")


if __name__ == "__main__":
    asyncio.run(main())
