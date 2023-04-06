document.addEventListener('DOMContentLoaded', function () {
    loadOptions();
    document.getElementById('save').addEventListener('click', saveOptions);
  });
  
  function saveOptions() {
    const uri = document.getElementById('uri').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const apikey = document.getElementById('apikey').value;
    const options = {
        uri: uri,
        username: username,
        password: password,
        apikey: apikey
      };
    chrome.storage.sync.set(
      options,
      function () {
        console.log('Options saved.');
      }
    );
  }
  
  function loadOptions() {
    chrome.storage.sync.get(['uri', 'username', 'password','apikey'], function (items) {
      if (items.uri) {
        document.getElementById('uri').value = items.uri;
      }
      if (items.username) {
        document.getElementById('username').value = items.username;
      }
      if (items.password) {
        document.getElementById('password').value = items.password;
      }
      if (items.apikey) {
        document.getElementById('apikey').value = items.apikey;
      }
    });
  }
  