# Note: RunPod credit ran out (22 October, about 07:31 UTC), for story log 31

What this file is: what stopped the pay-per-second graphics cards during the garden job, and how it was found.

* Last job a card took: 07:31 UTC. After that, jobs waited in line (3 by 07:45) while the workers reported "idle" and never took them.
* Restarting the workers (setting the most workers to 0, then back to 3) made fresh workers, but they also took nothing.
* An ordinary machine on the same Romania store showed everything intact. The store held about 8.5 GB of 30 GB, the start script and
  libraries were in place, and the job taker answered a test job. So nothing on our side was broken.
* Cause: the account balance was US$0.13. RunPod does not hand jobs to pay-per-second workers with a balance that low.
* The test machine was shut down at 07:53 (it cost about US$0.03). After that, spend was US$0.006 an hour (the two 30 GB stores only)
  and the balance was US$0.10.
* Waiting for the person to add credit. The jobs already waiting in line start by themselves once credit is there.
* Lesson: check the balance (GraphQL myself.clientBalance) before a long render job, and when jobs wait while workers sit idle.
* About 08:30: the person added credit (balance US$20.10). The helper's test job, which had waited in line for 9.5 minutes, ran at
  08:30:41 on an RTX 4090. The cards work again. While they were stalled, the helper drew small previews on this computer's processor
  (about 30 s each for a close-up and 5-6 minutes each for the two main views).
