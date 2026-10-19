# Elicitation — User Interview 01

**Project:** SwimMatch
**Method:** Semi-structured interview (verbal), ~15 minutes
**Participant:** Current college swimmer (NCAA Division I, GMU)
**Purpose:** Understand how swimmers currently find and evaluate college programs, and where the process breaks down — to validate and refine our feature backlog.

---

## Summary of findings

- **SwimCloud is the dominant existing tool.** The swimmer found realistic schools by looking up programs on SwimCloud and comparing their own times to each school's times. They described the data there as "very accurate."
- **The real gap is on the coach side.** SwimCloud shows *how fast a team is*, but not *what a coach is actively recruiting for* or *whether they have spots left*. When asked what one thing a tool could have told them, the answer was: "what the coaches are actually looking for and if they have spots left."
- **Coaches are hard to reach.** The most frustrating part of the process was that "coaches were not being very responsive and it was not very easy to communicate."
- **Fit is driven by top events plus trajectory.** Coaches care most about a swimmer's best events ("they want to see your ceiling"), but improvement over time matters too. A recruit cannot be far off a team's roster times, though progress is weighed alongside.
- **SCY vs. LCM depends on the coach.** Whether short-course yards or long-course meters matters "depends on what the coaches are looking for."
- **Diving is a separate process.** Swimming and diving recruiting are "very different." Scope confirmed as swimming-only for now.

---

## Interview notes (questions and responses)

### The recruiting process

- **How did you figure out which schools were realistic for you?**
  "I looked up on SwimCloud website and compared my times with the school times."

- **What made a school a "reach" vs. a "safe" fit?**
  "I was looking for mid-major schools because my times weren't good enough for Power 4 schools, and the best fit for me was GMU — but mostly I looked on SwimCloud."

- **Did coaches give you a time standard to hit, or did you infer it from the roster?**
  "You can find the times on SwimCloud, and it depends on what the coaches are looking for — so basically no."

### Times and fit

- **Which events count most in recruiting — your best, your top 2–3, or overall spread?**
  "Mostly your top ones, because coaches want to see your ceiling — but the improvement is important as well."

- **Do coaches care more about your current time or your improvement over time?**
  "They care about both."

- **Does short-course yards vs. long-course meters matter in how you talk about times?**
  "Depends on what the coaches are looking for."

- **How far off a team's roster times can you be and still get recruited?**
  "Not very far, but they care about your progress over time as well."

### Tools and pain points

- **What was the most frustrating part of finding programs?**
  "That the coaches were not being very responsive and it was not very easy to communicate."

- **Did you use any site or spreadsheet? What did it do well or badly?**
  "I used SwimCloud, where I could [see where I] could be a good fit."

- **If a tool could've told you one thing during recruiting, what would it have been?**
  "It could show what the coaches are actually looking for and if they have spots left."

### Data sources

- **Where did you find a team's recruiting times?**
  "SwimCloud."

- **How accurate and current was that info?**
  "Very accurate."

### Diving

- **Do swimmers and divers go through recruiting the same way, or is it separate with different standards?**
  "It's very different — but we are swimmers, so not much information about diving."

---

## Implications for requirements

| Finding | Impact on backlog |
| --- | --- |
| SwimCloud already solves times-vs-school comparison, accurately | We do not rebuild time comparison; we build what SwimCloud lacks |
| Swimmers can't tell what coaches want or if spots are open | Directly validates **Feature 1 — Coach program posts** (states events, target times, openings) |
| Coaches are unresponsive and hard to reach | Supports a coach-authored public post over cold outreach |
| Top events + improvement both matter | A coach post should let coaches state target events and times |
| SCY vs. LCM depends on the coach | Posts should let coaches specify course type |
| Diving is a separate process | Confirms swimming-only scope for this release |

---

*Note: This is one interview (n = 1). Additional interviews from team members should be appended as `elicitation_interview_02.md`, etc., to strengthen the elicitation record.*
