# FlappyBirdPlus
Upgraded Flappy Bird with health, guns & enemies! Trained 'AI' included.

Part of the basic Flappy Bird code stolen from https://github.com/sourabhv/FlapPyBird


<br/>


Would it be possible to run the game in a browser? With pygbag?
https://pypi.org/project/pygbag/

# TODO:

1. guns - add animation and sound for shooting and reloading
2. multiple types of enemies controlled by trained agents
3. 3rd inventory slot - maybe add hunger and food? Or some other item type.
4. traps...?
5. make the scene speed easily adjustable

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
 - rotation - rotate up or down
 - fire or not

The agent should be rewarded when their bullet hits the player, and penalized when it hits them or another enemy.

Reloading will not be done by AI, but can be coded to happen randomly, so it doesn't always use the entire magazine.
There should also be random cooldowns here and there, so they don't constantly fire.


<br/>

Training the SkyDart AI agents: TBD


<br/>

Only after the entire game is complete! =>
Training the Player AI agent:

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
If that's too simple, also try rewarding it for hitting enemies, and punish it for getting hit.
Maybe also reward it when the bird has high health and shield, and punish it when they're low, although I'm not sure this is a good idea.
