#Welcome to ostorlab.

<figure markdown> 
![analysis](../public/Ostorlab-sm.png){a}
</figure>

<figure markdown> 
[Get started](#){ . .md-button--primary .md-button }
</figure>

##features
###Android and iOS
Support for native Android and iOS applications as well as 12 multi-platform framework.
###Advanced Analysis
Powered by static taint analysis engine, debugger-powered dynamic analysis and smart fuzzing. 
###Detailed Report
All findings provide technical description, recommendation, references, CVSSv3 score and technical details.

### Powerful & Simple API

```python
import requests
import json


query = '''
query {
  allScans {
    scans {   
      id
      title
      progress
    }
  }
}
'''

# Retrieve authentication token.
request = requests.post(url='https://ostorlab.co/apis/token/',
                       json={"username":"user1","password":"pass1"})
json_data = json.loads(request.text)
if "token" in json_data:
   token = json_data["token"]
   # Set token in Authorization header.
   headers = {"Authorization": f"Token {token}"}
   # Post query request.
   request = requests.post(url='https://ostorlab.co/apis/graphql_token/',
                           json={"query": query},
                           headers=headers)
   print(request.json())
```
