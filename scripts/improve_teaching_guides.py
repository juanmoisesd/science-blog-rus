import requests
import json
import os
import re
import time
from datetime import datetime
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader
from slugify import slugify

class TeachingGuideImprover:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://zenodo.org/api"
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.env = Environment(loader=FileSystemLoader('templates/teaching_guides'))

    def fetch_records(self, query: str = 'title:"Teaching Guide" AND creators.name:"de la Serna Tuya, Juan Moisés"', size: int = 10) -> List[Dict]:
        params = {"q": query, "size": size, "sort": "mostrecent"}
        response = requests.get(f"{self.base_url}/records", params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()["hits"]["hits"]

    def improve_record(self, record: Dict, output_dir: str) -> List[str]:
        metadata = record["metadata"]
        title = metadata["title"]
        doi = record.get("doi", "N/A")
        orcid = "0000-0002-8401-8018"

        lang_match = re.search(r"\(([^)]+)\)", title)
        language = lang_match.group(1) if lang_match else "English"
        topic = title.split(":")[-1].strip()

        slug = slugify(title)
        record_dir = os.path.join(output_dir, slug)
        os.makedirs(record_dir, exist_ok=True)

        context = self._get_context(topic)

        render_data = {
            "title": title,
            "doi": doi,
            "orcid": orcid,
            "language": language,
            "topic": topic,
            "context": context
        }

        templates = [
            ("teaching_guide_extended.md.j2", "teaching_guide_extended.md"),
            ("student_activity_sheet.md.j2", "student_activity_sheet.md"),
            ("instructor_guide.md.j2", "instructor_guide.md"),
            ("quickstart.md.j2", "quickstart.md"),
            ("ethics_discussion.md.j2", "ethics_discussion.md")
        ]

        generated_files = []
        for template_name, output_name in templates:
            template = self.env.get_template(template_name)
            content = template.render(**render_data)
            filepath = os.path.join(record_dir, output_name)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            generated_files.append(filepath)

        return generated_files

    def get_or_create_draft(self, record_id: str) -> str:
        rec_resp = requests.get(f"{self.base_url}/records/{record_id}", headers=self.headers)
        rec_resp.raise_for_status()
        rec_data = rec_resp.json()
        concept_id = rec_data.get("conceptrecid")

        drafts_resp = requests.get(f"{self.base_url}/deposit/depositions",
                                   params={"q": f"conceptrecid:{concept_id}"},
                                   headers=self.headers)
        drafts_resp.raise_for_status()
        drafts = drafts_resp.json()

        for d in drafts:
            if d.get("state") == "unsubmitted":
                print(f"Found existing draft {d['id']} for concept {concept_id}")
                return str(d["id"])

        print(f"Creating new version for record {record_id}...")
        new_version_url = f"{self.base_url}/deposit/depositions/{record_id}/actions/newversion"
        resp = requests.post(new_version_url, headers=self.headers)
        resp.raise_for_status()

        latest_draft_url = resp.json()["links"]["latest_draft"]
        return latest_draft_url.split("/")[-1]

    def publish_improved_version(self, record_id: str, files_to_upload: List[str]):
        draft_id = self.get_or_create_draft(record_id)

        draft_resp = requests.get(f"{self.base_url}/deposit/depositions/{draft_id}", headers=self.headers)
        draft_resp.raise_for_status()
        draft_data = draft_resp.json()

        metadata = draft_data["metadata"]
        metadata["publication_date"] = datetime.now().strftime("%Y-%m-%d")

        if "imprint_publisher" in metadata:
            del metadata["imprint_publisher"]

        update_resp = requests.put(
            f"{self.base_url}/deposit/depositions/{draft_id}",
            data=json.dumps({"metadata": metadata}),
            headers={**self.headers, "Content-Type": "application/json"}
        )
        if update_resp.status_code != 200:
            print(f"Warning: Metadata update failed: {update_resp.text}")

        bucket_url = draft_data["links"]["bucket"]

        for filepath in files_to_upload:
            filename = os.path.basename(filepath)
            print(f"Uploading {filename}...")
            with open(filepath, "rb") as fp:
                r = requests.put(f"{bucket_url}/{filename}", data=fp, headers=self.headers)
                r.raise_for_status()

        print(f"Publishing draft {draft_id}...")
        publish_url = f"{self.base_url}/deposit/depositions/{draft_id}/actions/publish"
        publish_resp = requests.post(publish_url, headers=self.headers)

        if publish_resp.status_code != 202:
            if publish_resp.status_code == 400:
                 draft_resp = requests.get(f"{self.base_url}/deposit/depositions/{draft_id}", headers=self.headers)
                 metadata = draft_resp.json()["metadata"]
                 metadata["publication_date"] = datetime.now().strftime("%Y-%m-%d")
                 requests.put(f"{self.base_url}/deposit/depositions/{draft_id}",
                              data=json.dumps({"metadata": metadata}),
                              headers={**self.headers, "Content-Type": "application/json"})
                 publish_resp = requests.post(publish_url, headers=self.headers)

        publish_resp.raise_for_status()
        print(f"Successfully published improved version {draft_id}")
        return publish_resp.json()

    def _get_context(self, topic: str) -> str:
        if "sleep" in topic.lower() or "sueño" in topic.lower():
            return "This dataset explores the relationship between lifestyle factors and sleep quality in adolescent populations."
        elif "covid" in topic.lower():
            return "This dataset provides insights into the psychological impact of the COVID-19 pandemic across different regions."
        return f"This dataset provides a foundation for practicing data analysis and interpretation within the context of {topic}."

if __name__ == "__main__":
    import sys
    api_key = os.environ.get("ZENODO_API_KEY")
    if not api_key:
        if len(sys.argv) > 1:
            api_key = sys.argv[1]
        else:
            print("Error: ZENODO_API_KEY environment variable not set.")
            sys.exit(1)

    improver = TeachingGuideImprover(api_key)

    print("Fetching records...")
    try:
        records = improver.fetch_records(size=10)
    except Exception as e:
        print(f"Failed to fetch records: {e}")
        sys.exit(1)

    output_base = "improved_teaching_guides"
    os.makedirs(output_base, exist_ok=True)

    for record in records:
        record_id = str(record["id"])
        title = record['metadata']['title']
        print(f"\n--- Processing: {title} (ID: {record_id}) ---")

        files = improver.improve_record(record, output_base)

        try:
            improver.publish_improved_version(record_id, files)
            print(f"Completed {title}")
            time.sleep(2) # Throttle
        except Exception as e:
            print(f"Error processing {title}: {e}")
            continue

    print(f"\nDone!")
