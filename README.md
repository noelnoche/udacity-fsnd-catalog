Catalog
===
<br>

Synopsis
---
Catalog is a basic information organizing web service with a clean and 
simple interface. It is made to demonstrate implementation of common 
concepts used in full stack projects, including:

1. persistent data storage
2. CRUD operations mapped to HTTP methods
3. third-party OAuth authentication
4. password-based login
5. RESTful API


Demo link
---
[https://www.youtube.com/watch?v=dcgpyX5Ld94&feature=youtu.be](https://www.youtube.com/watch?v=dcgpyX5Ld94&feature=youtu.be)


Requirements
---
+ Python 2.7.x
+ VirtualBox
+ Vagrant
+ See the _requirements.txt_ file for project-specific requirements.
+ Note that all the packages in the _requirement.txt_ file are installed
  by the Vagrantfile when `vagrant up` is first run.


Setting Up Third-party Login
---
You will need to register this application with a service below to enable
the OAuth login feature. After registering, you need to obatin the necessary keys
and tokens to fill in _client\_secrets_ JSON files in the _login_ directory.
Useful links are provided in the Reference section.
<br>

**Google Plus**

1. Go to the Google Cloud Console page.
2. Create a project (see Reference section for details).
3. Click the menu icon to open the left panel in the Dashboard screen.
4. Select "APIs & services" then "Credentials".
5. Click "Create credentials" and select "OAuth client ID".
6. Select "Web application".
7. Fill in the Name field (credentials label).
8. Under Authorized redirect URIs and Authorized JavaScript origins add `http://localhost:8000/`.
9. Click "Create".
10. In the Credentials screen, click the credentials you just created.
11. Add the Client ID, Client secret and project ID to the `client\_secrets_gpl.json` file.
12. Add the Client ID as the `client_id` value in the _login\_main.html_ file.

**Facebook**

1. Go the Facebook for Developers page.
2. Click "Add a New App".
3. Click "Settings" on the left panel.
4. Fill in the Display Name field.
5. Copy the App ID and App Secret to the `client\_secrets_fb.json` file.
6. Add the App ID as the `appId` value in the _login.html_ file.
6. Under Products in the left panel click "Add Product".
7. Choose "Facebook Login" and go its settings screen.
8. In Valid OAuth redirect URIs field add `http://localhost:8000/`.
9. Click "Save Changes".

**Twitter**

1. Go the the Twitter App Managment page.
2. Click "Create New App".
3. Under the Settings tab, fill in all the fields and select both boxes at the end.
4. For the Callback URL use `http://localhost:8000/user/auth_twt`.
5. Go to the Keys and Access Tokens tab.
6. Generate the keys and tokens and add them to the `client\_secrets_twt.json` file.
7. Go to the Permissions tab.
8. Select "Read Only" and "Request email addresses from users."
9. Click "Update Settings".


Development Environment Setup
---
1. Install VirtualBox (See Reference section for link).
2. Install Vagrant (See Reference section for link).
3. Create a directory called _vagrant_.
4. Download the project repo and open it.
5. Place the repo content inside the _vagrant_ directory.


Installation & Usage
---
1. Open your terminal application.
2. `cd` to the vagrant directory and run `vagrant up`.
   (Installs the Linux OS and project dependencies when first run)
3. Run the following commands:
    + `vagrant ssh`  
    + `cd /vagrant `  
    + `cd /catalog `  
4. Open a second terminal.
5. `cd` to the vagrant directory.
6. Repeat step 3.
7. Run `redis-server`
8. Go back to the first terminal and run:  
    + `python catalog/db_setup` (do this only once)
    + `python run.py`
9. Open your web browser to `http://localhost:8000/catalog`


API: Request/Response Details
---

|     |     |
| --- | --- |
| **Endpoint** | catalog/api/1.0 |
| **Request type** | GET |
| **Response type** | JSON |
| **Rate limited** | Yes |
| **Requests / 30-sec window** | 300 |


API: Optional Parameters
---

| Parameter | Value | Action |
| --- | --- | --- |
| None | N/A | Returns all items grouped by category |  
| user_id | < number > | Restricts data to a specific user |  
| q | categories or items | Returns only categories or items respectively |  
| search | < item name > | Find a specific item by name |  
| limit | < number > | Limits the number of results |  


API: Request & Response Example
---

        http://localhost:8000/catalog/api/1.0/?q=items&&user_id=1

        {
        "data": [
            {
            "category": "Mystical creatures", 
            "description": "Vivamus erat lorem, blandit sed eros id...", 
            "id": 2, 
            "name": "Unicorn", 
            "user_id": 1
            }, 
            {
            "category": "Unsorted", 
            "description": "Lorem ipsum dolor sit amet, consectetur...", 
            "id": 1, 
            "name": "Eskimo", 
            "user_id": 1
            }
        ], 
        "response": "Data found.", 
        "status": "200"
        }


Credits
---
Code in _rlimiter_ folder and _hungryrequests.py_ script provided by [Udacity](https://www.udacity.com)


License
---
Code provided under an [MIT license](https://github.com/noelnoche/udacity-fsnd-logs-analysis-website/blob/gh-pages/LICENSE.md)


Reference
---
+ [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
+ [Vagrant](https://www.vagrantup.com/downloads.html)
+ [PostgreSQL for Development with Vagrant](https://wiki.postgresql.org/wiki/PostgreSQL_For_Development_With_Vagrant)
+ [Google Cloud Console](https://console.cloud.google.com/)
+ [Creating a Google Project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
+ [Facebook for Developers ](https://developers.facebook.com/)
+ [Twitter App Management](https://apps.twitter.com/)
