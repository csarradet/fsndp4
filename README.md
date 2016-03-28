Setup steps:

Create a new App Engine project
Update app.yaml to reflect your project name
Deploy project

Allow the app to see your account and log it in the DB:
Access the live API explorer (https://##your_app_id##.appspot.com/_ah/api/explorer) and run the create_user query with OAuth 2.0 enabled and an empty request body

Flag your account as an admin (log in with the same account you used to create the project):
Access console.developers.google.com
From the dropdown in the top-left corner, click Datastore
In the left sidebar, click Entities
Click the entity matching your email address
Change is_admin to True, then click save




