import os
import pandas as pd
import json
import hashlib
from data_logger import Data_Logger, file_exists


def generate_id(string: str) -> str:
    """Generate a unique ID by hashing a string."""
    return hashlib.md5(string.encode()).hexdigest()


class Graph:
    '''
    Graph class builds a JSON structure of nodes and links from a CSV using Data_Logger.
    Each entry and each tag become nodes; links connect entries to tags and tags to parent tags.
    '''
    def __init__(self, csv_path: str, json_path: str):
        self.csv_path = csv_path
        self.json_path = json_path
        self.logger = Data_Logger(self.csv_path)

    def make_file(self):
        """Creates the JSON file if it does not exist."""
        if not file_exists(self.json_path):
            struct = {
                "nodes": [],
                "links": []
            }
            with open(self.json_path, 'w') as f:
                json.dump(struct, f, indent=1)

    def populate_json_from_csv(self):
        df = pd.read_csv(self.csv_path)
        struct = {
            "nodes": [],
            "links": []
        }

        tag_ids = {}
        entry_ids = set()

        # 1. Create nodes for tags
        for tag in self.logger.get_all_tags_and_count():
            tag_id = generate_id(tag)
            tag_ids[tag] = tag_id
            struct["nodes"].append({
                "id": tag_id,
                "user": "admin",
                "title": tag,
                "link": None,
                "type": "[TAG]"
            })

            # Add links between nested tags (e.g. A/B/C -> A/B)
            parts = tag.split("/")
            if len(parts) > 1:
                parent = "/".join(parts[:-1])
                if parent in tag_ids:
                    struct["links"].append({
                        "source": tag_id,
                        "target": tag_ids[parent],
                        "type": "[TAG]"
                    })

        # 2. Create nodes for entries and links from entries to tags
        for _, row in df.iterrows():
            title = row["Name"]
            tag = row["Tag"]
            link = row["Link"]
            entry_id = generate_id(title)

            # Avoid duplicate entry nodes
            if entry_id not in entry_ids:
                struct["nodes"].append({
                    "id": entry_id,
                    "user": "admin",
                    "title": title,
                    "link": link,
                    "type": "[ENTRY]"
                })
                entry_ids.add(entry_id)

            # Add links to all levels of the tag hierarchy
            for hierarchical_tag in self.logger.make_tags(tag):
                if hierarchical_tag in tag_ids:
                    struct["links"].append({
                        "source": entry_id,
                        "target": tag_ids[hierarchical_tag],
                        "type": "[ENTRY]"
                    })

        # Save to JSON file
        with open(self.json_path, 'w') as f:
            json.dump(struct, f, indent=2)


if __name__ == "__main__":
    csv_path = "./data.csv"     
    json_path = "./output_graph.json"

    g = Graph(csv_path, json_path)
    g.make_file()
    g.populate_json_from_csv()

    print(f"Graph generated and saved to {json_path}")
