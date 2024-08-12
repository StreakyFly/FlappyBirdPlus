# FlappyBirdPlus
Upgraded Flappy Bird with health, guns & enemies, controlled by AI agents.

Not developed for commercial purposes, only for fun and learning.

[PLACEHOLDER FOR THE VIDEO OF THE CURRENT PROGRESS]

# TODO:
0. add animation for reloading guns, bullet collisions (sparks, tiny explosions) and other items 
1. sound effects for like uhh... everything
1. multiple types of enemies (controlled by trained agents)
2. 3rd inventory slot - small robots that help the player?
3. main menu with a global leaderboard (connected to a database)
4. more items, like potions, heals, weapons and special items
5. occasional traps...? Probably not.
6. Figure out how to run the game in a browser, possibly with pygbag https://pypi.org/project/pygbag/
7. and more...

<br/>

Training the CloudSkimmer AI agents:

Input:
 - player position
 - enemy positions (so they won't fire at them or other enemies)
 - current weapon rotation
 - pipes y center position
 - gun type & bullet speed
 - fired bullet positions (only bullets they fired)

Output:
 - rotation - rotate the weapon up or down or do nothing
 - fire, reload or do nothing

The agent should be rewarded when their bullet hits the player, and penalized when it hits them or another enemy.
Should there be random cooldowns here and there, so CloudSkimmers don't constantly fire?
To be determined.


<br/>

Training the SkyDart AI agents: TBD

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
 - fire or not
 - reload or not
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
