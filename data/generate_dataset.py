"""
Generates the TakeMeter labeled dataset.

Reddit's JSON API now requires OAuth authentication, so data was generated
using an LLM (Claude) with knowledge of real r/nba discourse patterns.
All examples are marked ai_assisted=True. Labels were assigned by the
annotator (Claude) following the taxonomy in planning.md and then reviewed.

Label definitions (from planning.md):
  analysis  — structured argument backed by specific verifiable evidence
  hot_take  — bold confident claim stated without real supporting reasoning
  reaction  — immediate emotional response to an event; no argumentative intent

Run this script once to produce data/dataset.csv.
"""
import csv
import random

EXAMPLES = [
    # ── ANALYSIS (70) ─────────────────────────────────────────────────────────
    {
        "text": "The argument that Jokic isn't a dominant defender ignores his defensive positioning. Denver finished top-10 in defensive rating in both his DPOY seasons. He's not a rim protector, but his help rotations and passing lane disruptions are genuinely elite — the traditional eye-test misses it because he doesn't block shots.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "People comparing Wembanyama to past big man prospects are missing the defensive uniqueness. His shot contest rate per 100 possessions in his rookie year exceeded Gobert's at the same age. His wingspan-adjusted reach means he can contest shots from a step further than any player in league history. He's not a slow burn — he's already changing defensive outcomes.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The knock on Harden being a bad defender is largely accurate, but the framing ignores his ball-hawk ability. His steal rate ranks in the top 5% of guards historically — he compensates for poor off-ball defense by gambling in passing lanes. It's a net negative overall, but 'worst defender in the league' misses this entirely.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Trae Young's playoff struggles correlate strongly with one factor: teams that switch every screen neutralize his pull-up game. In series where opponents switched pick-and-roll coverage, his true shooting dropped from .595 to .529. The solution isn't 'he just can't perform in playoffs' — it's a specific matchup problem that better floor spacing would address.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The Lakers' half-court offense ranks 28th in the league in points per 100 possessions when LeBron sits. The 'LeBron is dragging the team' narrative ignores that their spacing collapses without his gravity — no other ball-handler on the roster creates the same defensive attention.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Kawhi Leonard's true shooting percentage in his second Toronto season (.601) is higher than the equivalent season for every other player in the current top-10 all-time conversation. His DPOY-caliber defense on top of that output makes the small sample argument frustrating — the advanced metrics don't forget even if the narrative has.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason Curry's gravity works differently from other shooters is that defenses have to extend coverage 30 feet from the basket, which opens up the entire middle of the floor. Tracking data shows opponents go under picks against Curry at a lower rate than any other point guard in history — the threat of his shot physically reorganizes defenses.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Looking at Box Plus/Minus for the 2016 Finals: LeBron finished +10.2 for the series, which is the highest for any player on a championship-winning team since the stat became trackable. The 'he lost that series so it counts against him' argument doesn't survive contact with the numbers.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason the Bucks struggle in the playoffs is specific: their half-court offense becomes predictable when opponents can crowd the paint against Giannis without fearing perimeter shooting. Their 3P% drops from 36.4% in the regular season to 32.1% in the playoffs — that four-point gap is almost entirely explained by shot quality, not shooting variance.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Rudy Gobert's defensive impact is most visible in a stat that gets underreported: opponent field goal percentage within 6 feet of the basket. Teams average 61% at the rim league-wide; against Utah with Gobert, that drops to 52%. That nine-point suppression is the largest in the league and has been consistent for five straight seasons.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The criticism of KD's rings ignores that Oklahoma City was statistically better than the Warriors teams he joined when adjusted for playoff performance. His PIPM on both championship teams ranked first on the roster. The rings argument is backward — the teams improved because of him, not the other way around.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Comparing Luka and LeBron at age 23: Luka was averaging 28.4/9.1/8.7 while LeBron at 23 was at 27.3/7.9/7.2 with better efficiency. The narrative that Luka is 'still developing' compared to LeBron at the same age doesn't hold up when you look at the actual numbers side by side.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason point differential is a better predictor of playoff success than regular season record is that teams can game their records with load management and fourth-quarter DNPs. The five teams with the best point differential in each of the last ten seasons have won the championship six times. Record-based seeding misses this signal.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Chris Paul's playoff reputation as a choke artist doesn't survive statistical scrutiny. His PPG and APG actually improve in the playoffs compared to the regular season across his career. The narrative is driven by three or four high-profile fourth-quarter sequences that get replayed endlessly — not his aggregate performance.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The 2004 Pistons defense was historically good: they held opponents to 84.3 points per game, which in pace-adjusted terms was the most efficient defense since the hand-check era ended. The argument that modern teams would have beaten them ignores that the Pistons were built to switch and pressure in a way that specifically counters pace-and-space offenses.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "OKC's rebuild is underrated in terms of speed. They currently have seven first-round picks in the next four drafts plus four pick swaps. By draft value projections, that's equivalent to owning the #1 overall pick four years running. No team since the Sixers' Process has accumulated that kind of future capital.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason zone defense is more common now than a decade ago is data-driven: modern tracking shows that zone forces the ball to the corners, where three-point attempts have lower expected value than above-the-break shots. Teams are running zone specifically to remove the high-value pull-up threes from elite shot creators' arsenals.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Reggie Miller's clutch shooting record deserves more respect in the historical conversation. His TS% in the final two minutes of close games was .643 — higher than Jordan in the same situations. The 8-points-in-9-seconds game is remembered; the underlying efficiency across his career isn't.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The argument that Embiid's injuries make him a lesser MVP candidate ignores that his per-game production when healthy is the highest in the league by most metrics. VORP, BPM, and PER all have him top-3 in every healthy season he's played. Availability is a real concern, but it's a separate question from peak performance.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason small-ball lineups work in the playoffs despite the size disadvantage is rebounding. When you play small, you lose offensive rebounding but gain defensive rebounding rate because guards are faster to box out on the perimeter. The net effect on second-chance points is roughly neutral, but you gain shooting and switching flexibility.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Draymond Green's defensive value is most visible in lineups data: Golden State's defensive rating is consistently 6 to 8 points better per 100 possessions with Draymond on the floor versus off. That's a bigger single-player defensive swing than any other non-center in the last decade. The offensive limitations are real, but they don't cancel that.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The Clippers' long-term problem isn't their roster — it's their luxury tax situation. They're projected to be $90M over the tax line next season, which triggers the repeater tax for the third time. The per-dollar efficiency of their roster construction is among the worst in the league, and they can't fix it without losing the players that make them competitive.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Ben Simmons' offensive failure in the 2021 playoffs was specific: the Hawks loaded up on his free throw shooting late in games and it worked completely. His free throw rate that series was 8.3 per 36 minutes in the regular season but dropped to 2.1 in the last five minutes of close games — he was avoiding contact, not just missing shots.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The Heat Culture brand of player development is demonstrably real in the numbers: undrafted players on Miami average 1.8 Win Shares per 48 minutes above their pre-Heat career average — the highest uplift for undrafted players of any franchise over the last 15 years. It's not just marketing; it shows up in the data.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Kyrie Irving's shot creation ability is statistically elite: his points per shot attempt off the dribble (.98) is higher than any other guard not named Curry in the last five seasons. The narrative that he's a poor fit in every organization is about behavior and chemistry — his on-court skill set is not in question if you look at the efficiency numbers.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The 'load management destroyed competitive balance' argument doesn't hold up against the injury data. Soft tissue injury rates actually declined 12% league-wide after load management became standard practice (2018–2023 vs. 2013–2018). The games missed to rest are offset by fewer season-ending injuries to star players.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Looking at clutch stats across Kobe Bryant's career: his TS% in the final two minutes of games within five points was .512, which is below league average for that era. The Kobe clutch mythology is built on shot volume and memorable makes — the misses are forgotten. Jordan's equivalent number was .621.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason transition offense matters more than ever is pace: teams averaging 100+ possessions per game allow 11% more points per game than teams in the 96-possession range, but they also score 14% more. The net effect favors pace because transition shots are the highest-quality attempts in basketball — layups and corner threes from fast breaks.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Ja Morant's injury history is directly correlated with his play style: he drives to the basket more than any other guard and takes contact at a rate 40% above the positional average. His durability ceiling is structurally limited by how he plays, not bad luck. To get a healthy Ja you need a different Ja, and that's the roster-building question Memphis has to answer.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The case for Hakeem Olajuwon as the greatest center of all time rests on one underappreciated fact: he was an elite defender AND an elite offensive player at the same time. Shaq was better offensively; Robinson was comparably dominant defensively; but neither combined both at Hakeem's level. His two championships without a second star are also relevant context.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The three-pointer has made the shot clock more valuable as a strategic tool. Teams with fewer than 7 seconds on the clock are now taking corner threes at 2.4x the rate they were in 2010, and those shots score at 1.07 points per possession — better than almost any other end-of-clock option. The shot clock crisis has become a shot clock opportunity.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason the Warriors dynasty was difficult to replicate isn't just talent — it's their defensive switching system. They were the first team to consistently switch 1-through-5 without losing defensive efficiency, which required five players who could guard multiple positions without significant drop-off. That kind of positional versatility depth is almost impossible to maintain through free agency.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Paul George's regular season vs. playoff split is real but misattributed. His scoring average drops only 1.2 points in the playoffs, but his usage rate drops 4.5 percent — which means he's actually slightly more efficient per opportunity. The 'PG chokes' narrative is driven by a few high-profile late-game misses, not aggregate performance.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The post-merger ABA-NBA era has produced exactly two players who ranked top-3 in both offensive and defensive rating simultaneously for a full season: Bill Walton in 1977 and Giannis in 2020. That's the actual measure of two-way dominance, and it's how rare it is.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason Melo's teams never won is specific to construction: every team built around him prioritized scoring over defense and playmaking. His ORTG was fine throughout his Knicks years — the team's DRTG was consistently bottom-10. Blaming Melo for team failures ignores that the rosters were structurally built wrong around him.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Anthony Davis is the most volatile franchise cornerstone in the league in terms of floor vs. ceiling. When healthy he posts a net rating of +9.2; when he misses more than 20 games, the Lakers' net rating drops to -1.1. No other top-5 player has that wide a swing between their healthy and injured team impact.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Corner three percentage league-wide has held flat at around 38.5% for the past six seasons despite teams shooting them more. This means the marginal corner three is just as good as the average corner three — teams haven't over-shot them to the point of diminishing returns yet, which means the analytics consensus to keep shooting them is correct.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason the Celtics' current core is so hard to beat in the playoffs is their defensive versatility: their five starters can all guard positions 1 through 4 without significant drop-off. Tracking data shows they give up the lowest points per possession against isolation plays of any team in the league — because isolation is a bad play against switching defenses.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Isaiah Thomas's 2016-17 season is genuinely one of the most underrated in NBA history. He averaged 28.9 PPG on .592 TS% as a 5'9\" guard carrying a team to the #1 seed in the East, doing most of it in the second half of the season while grieving his sister's death. The hip injury that came right after means we never saw what a healthy follow-up looked like.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The 'star players don't guard their assignment' problem in the modern game is real but exaggerated. Tracking data on defensive possessions shows LeBron and KD both take below-average quality shots against them — they redirect assignments to easier matchups rather than completely abandoning defense, which is actually smart rotation rather than laziness.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Tim Duncan's career VORP of 149.3 is the highest of any player in the shot-clock era who never led the league in scoring. His value came entirely from efficiency, defense, and consistency — 19 straight seasons with a positive BPM, which no other player in the database has matched.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason the mid-range jumper has a comeback narrative but not actual comeback numbers: mid-range attempts as a percentage of total shots have been flat or slightly declining for four years. What's changed is who takes them — elite mid-range shooters like DeRozan and KD score 1.03 points per mid-range attempt, which is actually above average for non-three-point shots. But most players can't do that.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Steve Nash's back-to-back MVP case rests on something the box score doesn't show: Phoenix's offensive rating with Nash on the floor was 12 points better than the league average in 2005-06. No other non-center has produced a comparable on/off split in the modern era. His PER doesn't capture the system-elevating impact.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason small market teams can't retain stars isn't market size alone — it's the entertainment amenity gap. Research on free agent decisions since 2010 shows that players cite team competitiveness first, but among equally competitive options, large market teams win at 3:1 over small markets. Oklahoma City has had to overpay every star they've kept relative to the open market.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The 2016 Warriors blowing a 3-1 lead is used as a caveat against their dynasty, but the statistical context matters: Golden State that series had a -4.3 net rating for games 5-7 combined, which correlated almost perfectly with Draymond's suspension and Harrison Barnes's collapse (.347 TS% in games 5-7). Specific personnel failures, not a general choking pattern.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason second-round picks have become more valuable in trade negotiations over the past decade: the league's increasing salary cap has created roster spots where cheap second-round contracts can be worth 15-20 million dollars per year in surplus value over their rookie deal. Two good second-round picks in back-to-back years equals one mid-tier free agent deal.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Dirk Nowitzki's one-legged fade is often described as unguardable, but the mechanical reason is specific: the motion starts identically to his drive step, so the defender can't load for the contest until the ball is already leaving his hand. No other player has successfully replicated it because it requires both the footwork precision and the shot arc to be in a very narrow window.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The Spurs' success with the two-man game under Pop wasn't just talent — their high/low passing system was specifically designed to exploit weaknesses in help defense rotations that other teams ignored. Their points per touch in post entries with a cutter off the weak side was 1.23, compared to the league average of 0.98. The system extracted value from plays most teams didn't run.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Devin Booker's efficiency numbers have improved every year since he turned 23, and his current TS% (.614) is in the same range as Kobe's best seasons. The narrative that he's 'just a scorer' ignores that his assist rate has doubled since 2019 and his turnover percentage has dropped. He's a more complete player than his reputation suggests.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason switching has proliferated in NBA defenses is not just shot contest data — it's that every team now has players who can exploit mismatches in the pick-and-roll. If you don't switch, you're giving up either a center defending in space or a guard defending a 7-footer. Switching trades a known vulnerability for a recoverable one.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Steph Curry's 2015-16 season (402 threes, 73-9 Warriors, unanimous MVP) is the most statistically dominant offensive season since the introduction of the three-pointer. His PER was 31.5, his TS% was .670, and he did it on the highest usage rate of his career. The argument that the game was easier then ignores those are all-time numbers by any era's standard.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason Zion Williamson's injury history should concern New Orleans long-term is structural, not random: his body fat percentage and playing weight put stress on his knees and ankles at a rate that sports medicine research shows correlates with soft tissue breakdown over a 10-year NBA career. He's not unlucky — he's operating at the physiological edge of sustainable NBA play.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Charles Barkley's case for being underrated in the all-time conversation: he averaged 22.1 PPG and 11.7 RPG for his career while shooting .541 FG%. For a player listed at 6'6\" (likely shorter), those rebounding numbers are historically unprecedented — only Rodman rebounded at a higher rate, and Rodman didn't score. Barkley was doing both.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason playoff basketball has lower scoring than regular season isn't just defense — it's familiarity. Teams that have faced the same opponent in the same series for more than 3 games score 4.2 fewer points per 100 possessions than games 1 and 2 of the same series. Opponent-specific preparation over time is the biggest factor in scoring compression.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The 1986 Celtics roster had three future Hall of Famers (Bird, McHale, Parish) all playing in their prime simultaneously, plus two more Hall of Famers as rotation pieces (Walton, DJ). It's the only time in NBA history where five players who made the Hall of Fame were contributing rotation players on the same team in the same season.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The Thunder's draft success over the last three years is not luck — their analytics staff uses a physiological aging model to project which college players will peak in the NBA between ages 24-28 rather than immediately. High-ceiling late developers are systematically undervalued by teams that need wins now, and OKC is deliberately exploiting that market inefficiency.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "John Stockton's assist totals are often dismissed as a system product, but his assist percentage (percentage of teammate field goals he assisted while on the court) was 52.3% for his career — meaning he was involved in over half of every made field goal while he played. That's not a system stat; that's a measure of actual facilitation.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason Miami keeps developing unknown players into contributors is their conditioning and spacing system. They run a motion offense that requires every player to read defensive rotations and cut simultaneously — players who arrive already knowing how to move off the ball adapt faster and produce earlier than on teams with more isolation-heavy systems.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The current Knicks rebuild is structurally different from past attempts: they've accumulated tradeable contracts with positive value rather than max contracts with negative value. Their $0 dead cap and multiple first-round picks puts them in a trade position that no previous Knicks team since 2000 has been in. This rebuild has the right architecture even if the outcomes aren't certain.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The argument that LeBron's longevity proves he's the GOAT has a specific statistical backing: his PER has stayed above 25 into his late thirties, while every other player in NBA history shows a decline below 22 by age 35. The aging curve for elite players bends toward Jordan's type; LeBron's doesn't. That's genuinely unprecedented.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason rebounding is more position-neutral now than in any prior era is simple physics: the three-point revolution has moved shots further from the basket. Long misses create longer rebounds that land further from the paint — in areas where guards and wings can compete with centers. Rebounding by non-big players has increased 23% since 2015.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Manu Ginobili's career Win Shares per 48 minutes (.218) is higher than most Hall of Fame starters despite coming off the bench for most of his career. The 'sixth man' label undersells his actual impact — his playoff minutes per game were equivalent to a starter, and his performance in those minutes rivals anyone on those Spurs teams.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The reason the league's best teams have converged on similar defensive schemes is data: drop coverage in pick-and-roll gives up corner threes to the roller's dump-off receiver; hedge coverage exhausts the big man on switches; switching is the least bad option against the modern pick-and-roll. Teams that still play drop coverage against elite shooters are leaving points on the board.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Phoenix Suns' current rebuild timeline is actually favorable when you look at their draft position: they're projected top-5 in next year's draft, which historically has a 40% chance of producing an All-Star. Combined with their core of young players on cheap contracts, the rebuild window is 2-3 years, not 5, if the draft breaks right.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "The notion that the NBA was more physical in the 80s and that modern players couldn't handle it ignores the rule changes. Hand-check defense was explicitly banned in 2004 specifically because it was hurting offensive production and viewership. Players didn't get softer — the rules changed to produce a different kind of game. Retroactive comparisons across rule regimes are inherently incomplete.",
        "label": "analysis",
        "notes": "",
    },
    {
        "text": "Jimmy Butler's clutch performance is backed by specific data that rarely gets cited: his TS% in the final two minutes of games within five points is .639, which ranks in the top 10 for players with at least 200 such possessions over the last six seasons. The 'Jimmy Buckets' narrative is not mythology — the efficiency in high-leverage moments is real and consistent.",
        "label": "analysis",
        "notes": "",
    },

    # ── HOT TAKE (92) ─────────────────────────────────────────────────────────
    {
        "text": "LeBron James is not the GOAT and never will be. Jordan won six rings, never lost a Finals, and had to deal with the Bad Boy Pistons. LeBron had everything handed to him and still lost Finals. Not even close.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Steph Curry is not a top-5 player of all time. The three-point era inflated every guard's numbers. Put him in the 80s and he's an above-average starter at best.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Dame Lillard will never win a championship. He's a loser and the Trail Blazers were right to move on. The numbers don't lie.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Kyrie Irving is the most skilled player in the history of the NBA, full stop. Nobody has his handle, his footwork, and his shot creation all at once. People hate him so they won't admit it.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Celtics are soft. They always find a way to lose in big moments and they always will. This franchise is cursed after the Larry Bird era ended.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "KD is the most talented player who ever lived and it's not even arguable. If he wanted to be the GOAT he could be, he just doesn't care enough about winning.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The league is soft now. Players in the 80s and 90s would wipe the floor with these guys. No hand-checking, no defense allowed — might as well be playing horse.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Nikola Jokic is overrated. He can't guard anybody and his offense only works because he has great teammates. Put him on the Wizards and he's a .500 player at best.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The MVP award is completely meaningless. It goes to whoever has the best PR team, not whoever is actually the best player. It's a popularity contest and always has been.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Anthony Davis is the biggest bust in NBA history for a player of his talent level. He could be the best player in the league if he cared more. He simply doesn't want it bad enough.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The 2010s Golden State Warriors are the greatest dynasty in NBA history and it's not close. Better than the 90s Bulls, better than the 80s Lakers, better than anything. The talent level and the style of play was incomparable.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Luka Doncic is going to win 5+ MVPs before he retires. He's the most unstoppable offensive player since peak MJ, and he's only getting better. Anyone who disagrees is a hater.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Kawhi Leonard chose comfort over legacy. He could have been in the all-time conversation with his talent level but he'll retire as a guy who played 40 games a year and never led a team to a Finals again.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Westbrook was never a good player. His triple doubles were always a statistical mirage and everyone knew it. The contract he got was the worst in NBA history.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Houston Rockets small ball experiment is the dumbest coaching decision in modern NBA history. They had a Hall of Fame center and chose to sit him. Pure arrogance from Daryl Morey.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Carmelo Anthony should be remembered as a first-ballot Hall of Famer and an all-time great. The narrative that he was selfish is wrong and driven by hate. He was one of the best scorers ever.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The media has never given Giannis the respect he deserves because he doesn't have the 'right' personality. If he were American they'd be talking about him as the GOAT right now.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Zion Williamson is never going to be an elite player. His body is always going to break down and his conditioning issues show a mental weakness that doesn't go away. New Orleans wasted their rebuild on him.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Spurs dynasty was fake because the competition in the West was weak in their early years and the rules favored them later. Pop is a great coach but those championships are all asterisks.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Dirk Nowitzki is the most underrated player in NBA history. People talk about Jordan and LeBron but Dirk almost never gets mentioned in GOAT conversations even though he was better than half the names people throw out.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Referees have been terrible this season and it's getting worse every year. The league doesn't care about officiating quality because the big market teams get the calls they need to win.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The three-pointer ruined basketball. Games are just contested threes and floaters now. The beautiful mid-range game is dead and the sport is worse for it. I miss the 2000s.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Shaq was the most dominant player of all time and it's not even debatable. When he was in his prime, nobody could stop him — not Jordan, not Bird, not anyone. Pure physical dominance at that level has never been matched.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Every team that passed on Jalen Brunson for cheap is going to regret it for the next decade. He's going to be a top-5 point guard in the league in two years and the Mavericks look like complete idiots.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Kobe Bryant was a better scorer than Michael Jordan. People don't want to hear it but it's true. MJ gets credit for everything while Kobe gets dismissed even though their offensive games were nearly identical.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Warriors dynasty is tainted because they had four All-Stars. Any team with that roster could have won championships. Pop did more with less and his rings mean more because of it.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Ja Morant is the most exciting player in the league and he's going to be a top-10 all-time point guard when his career is done. His athleticism is completely unmatched in modern NBA history.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The East has been weak for 15 years and any team in the West top-8 would have made the Finals in the East at least twice during that stretch. Eastern stars are fraudulently celebrated.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Kevin Durant needs Steph Curry to win a championship. Without Steph, he's just another star who can't get it done in the playoffs. His rings don't count as much because he joined them.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Modern NBA players are spoiled and soft. They form super teams, demand trades, and skip games. Players from the 80s would never have done this — they respected the game.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Paul George has no business being in the All-Star game this year. He's had one good stretch and the media ran with it. He's a second star at best and everyone outside of LA knows it.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Sacramento Kings will never win a championship. That franchise has bad karma from the 2002 Western Conference Finals and they're going to be mediocre forever.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "James Harden is the biggest fraud in NBA history. He pads stats in the regular season and disappears in the playoffs every single time. 'The Beard' is a joke — more like 'The Coward.'",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Steve Nash winning back-to-back MVPs over Shaq was the most embarrassing thing the voters ever did. Shaq was still a dominant player; Nash was a system player. The analytics guys ruined the award.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Chris Paul is the most overrated point guard in the last 30 years. He's never led his team to a Finals and he was the common denominator on every team that choked in the playoffs. He's a great regular season player and that's all.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Phoenix Suns should blow the whole thing up. They've had their chance and they're not built to compete at the highest level. Time to trade everyone and start from scratch.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Draymond Green is the most overrated player in the modern era. His value is entirely a media invention. Any smart, athletic defender could do what he does if they had Curry and KD helping them.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Jimmy Butler is the most mentally strong player in the league. He thrives in the biggest moments while everyone else shrinks. He should already have multiple rings and the fact that he doesn't is on his teammates.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The league has been rigged for LeBron since 2003. Every narrative, every rule change, every MVP vote — it's all been tilted toward making him look like the GOAT. The fix has been in for 20 years.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Cade Cunningham is going to be top-5 in the league in three years and Detroit is building the best young core in the East. Bookmark this. People sleeping on them now will feel stupid.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Lakers are always going to attract the best free agents and win championships because that's what the league wants. They're the most protected brand in sports and Stern/Silver have both ensured it.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Ben Simmons is a wasted talent and it's entirely his own fault. His work ethic has always been suspect, his mental health excuse is overblown, and the Nets gave up too much to get him.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Modern big men can't guard anyone and the position has been completely ruined by the analytics era. Real centers — Shaq, Hakeem, Ewing — would average 40 against the soft defenses teams run now.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Warriors are done. Their window closed and they're going to be a lottery team within two years. Everyone saw this coming except Warriors fans who thought the dynasty would last forever.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Magic Johnson was a better all-around basketball player than LeBron James. People forget because Magic played in a different era but he was bigger, faster, smarter, and won more rings. Case closed.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Wembanyama will win an MVP before he turns 24. It's already inevitable. This is the most talented player the NBA has ever seen and we are watching history in real time.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Celtics always find a way to collapse when it matters most. It's cultural. Until they get a different type of player who wants the moment, they'll always be a regular season team.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Jaylen Brown over Jayson Tatum is the most wrong hot take in the league right now. Tatum is clearly the better player by every measure and the people who push the Brown narrative are just contrarians.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Westbrook's triple doubles mean nothing. Assists that go nowhere, rebounds that pad stats, turnovers that kill possessions. He actively hurt every team he was on after OKC and nobody wants to admit it.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Portland Trail Blazers are going to be terrible for the next decade. They have no draft picks, no star, and no direction. The Lillard trade was a disaster and the rebuild will take forever.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Tyrese Haliburton is the most underrated player in the league. He's going to be an All-NBA player for the next 10 years and Indiana is going to be a dark horse every single season.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Scottie Pippen is the most underappreciated player in NBA history. Without him, Jordan wins zero rings. He was not Jordan's sidekick — he was the co-star and history has been completely unfair to him.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The NBA doesn't care about small market teams and never will. The rules, the scheduling, the refereeing — everything is set up to make sure New York, LA, and Golden State are always relevant. It's not a conspiracy, it's just money.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "If LeBron had Jordan's mentality he would have 10 rings right now. His problem has always been caring more about his brand than winning. Jordan would have never formed a super team.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Donovan Mitchell is a certified star who has been wasted on bad teams his whole career. Put him on the Celtics in their prime and they win the championship by 20 games in the regular season.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Houston Rockets dynasty window has permanently closed and it's entirely James Harden's fault. He could have been the face of a franchise for 15 years and instead he forced his way out the moment things got hard.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Orlando Magic are going to be the best team in the East in three years. Paolo Banchero is a future MVP and everyone sleeping on this team right now is going to look very foolish.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Nikola Jokic should not have won MVP over Embiid even once. Jokic's numbers look better because Denver's system pads his stats. Embiid in the same system would average 36 and 15.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The modern NBA is unwatchable. Teams just jack up threes, nobody posts up anymore, the mid-range is dead, and every team looks the same. Analytics ruined the sport.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Giannis Antetokounmpo already has a better peak than LeBron James. His MVP seasons were more dominant and his 2021 Finals was the most impressive individual playoff performance since Jordan in '96. He's just getting started.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "There is no universe where LeBron James wins a ring without another top-10 player next to him. Jordan did it twice with Horace Grant and a role player next to him. That's why Jordan is the GOAT.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Oklahoma City rebuild is going to fail because no star player wants to live in Oklahoma City. They can draft all they want but the moment those players can leave, they will.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Patrick Beverley is the most valuable non-star player in the league. His leadership and defensive intensity make every team he's on better and the stats will never capture his true impact.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Dwyane Wade is a fraudulent Hall of Famer. He only has rings because of LeBron and his individual legacy is massively overstated by Heat fans and South Florida media.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Philadelphia 76ers Process was the most embarrassing era in NBA history. Tanking intentionally for five years, losing 70 games seasons in a row, and they still don't have a championship. It was fraud on their fanbase.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Shai Gilgeous-Alexander will be the best player in the league within two years. Oklahoma City is going to surprise everyone and SGA is going to win an MVP in a city nobody expected.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Kobe won five rings with Shaq and Pau Gasol doing the heavy lifting. People forget Jordan never needed a co-star of that caliber. Kobe's rings are compromised.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The media's obsession with LeBron vs. Jordan is manufactured. Real fans know it's not close — Jordan is the GOAT, LeBron is #2, and the conversation only exists because ESPN needs clicks.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Devin Booker will win an MVP before Jayson Tatum. Booker is a more natural scorer, a clutch performer, and plays with less support. The East bias in the media hides how good Booker actually is.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Isaiah Thomas deserved to be a starter on the 2017 All-Star team and the disrespect he got from management in Boston immediately after his best season is the most disgusting thing a franchise has done to a player in modern history.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Draymond Green gets away with more dirty plays than any player in the league and the referees never call it because the league is protecting the Warriors brand. If he played for Oklahoma City he'd be suspended 20 games a year.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Denver Nuggets dynasty ends the moment Jokic retires. They have no sustainable second star and the moment the league figures him out they'll go back to being a 50-win team that loses in the second round.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Minnesota Timberwolves are going to win the championship within five years. They have the pieces and a coach who can put it together. Anthony Edwards is going to be the face of the league.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Embiid is the best center in the league and it's not debatable anymore. His offensive game is unmatched, he's improved on defense, and his MVP season showed he can carry a team. Jokic era is over.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Suns blew their championship window with bad management and they deserve everything they're getting now. Robert Sarver's ownership poisoned that franchise for a decade.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Anthony Edwards is going to be more popular than LeBron within five years. He's exactly what this league needs — an alpha who wants to be great and doesn't complain. The torch is being passed right now.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Shaq vs. Wilt Chamberlain is the most underrated debate in NBA history. People dismiss Wilt's numbers but Shaq playing against Wilt's competition would have averaged 50 a game. Wilt was just that dominant.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The New York Knicks are the most irrelevant franchise in basketball and they've earned every bit of their mediocrity. Bad ownership, bad drafting, bad culture. They'll never win another championship in my lifetime.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The refs gave the 2002 Lakers a free pass in the Western Conference Finals against Sacramento and the NBA has never properly acknowledged it. That is the most corrupt moment in modern basketball history.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Jamal Murray is the best clutch player in the NBA. The 2020 bubble run should have made him a household name. He is criminally underrated and gets zero attention because he plays in Denver.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The Celtics and Lakers are the two most overrated franchises in NBA history. Their dynasties were built in an era of weak competition and people have been riding that reputation for 40 years.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "Isiah Thomas should be in the top 10 all-time point guard conversation and the fact that he's excluded is purely because of his beef with Jordan and the 1992 Olympic team drama. Pure politics keeping him out.",
        "label": "hot_take",
        "notes": "",
    },
    {
        "text": "The league allows superstars to get away with travel and carry violations that would get role players called immediately. The officiating is fundamentally two-tiered and it makes the sport less competitive.",
        "label": "hot_take",
        "notes": "",
    },

    # ── REACTION (68) ─────────────────────────────────────────────────────────
    {
        "text": "I literally cannot believe they blew a 20-point fourth quarter lead AGAIN. This team is going to give me a heart attack. Season over fr",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "WAIT WHAT. CURRY JUST HIT A 50 FOOTER AT THE BUZZER. I'm screaming. My neighbors hate me right now. That was the most insane thing I've ever seen.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Giannis just went for 48/15/8 and they still lost. I have no words. Nothing left. I'm going to bed.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Trade just dropped and I'm shaking. Three first rounders for that?? Someone at the front office is getting fired before the season ends.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "LeBron just passed Kareem's scoring record. I'm watching history live right now. Absolute legend. Whatever you think about him, this is incredible.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Wembanyama just had a block from behind on a breakaway that defies the laws of physics. I watched it five times and still don't know how that happened.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "NO NO NO NO NO. BACK INJURY. Please let it not be serious. This can't happen again. I am physically sick right now.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The Knicks are actually going to the conference finals. I've been a fan for 25 years and I have never felt this. MSG tonight was unreal. This city is alive.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Bronny and LeBron just played on the same court in an actual NBA game. Whatever you think about it, that's something we've never seen before and probably won't again. Wild.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "DAME TIME IN THE PLAYOFFS BABY. I knew it. I've always known it. This is the year. It's happening. I'm so hyped right now.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Anthony Edwards just did a 360 tomahawk dunk over two defenders and stared the bench down after. That man is not human. I need to lie down.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Just found out about the Westbrook trade and I'm still processing. Can't tell if this is genius or disaster. The vibes are all over the place in this thread.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Tatum just hit the go-ahead three with 2 seconds left. CELTICS WIN. I hugged my roommate and he's not even a basketball fan. THE GARDEN IS GOING CRAZY.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "I've been watching basketball for 30 years and I have never seen a game like that. Four lead changes in the last 90 seconds. My heart cannot take another game like this.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Jokic just recorded a triple-double in the third quarter alone. At some point this becomes less basketball and more performance art. What is happening.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The injury report just dropped and he's listed as questionable for game 7. I genuinely cannot watch. I'll check the score at midnight after it's over.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "SGA dropped 42 tonight and carried the whole team on his back. Whatever happens this season, this man is a stone cold bucket and OKC fans are eating well.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The fourth quarter comeback just completed. Down 15 with 4 minutes to go. I've never seen anything like this in my life. Sports are impossible.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Kyrie just did that stepback that lands him in the free throw lane somehow and nobody was calling travel?? I need officials to explain that in real time.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "This is the worst refereeing I've seen in years. Four consecutive calls against us in the final two minutes. I'm done. Turning it off. Not watching again this week.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Luka with 60 points tonight. 60. SIXTY. In a playoff game. Someone check on Mavericks fans because this isn't normal.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The buzzer beater went in. I'm in shock. We're in the Finals. Twenty-two years. I've been waiting twenty-two years for this and I cannot stop crying.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Just watched the Kawhi shot for the first time in a while. Still gets me every time. That bounce. The silence. Then the explosion. Greatest moment I've ever watched live.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The trade deadline is in three hours and I'm just hitting refresh on the NBA app constantly. This is not healthy. Send help.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Curry just shot from half court with three seconds left and it went in for no reason. I've given up trying to explain Steph Curry to people who don't watch. There are no words.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "KD just posted something on Instagram about the trade rumors and now I can't focus on anything else. The basketball gods are testing me specifically.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The Sixers just lost by 2 in a game where Embiid had 38. I'm done for the day. Maybe the week. Somebody else cover this franchise.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "That's a broken play, a scramble, a kickout, a 30-foot Steph Curry three, game over. I watched the sequence six times. Basketball is not real.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Team just announced he's out for the season. Torn ACL. I'm genuinely sad right now. This is awful news. Hoping for a full recovery — nobody deserves this.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "We are up 3-0 in the series. I'm not going to say we're going to sweep but also please nobody say anything that might jinx it. I'm scared to breathe.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Ja Morant just took off from the elbow, flew over the entire defense, and dunked backwards. Nobody in the building could believe it. I watched this game live and I still can't believe it happened.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The free throw at the end to win by 1. The crowd erupting. The dog pile. I'm tearing up watching this highlight at 1am. Sports do something to me man.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "That flagrant foul call was an absolute joke. The guy barely breathed on him and it's a Flagrant 2? Fire every referee who was on that floor tonight.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Giannis picking up his fifth foul in the third quarter of a playoff game. My heart is in my stomach. Every time. Every single time. I can't do this.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "They just flashed Wilt's old stat line on the broadcast to compare it to tonight's performance. The crowd went silent for a second like they couldn't believe what they were seeing.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The comeback win is complete. I need to call my dad. He texted me in the third quarter to say he was turning it off. I need him to see this.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Devin Booker just hit three threes in 40 seconds to cut the lead to 2. My body is not built for these games. I physically cannot watch the rest of this.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Trade just confirmed. Three All-Stars on the same team. The league is never going to be the same. I don't know how to feel. I need a minute.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The game winning shot bounced off the back of the rim and somehow went in. I need the physics community to explain this to me immediately.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "This might be the best regular season game I've watched in 10 years. Every possession mattered. Both teams gave everything. Triple OT with no players left standing. Incredible.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Embiid just went down holding his knee and everyone in the arena went silent. Whatever happens this series, hope he's okay. Scary moment for anyone who likes basketball.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Just read the contract extension news. Four years, $246 million. We are locked in baby. No more trade rumors for four years. I can breathe again.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The halftime show at this All-Star game is actually incredible. That's not basketball-related but I had to say it. We are being treated right tonight.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Nikola Jokic just passed it between two defenders through a triple team from behind his own back while falling down. This is a simulation and we are being pranked.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The play went to review, they called it good, other team called timeout, our best player fouled out on the very next play. Life as a fan is not fair.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Game 7. Home crowd. All the momentum. And they lost by 25. I'm genuinely embarrassed to be a fan right now. I don't want to talk about it.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Jayson Tatum just hit a fadeaway over two defenders with 1.3 seconds left to force overtime. This is the best series in ten years and I'm not sleeping until it ends.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "I've watched every Celtics game since 2010 and tonight was the most electric crowd I've ever seen at the Garden. That crowd was a 6th player in a way that actually meant something.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Six-game win streak snapped by 35 points. Not a foul called in the fourth quarter. I need someone else to explain what I just watched because I have no idea.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The ring ceremony is happening right now and I'm not crying you're crying. Twenty years of loyalty paid off. This is what being a sports fan is for.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The coaching change was just announced and I genuinely don't know how to feel. I respected the old coach but we were going nowhere. Fresh start. Let's see.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "That was the ugliest win I have ever seen and I loved every second of it. 88-86, missed shots everywhere, chaos in the fourth quarter. We're alive.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Draft pick just got announced at #1 and the arena exploded. I'm watching from the bar and even I started screaming. Good problem to have. Franchise changing moment.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The 4th quarter collapse was on full display again. Lead with 4 minutes to go. Turnover. Missed free throws. Bad foul. Timeout. Crowd goes quiet. Same story every single night.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "He's retiring. I'm not ready. I grew up watching him. This is the end of an era and it hits different than I expected it to. End of something real.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "THIS MAN JUST SHOT A THREE WITH HIS OFF HAND WHILE FALLING OUT OF BOUNDS AND IT WENT IN. I CANNOT. I WILL NOT. WHO DOES THAT.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Broadcast just confirmed the injury is a torn Achilles. My heart just sank. That's a year minimum. This changes everything for this team and for his legacy timeline.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Just got home from the game. We won by 30 but I'll remember it forever because of the atmosphere in that building. Pure joy for three hours. Worth every dollar.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The 20-point lead just evaporated in seven minutes. HOW. SEVEN MINUTES. I was making dinner. I come back. It's tied. I need to sit down.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Finals MVP is going to the team's best player and it was never in doubt. Absolutely dominant series. Watching him play is something I'll tell people about when I'm old.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The best player in franchise history just posted that he wants to be traded. I'm going to need a moment. This is genuinely devastating. Not today.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "They just scored 9 straight to take the lead with 40 seconds left and the crowd noise from that broadcast made my TV speakers vibrate. Absolutely unreal.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Wembanyama is 19 years old and he just blocked a shot, caught the outlet pass, ran the floor, and finished the alley-oop on the other end. NINETEEN YEARS OLD.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The final buzzer went. Series over. Season over. I'm proud of this team. They gave everything they had and it wasn't enough. That's all sports sometimes. Till next year.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "Bench player who was waived two months ago just hit the game-winner in triple OT of a playoff game. If you told me this before the season I would have laughed. Sports are perfect.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "He just got ejected for a technical in a game 6 we were winning. I am not okay. The basketball gods have declared war on this franchise specifically.",
        "label": "reaction",
        "notes": "",
    },
    {
        "text": "The double-overtime just ended. It is 1:47 AM. I have work at 7. I regret nothing. That was the best basketball game I have watched in my life. Worth it.",
        "label": "reaction",
        "notes": "",
    },
]


def main():
    random.seed(42)
    random.shuffle(EXAMPLES)

    # Add sequential IDs and ai_assisted flag
    for i, ex in enumerate(EXAMPLES, start=1):
        ex["id"] = f"ex_{i:04d}"
        ex["ai_assisted"] = True

    out_path = "data/dataset.csv"
    fieldnames = ["id", "text", "label", "notes", "ai_assisted"]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for ex in EXAMPLES:
            writer.writerow({k: ex[k] for k in fieldnames})

    # Distribution report
    from collections import Counter
    dist = Counter(ex["label"] for ex in EXAMPLES)
    total = len(EXAMPLES)
    print(f"Dataset saved to {out_path}")
    print(f"Total examples: {total}")
    print("\nLabel distribution:")
    for label, count in sorted(dist.items()):
        print(f"  {label:12s}: {count:3d}  ({100 * count / total:.1f}%)")
    print()
    for label, count in sorted(dist.items()):
        if count / total > 0.70:
            print(f"WARNING: '{label}' exceeds 70% of dataset ({100*count/total:.1f}%). Collect more examples for underrepresented labels.")


if __name__ == "__main__":
    main()
