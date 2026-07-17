# PulseMetrics

**Live app:** https://traya1.streamlit.app/

A tool that looks at an A/B test and tells you, honestly, whether you should launch it.

---

# What problem does this solve?

Companies are always trying small changes to a website or app. Maybe a button gets new text. Maybe a section moves higher on the page. Maybe something new gets added entirely.

Every time a change like this is tested, half the visitors see the old version and half see the new version. Then someone has to answer one simple sounding question that is actually quite hard.

Did the new version actually work better, or did it just look better by chance?

That question is what PulseMetrics answers.

---

# What PulseMetrics actually is

Think of it like a judge, not a scientist and not a designer. Someone else runs the experiment. Real visitors see the old version or the new version. PulseMetrics does not decide who sees what. It only looks at the results afterward and gives an honest verdict.

The verdict is always one of four words.

- **Ship.** The new version is a real improvement. Roll it out to everyone.
- **Wait.** Not enough people have gone through the test yet to be sure.
- **Investigate.** Something looks off and a person should take a closer look before deciding.
- **Reject.** The new version is not actually better, or it is causing a hidden problem.

---

# Why not just look at the numbers directly?

Because raw numbers can trick you. Here are four ways that happens, and how PulseMetrics checks for each one before it trusts anything.

### 1. The split was uneven.

If the test was supposed to show the new version to half the visitors but it actually went to way more or way fewer people than planned, something is broken, maybe a bug, maybe a tracking error. PulseMetrics checks this first, before looking at anything else.

### 2. Not enough people were tested yet.

If only a handful of people have gone through the new version, one lucky day could make it look like a big win. PulseMetrics checks whether enough people have actually gone through the test to trust the result.

### 3. The win came with a hidden cost.

More purchases sounds great, until you notice refunds also went up. PulseMetrics checks a safety metric like refund rate alongside the main result, so a good looking win does not hide a real loss.

### 4. Different types of users disagreed.

Sometimes new visitors respond well to a change while returning users dislike it. Looking only at the overall average can hide that split opinion completely. PulseMetrics checks whether different user groups actually agree on the result.

Only after all four of these pass does PulseMetrics calculate the final numbers and give a verdict, along with a plain sentence explaining why.

---

# What it measures

- **Form Fill Rate.** How many visitors actually completed the intended first step of the journey.
- **Conversion Rate.** How many visitors actually purchased.
- **Lift.** How much better, or worse, the new version did compared to the old one.
- **Confidence.** How sure we can be that the result is real and not just luck.

---

# Handling many tests at once

It is rare for only one experiment to run at a time. PulseMetrics keeps a simple list of every experiment currently running, what part of the page it touches, and its current status.

If two experiments are running at the same time and both touch the same part of the page, PulseMetrics flags it as a possible conflict, instead of silently giving a result that might be confused by the overlap.

---

# What this tool is not

It does not decide who sees the old version and who sees the new one. That job belongs to a different kind of system entirely. PulseMetrics comes in after that part is already done. It only reads the results and judges them.

It also does not use machine learning. That was a deliberate choice. The question here is not "who is likely to buy something." It is "did this specific change actually help." That is a question about evidence, not prediction, and a simple honest statistical test answers it better than a black box model ever could.

---

# How it is built

- Python does all the calculations and decision logic.
- Streamlit turns that logic into the web page you can click through.
- Everything is rule based and explainable. Every verdict can be traced back to a specific number and a specific reason. Nothing is a guess.

---

# Try it yourself

Visit the live app here:

**https://traya1.streamlit.app/**

You will see a list of experiments, their current status, and a decision for each one. Click into any experiment to see the full breakdown, the reasoning behind the decision, and the charts comparing the old and new versions.

---

# Running it locally

```bash
git clone <this-repo-url>
cd pulsemetrics

python -m venv venv

# Windows
venv\Scripts\activate

# Mac or Linux
source venv/bin/activate

pip install -r requirements.txt

streamlit run dashboard.py
```

---

