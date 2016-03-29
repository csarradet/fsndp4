<h1>Overview</h1>
Google Cloud Endpoints implementation of the game Liar's Dice.
For an overview of how the game works, see <a href="https://www.youtube.com/watch?v=jEo1kvtOkcg">this 60 second intro</a>


<h1>Initial Setup</h1>
<h3>Create a new App Engine project</h3>
Update app.yaml to reflect your project name
Deploy project


<h3>Allow the app to see your account and log it in the DB</h3>
Access the live API explorer (https://##your_app_id##.appspot.com/_ah/api/explorer) and run the user.enroll method with OAuth 2.0 enabled


<h3>Flag your account as an admin</h3>
Access console.developers.google.com (log in with the same account you used to create the project)
From the dropdown in the top-left corner, click Datastore
In the left sidebar, click Entities
Click the entity matching your email address
Change is_admin to True, then click save




