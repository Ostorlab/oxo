import os
import json


def generate_kb(config):
    guide_nav = [c for c in config['nav'] if c.get('Guide') is not None][0]
    kb = []
    kbvulnz_path = os.getcwd() + '/../kbvulnz/'
    directory = os.fsencode(kbvulnz_path)
    for file in os.listdir(directory):
        if file == b'.git':
            print("pass .git")
            continue
        vuln_folder_name = os.fsdecode(file)
        folder_path = f'{kbvulnz_path}{vuln_folder_name}'
        if os.path.isdir(folder_path):
            # description
            if os.path.isfile(f'{folder_path}/description.md'):
                with open(f'{folder_path}/description.md') as f:
                    description = f.read()
            else:
                pass
            # recommendation
            if os.path.isfile(f'{folder_path}/recommendation.md'):
                with open(f'{folder_path}/recommendation.md') as f:
                    recommendation = f.read()
            else:
                pass
            # metadata
            if os.path.isfile(f'{folder_path}/meta.json'):
                meta_file = open(f'{folder_path}/meta.json')
                metadata = json.load(meta_file)
            else:
                pass

            vuln_md_folder = f"{os.getcwd()}/docs/kb/{vuln_folder_name}.md"
            read_me = open(f'{vuln_md_folder}', 'w')
            links = f""""""
            for value, key in metadata["references"].items():
                links += f""" * [{value}]({key})\n"""

            md = f"""
## {metadata["title"]} 
<button> Risk: <code class='{metadata['risk_rating']}'> 
{metadata['risk_rating']} </code>
</button> 

#### Description
{description}
            
#### Recommendation
{recommendation}

#### Links
{links}


"""
            read_me.write(md)
            kb.append({metadata['title']: f"kb/{vuln_folder_name}.md"})
    guide_nav['Guide'].append({'Knowledge Base': kb})
