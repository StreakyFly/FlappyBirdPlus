# FlappyBirdPlus
Upgraded Flappy Bird with health, guns & enemies, controlled by AI agents.

Not developed for commercial purposes, only for fun and learning.

[PLACEHOLDER FOR THE VIDEO OF THE CURRENT PROGRESS]

Inventory backgrounds and some item icons are placeholders and will be replaced.

# TODO:
0. make fighting enemies a bit easier and more fun! (fighting CloudSkimmers is too hard)
1. barely touching the top/bottom of a pipe shouldn't immediately kill the bird, but only slightly damage it
2. add animation for reloading guns, bullet collisions (sparks, tiny explosions), enemy deaths and other items 
3. sound effects for like uhh... everything
4. multiple types of enemies (controlled by trained agents)
5. 3rd inventory slot - small robots that help the player?
6. main menu with a global leaderboard (data stored in a database)
7. more items, like potions, heals, weapons and special items
8. occasional traps...? Probably not.
9. Figure out how to run the game in a browser, possibly with pygbag https://pypi.org/project/pygbag/
10. and more...

<br/>

Training the CloudSkimmer AI agents: WIP

Training the SkyDart AI agents: TBD

Training the robot AI agents: TBD

<br/>

Training the Player AI agent (once the game is complete):

Input:
 - player position, rotation, health & shield
 - pipes y center position
 - enemy positions, their type and health
 - positions and velocities of bullets the player fired
 - positions and velocities of other bullets (excluding those that already hit the floor)
 - spawned item positions
 - gun stats & bullet stats
 - quantity of the 3rd slot item and its type whatever it may be
 - quantity of potions and their type
 - quantity of heals and their type
 - quantity of special items and their type
 - ... and possibly more

Output:
 - jump or not
 - fire, reload or do nothing
 - use the 3rd slot item or not
 - use a potion or not
 - use a heal or not

The agent should be rewarded every time they pass a pipe/the score increases.
It should also be rewarded for hitting enemies, and punished for getting hit.
Maybe also reward it when the bird has high health and shield, and punish it when they're low?
To be determined.

<br/>

Credits:
 - Part of the basic Flappy Bird code is from https://github.com/sourabhv/FlapPyBird, but it was later heavily modified and expanded upon.
