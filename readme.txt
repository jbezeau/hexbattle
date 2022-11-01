# zip up application.py, board.py, dbconnect.py and requirements.txt for deployment to elastic beanstalk
# install requests and pygame manually to run the UI components

Hex Battle:

    The objective is to use your pieces to eliminate all the enemy or capture their flag

Deploy the game:
    Run application.py to start a flask server that hosts the game board instance.
    Run session.py to start the game launcher,
        or you can just start edit.py to set up a scenario and then run display.py to play out turns
    Run simpleplayer.py to watch the computer do battle with itself!
        The play function defined in simpleplayer will be introduced as an opponent option for humans soon.

UI Guide:
    Session.py: edit your player ID, search for unfinished games to resume in Sessions or create a new Scenario to play
    Edit.py: raise and lower terrain (can't be moved on) and place additional tokens on the board
    Display.py: play the game by moving tokens of your color and clicking end turn to let the next player go
    As a general UI convention, tapping on any non-UI element of the screen will revert selections / show main menu

Play guide:
    Soldiers (triangles) can move one space and shoot with a range of two spaces. Soldiers capture enemy pieces on their move.
    Tanks (squares) can move three spaces and shoot four spaces. Tanks can not capture like Soldiers do.
    Flags (pentagons) do not act. If your flag is captured by a Soldier, all of your pieces will change to the captor's side.
    Terrain (brighter or darker hexes) can not be used for movement by any troops.

