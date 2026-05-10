import requests
import json
import os
import re
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader
from slugify import slugify

class TeachingGuideImprover:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://zenodo.org/api/records"
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.env = Environment(loader=FileSystemLoader('templates/teaching_guides'))

    def fetch_records(self, query: str = 'title:"Teaching Guide" AND creators.name:"de la Serna Tuya, Juan Moisés"', size: int = 10) -> List[Dict]:
        params = {"q": query, "size": size}
        response = requests.get(self.base_url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()["hits"]["hits"]

    def improve_record(self, record: Dict, output_dir: str):
        metadata = record["metadata"]
        title = metadata["title"]
        doi = record.get("doi", "N/A")
        orcid = "0000-0002-8401-8018"

        # Extract language and topic from title
        lang_match = re.search(r"\(([^)]+)\)", title)
        language = lang_match.group(1) if lang_match else "English"
        topic = title.split(":")[-1].strip()

        # Use python-slugify for better international support
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

        # Generate files using templates
        templates = [
            ("teaching_guide_extended.md.j2", "teaching_guide_extended.md"),
            ("student_activity_sheet.md.j2", "student_activity_sheet.md"),
            ("instructor_guide.md.j2", "instructor_guide.md"),
            ("quickstart.md.j2", "quickstart.md"),
            ("ethics_discussion.md.j2", "ethics_discussion.md")
        ]

        for template_name, output_name in templates:
            template = self.env.get_template(template_name)
            content = template.render(**render_data)
            self._write_file(record_dir, output_name, content)

    def _get_context(self, topic: str) -> str:
        if "sleep" in topic.lower() or "sueño" in topic.lower():
            return "This dataset explores the relationship between lifestyle factors and sleep quality in adolescent populations."
        elif "covid" in topic.lower():
            return "This dataset provides insights into the psychological impact of the COVID-19 pandemic across different regions."
        return f"This dataset provides a foundation for practicing data analysis and interpretation within the context of {topic}."

    def _write_file(self, directory: str, filename: str, content: str):
        with open(os.path.join(directory, filename), "w", encoding="utf-8") as f:
            f.write(content)

if __name__ == "__main__":
    # Use environment variable for API key instead of hardcoding
    import sys
    api_key = os.environ.get("ZENODO_API_KEY")
    if not api_key:
        print("Warning: ZENODO_API_KEY environment variable not set. Using provided key for this session only if available.")
        # For the purpose of this task, I'll allow passing it as an argument or using the one from previous context if needed,
        # but the code should not have it hardcoded.
        if len(sys.argv) > 1:
            api_key = sys.argv[1]
        else:
            print("Error: No API key provided. Run with ZENODO_API_KEY=your_key python scripts/improve_teaching_guides.py")
            sys.exit(1)

    improver = TeachingGuideImprover(api_key)

    print("Fetching records...")
    try:
        records = improver.fetch_records(size=5)
    except Exception as e:
        print(f"Failed to fetch records: {e}")
        sys.exit(1)

    output_base = "improved_teaching_guides"
    os.makedirs(output_base, exist_ok=True)

    for record in records:
        print(f"Improving: {record['metadata']['title']}")
        improver.improve_record(record, output_base)

    print(f"Done! Improved guides are in the '{output_base}' directory.")
