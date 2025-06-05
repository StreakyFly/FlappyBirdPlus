# ⚠️ WARNING: Don't call `super().perform_step()` in your environment code!

Doing so can easily mess up your other logic, leading to extremely anti-debuggable bugs.
Trust me. You will shoot yourself in the foot, and **the worst part is you won't even realize you did**.


---


**Example: The Curious Case of Collapsing Policy**

When I continued training from the step2 checkpoint in the step3 env, the agent's performance collapsed.
By the end of step2, the agent had rewards around ~180, but in step3, they dropped to ~0 after just a few iterations.

At first, I thought it was because of harsh punishments for hitting teammates—the agent had simply become too scared to fire at all.
Turns out, I was completely off.

**The real issue was this:**

The `calculate_reward()` method needs `self.all_bullets_from_last_frame` to determine which entities the bullets hit.
At the end of the `calculate_reward()`, right before returning, I updated `self.all_bullets_from_last_frame` with the current frame's bullets so it would be ready for the next step.

In `enemy_cloudskimmer_simple_step3_env.py`, I called `super().perform_step()` early in `perform_step()`, wanting to reuse the main step logic.
Then, I added extra logic afterward and recalculated info, like the observation and reward at the end, thinking that was fine.

**But!**

`super().perform_step()` also calls `calculate_reward()`.
So `calculate_reward()` was called twice each step:

1. Once by `super().perform_step()`, updating `self.all_bullets_from_last_frame` with the *current* frame's bullets.
2. Again at the end of my own `perform_step()`, but now with the wrong bullets (from the current frame instead of the previous one).

"Okay, but surely 1 frame difference can't be that bad, right?", I thought to myself.

Well, usually not. But when a single-frame difference means crucial information is lost, it can lead to disaster.

Bullets have a `hit_entity` property that tells you what entity they hit.
`calculate_reward()` uses this property to reward or punish the agent accordingly.

Makes sense, right? Well, the bullets get removed from the game after hitting an entity—**before** `calculate_reward()` is called.

So, if we don't keep a reference to the bullets from the previous frame, we can't see what entity they hit.
We only see current bullets, not the ones that just hit something.

This meant `calculate_reward()` never gave rewards for hitting the player or punished for firing at teammates.
Which is why the agent's performance collapsed.

When there was a -0.2 punishment for firing, the agent learned not to fire at all, because it would only get punished.
When I changed the firing reward to +0.05, the agent learned that firing was good, but it didn't have a reason to fire at the player anymore, because it never got rewarded for that!


---


**How I found this out by accident**:

I was disappointed with the agent's poor performance. After trying many different reward shaping methods, I decided to add more logging to the code, so I could better understand what was going on.

When I added the logging logic, I also moved the line updating `self.all_bullets_from_last_frame` from `calculate_reward()`, into `perform_step()`, right after calling `calculate_reward()`.
I moved it because I used `self.all_bullets_from_last_frame` for the logging logic too, and it didn't feel right to update it in `calculate_reward()` anymore, since it was no longer just for the reward calculation.

After adding logging, I ran a test train run and to my surprise the agent's performance didn't immediately collapse like it did in all previous attempts.
I expected the reward to drop from ~180 to under 100 in the first few iterations, but it didn't.

I was surprised. Had the RNG gods finally smiled upon me, or was this just a lucky run?
I knew what I changed, but I didn't think it should affect training at all.
But to see a difference in `ep_rew_mean` this huge? It didn't make sense. I stopped the run and started another one. Again, no collapse.

I was confused. I stared at the code, trying to figure out what could have made such a big difference.
I was almost certain I didn't make any major changes to the code that would affect the rewards this much.

So I went to investigate. I looked at the history, comparing all the changes I'd made since the last failed run.
I found a few small changes, but nothing that should affect the rewards this much.

I stared at the code for a while, trying to figure out what could be the issue. Nothing obvious. Zero. Nada.

I shared the code changes with ChatGPT and asked him if he spots any issues. He didn't (at least nothing useful—just some random bullshit).
After a while I told him I give up, even though I wanted to learn the reason why these simple changes completely altered training. But I couldn't lose any more time on this.
Solution has been found. I didn't understand why it made a difference, but I **had** to move on.

ChatGPT replied:
> Honestly, that’s probably the best move! The result speaks for itself — you’ve got a stable, much smarter agent that’s consistently performing better. Spending hours dissecting exactly which tiny detail caused the breakthrough is interesting but not critical for your main thesis or moving forward.

The only thing that stuck in my head was:
> "dissecting exactly which tiny detail caused the breakthrough is interesting"

I KNEW IT WAS INTERESTING BEFORE ASKING. I JUST WANTED YOU TO SAY TO MOVE ON—NOT THAT SOMETHING I WANT TO DO BUT DON'T HAVE TIME FOR IS "INTERESTING"!

So there was only one thing left to do... get back to the code and start debugging it closely.

I undid those changes, even though I was certain they shouldn't affect training. Boom—rewards collapsed again.
Interesting, so it is actually related to the recent changes.
"Hmm, the line with `self.all_bullets_from_last_frame` update logic is the only thing that could have any real effect on the game, the rest was literally just logging logic."

I re-did everything, except that line. Rewards still collapsed.
Re-did that line as well—rewards were back to good!

"Okay, so this is clearly the culprit." I said to myself in a confident tone, still having no clue why that was the case.

But why does this affect the rewards so much?
We're either updating it in `calculate_reward()` right before returning, or in `perform_step()`, right after calling `calculate_reward()`.
We don't do anything else in between, so why does simply moving this one line affect the training so much?

Welp, it was time for real debugging.
I started the debugger and analyzed frame by frame what was happening, paying close attention to the reward and `self.all_bullets_from_last_frame`.
Nothing obvious.

I moved the `self.all_bullets_from_last_frame` update logic back to `calculate_reward()`—nothing obvious here either.
But wait, why do I need to press "Resume program" twice for the frame on the screen to change?
I only have one breakpoint, where I update `self.all_bullets_from_last_frame` in `calculate_reward()`. It should require one press of "Resume program" to continue to the next frame.

"Ohhhh, I'm probably calling `calculate_reward()` **twice**!"

It took me a while to realize the second call was coming from `super().perform_step()`, but I still didn't understand why this was an issue.

Just a few moments later it clicked!

The first call to `calculate_reward()` updated `self.all_bullets_from_last_frame` with current bullets.
The second call, which was actually the one we used for training, used the already updated bullets!
**From the current frame, not the previous one!**.

Suddenly everything made sense!
I started tracing back all the thoughts, problems and decisions I made about step3 environment.
One after another, I found logical explanations for each of them. It all fit together like a puzzle.

~0 rewards with -0.2 punishment for firing? Agent too scared to fire the gun? 11 rewards with +0.05 reward for firing? Not aiming at the player?
Even though I barely changed any logic from step2, the policy is collapsing no matter what I do?

It wasn't reward shaping that was the problem, nor was it the environment!
It was calling `calculate_reward()` twice each step, so the agent never got rewarded for hitting the player, or punished for firing at teammates.


---


**OH, MAN.** IF I DIDN'T DECIDE TO ADD THAT LOGGING PART, IT COULD HAVE TAKEN ME AGES TO FIGURE THIS OUT!
I was training the agent for two days before realizing this wasn't a reward shaping or environment design problem, but a simple timing issue!

This wasn't an issue before, because in other environments, I never called `super().perform_step()`, not even in step2 env—I didn't even override `perform_step()` there.


---

**Lesson:**
Touch grass and don't call `super().perform_step()` in your environment code.
