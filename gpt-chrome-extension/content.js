console.log("Hello World 1");

function extractEntitiesAndRelationships(text) {
    return new Promise(function(resolve, reject) {
        chrome.storage.sync.get(['apikey'],  function ({apikey}) {
    // Construct the API request
    const requestOptions = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apikey}`,
      },
      body: JSON.stringify({
        'model': 'gpt-3.5-turbo',
        'messages': [
          {
            'role': 'system',
            'content': `Extract disambiguated entities (with unique id derived from name, name and type) and their minimal semantic relationships (source, target, type)
            from the text and return them as a "nodes" and "links" JSON object only. Output no explanations or preamble just the plain JSON object.`,
          },
          {
            'role': 'user',
            'content': text,
          },
        ],
        'max_tokens': 3800,
        'temperature': 0.8,
      }),
    };
  
    fetch('https://api.openai.com/v1/chat/completions', requestOptions)
    .then(response => response.json())
    .then(d => {console.log(d);return d;})
    .then(json => JSON.parse(json.choices[0].message.content))
    .then(data => resolve(data))
    .catch(error => reject(error));
    });
    });
}
  

function sendToNeo4j({nodes, links}) {
  const nodeStatement = `
  UNWIND $nodes as node
  MERGE (n:Entity {id:node.id}) 
  SET n.name = node.name, n.type = node.type
  WITH n, node
  CALL apoc.create.addLabels(n,[node.type]) yield node as res
  RETURN count(*) as nodes`;
  
  queryNeo4j(nodeStatement, { nodes:nodes })
    .then((result) => {
      console.log('Added nodes:', result[0]["nodes"]);
      document.getElementById("output").innerText += `Added ${result[0]["nodes"]} nodes. `;
    })
    .catch((error) => {
      console.error('Error executing query:', error);
    });

    const relationshipStatement = `
    UNWIND $links as link
    MATCH (start:Entity {id:link.source}) 
    MATCH (end:Entity {id:link.target}) 
    WITH start, end, link
    CALL apoc.create.relationship(start,link.type, {}, end) yield rel
    RETURN count(*) as rels`;
    
    queryNeo4j(relationshipStatement, { links:links })
      .then((result) => {
        console.log('Added relationships:', result[0]["rels"]);
        document.getElementById("output").innerText += `Added ${result[0]["rels"]} rels. `;
      })
      .catch((error) => {
        console.error('Error executing query:', error);
      });
  
}

function recordToObject(record) {
    const obj = {};
    record.keys.forEach((key, index) => {
      obj[key] = record._fields[index];
    });
    return obj;
  }
  
    // Function to connect to Neo4j using the stored credentials and execute a query
function queryNeo4j(query, parameters) {
    return new Promise((resolve, reject) => {
      chrome.storage.sync.get(['uri', 'username', 'password'], function (items) {
        const uri = items.uri;
        const username = items.username;
        const password = items.password;
  
        if (!uri || !username || !password) {
          reject('Credentials not set. Please set them in the extension options.');
          return;
        }
  
        const driver = neo4j.driver(uri, neo4j.auth.basic(username, password), {disableLosslessIntegers:true});
        const session = driver.session();
  
        session
          .run(query, parameters)
          .then((result) => {
            const records = result.records.map(recordToObject);
            session.close();
            driver.close();
            resolve(records);
          })
          .catch((error) => {
            session.close();
            driver.close();
            reject(error);
          });
      });
    });
  }
  
function analyseText() {
    const selectedText = getSelectedText();
    document.getElementById("output").innerText = selectedText ? `Selected text: ${selectedText}` : 'No text selected';
    if (selectedText) {
        // analyse text
        const entities = extractEntitiesAndRelationships(selectedText)
        .then(entities => {
            console.log(entities);
            sendToNeo4j(entities);    
        })
        .catch( error =>
            console.log("Error extracting entities", error)
        );
    }
}

function createOverlay() {
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    overlay.style.zIndex = '9999';
    overlay.style.padding = '10px';
    overlay.style.display = 'flex';
    overlay.style.justifyContent = 'center';
  
    const container = document.createElement('p');
    container.id = 'output';
    container.style.backgroundColor = 'white';
    container.style.padding = '10px';
    container.style.borderRadius = '5px';
    container.style.width = '90%';
    container.style.height = '90%';

  
    const button = document.createElement('button');
    button.innerText = 'Get Selected Text';
    button.onclick = analyseText;
    
    overlay.appendChild(button);
    overlay.appendChild(container);
    document.body.appendChild(overlay);
  }
  
  function getSelectedText() {
    const selection = window.getSelection();
    const selectedText = selection.toString();
    return selectedText;
  }
  


  
// content.js
window.onload =  function () {
    createOverlay();
};