Export Microsoft To Do database from Chrome
==

Required software: Chrome web browser, Notepad++

## 1.
Open https://to-do.office.com/ in Chrome. Leave the tab open a couple of minutes. This gives To Do time to load data in the background.

## 2.
Press F12 to open the Chrome developer tools. Open the Console tab and paste this line at the prompt (">") at the bottom:

    indexedDB.databases().then(r => console.log(r))

## 3.
A new entry should appear in the console. Click to expand it and look for "name". Copy the name - it should look something like:

    todo_5b7dcc49-a24e-48f4-9424-1f17da827b54

## 4.
In another browser tab, open: https://gist.githubusercontent.com/loilo/ddfdb3c54fa474a89f71ce0660cd38b7/raw/f9c33c6ff4b091942350ec70ad3863676e4f0dc6/export.js

Copy the whole script, go back developer tools in your To Do tab, and paste the script in the Console.

##  5.
When asked for the name of the database, paste the todo_xxx name you saved earlier.

## 6.
You should see some stuff in the Console followed by a button named "Copy". Click Copy.

## 7.
Open Notepad++. Paste the contents of your clipboard. Save as a file called "microsoft_todo.json"