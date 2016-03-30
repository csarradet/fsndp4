<h2>Overview</h2>
<p>Google Cloud Endpoints implementation of the game Liar's Dice.</p>
<p>For a 60 second overview of how the game works, see <a href="https://www.youtube.com/watch?v=jEo1kvtOkcg">this video</a></p>.
<p>For a flowchart showing the turn structure of our version, see "p4_game_loop.png" in this repository.</p>

<h2>Initial Setup</h2>
<h4>Create a new App Engine project</h4>
<ul>
    <li>Update app.yaml to reflect your project name</li>
    <li>Deploy project using the Google App Engine launcher or command-line utilities</li>
</ul>

<h4>Allow the app to see your account and log it in the DB</h4>
<ul>
    <li>Access the live API explorer (https://##your_app_id##.appspot.com/_ah/api/explorer)</li>
    <li>Run the user.enroll method with OAuth 2.0 enabled</li>
</ul>

<h4>Flag your account as an admin</h4>
<ul>
    <li>Access console.developers.google.com (log in with the same account you used to create the project)</li>
    <li>From the dropdown in the top-left corner, click Datastore</li>
    <li>In the left sidebar, click Entities</li>
    <li>Click the entity matching your email address</li>
    <li>Change is_admin to True, then click save</li>
</ul>

<h2>Sample Game</h2>
<p>Follow along with this section to see the steps required to complete a game.  Note that we won't be stepping through every possible error condition, see the source code for that:</p>
<ul>
    <li>First, make sure you have access to a second Google account (for the second dummy player)</li>
    <li>Follow the setup steps above, then open a Chrome browser window</li>
    <li>Access the live API explorer (again)</li>
    <li>Browse to games.create. Submit your two Google account email addresses as the "email" fields of a "user_messages" envelope</li>
    <li>Copy the game ID that gets returned (in the "value" field)</li>
    <li>Browse to games.list and submit.  You should see your newly created game.</li>
    <li>Browse to games.lookup and submit with the game ID you copied earlier.  You should see the same game.  Note the "active_player", this should be the first account alphabetically.</li>    <li></li>
    <li>Open an incognito tab in Chrome (ctrl+shift+N on Windows).  Browse to the API again and log in with your second account.</li>
    <li>As the active player, browse to games.hand.get to see your current hand.</li>
    <li>Browse to games.bids.create and place a new bid (e.g. 1x1).</li>
    <li></li>
    <li></li>
    <li></li>
    <li></li>
    <li></li>
    <li></li>
    <li></li>
</ul>
