import streamlit as st
from pages.components.sidebar import *

st.set_page_config(layout="wide")
render_sidebar()

st.header("Welcome to my dashboard for basketball-related data.")

msg = """
This streamlit app is a work in progress, so there may be bugs. For my projects, see the section below. To navigate to pages, see the sidebar. Current pages include: \n
[**Live Game Dashboard**](Live_Game_Dashboard): A dashboard containing scores, play by play data, and estimated metrics for active games.\n
[**Player Dashboard**](Player_Dashboard): Historical and current season stats for all NBA players.\n
[**Lineup Dashboard**](Lineup_Dashboard): This page is incomplete. Right now, it includes some estimated point per minute values
for a project I'm working on.\n
[**Reproduced Tracking Data**](Reproduced_Tracking_Data): This page allows the user to upload footage of a possession, and use 
a model I developed to extract tracking information. Note that the current iteration is not final; In particular, there are issues 
with keeping track of players when obscured by screens.\n
[**All Raw Data**](All_Raw_Data): This page provides a graphical interface to request data from the NBA's API.

**For the source code, see my [Github](https://github.com/nehal-chigurupati/NBADashboard).**
"""
st.markdown(msg)

st.header("My Projects")
with st.expander(label="Predicting the length of three-point slumps", expanded=False):
    st.subheader("Predicting the length of three-point slumps")
    st.markdown("[Link](https://medium.com/@jxuwrsb/predicting-the-length-and-occurrence-of-three-point-shooting-slumps-24a320615d76)")

    summary = """
    The objective of this project is to determine the probability of a three-point shooting slump extending over a given number of games, 
    and to evaluate strategies for overcoming such slumps. To make these determinations,
      I applied techniques from survival analysis, a method commonly used in clinical studies to assess mortality risks.
     I reached three main conclusions:

    **(1)** For volume three point shooters (> 250 3PA per season), there is only a 5 percent chance that a shooting slump extends past 32 games. 
    **Slumps longer than 32 games may be indicative of structural issues with the shot or player.**

    **(2)** The length of a shooting slump is inversely related with its severity (defined as the difference between career and slump 3PT%). 
    In other words, **the more inefficient a player is shooting during a slump, 
    the quicker they can expect to return to normal**.

    **(3)** Decreasing three point attempts per game extends slumps, while increasing 3 point attempts per game shortens slumps, 
    confirming that **shooters can shoot their way out of slumps**.
    """

    st.markdown(summary)

with st.expander(label='A metric for measuring the “range” of offensive and defensive talent for NBA teams in the 2023–24 season', expanded=False):
    st.subheader('A metric for measuring the “range” of offensive and defensive talent for NBA teams in the 2023–24 season')
    st.markdown("[Link](https://medium.com/@jxuwrsb/a-metric-for-measuring-the-range-of-offensive-and-defensive-talent-for-teams-a81944f78350)")

    summary = """

In this project, I attempt to answer the following question:

*In constructing a roster, is the best strategy to be proficient in a wide range of offensive/defensive plays or excel in a select few plays?*

To quantitatively measure the diversity of offensive and defensive skills on a roster, 
I introduce three new metrics referred to as offensive, defensive, and net range, using techniques from topological data analysis. 
These metrics approximate the diversity of a team’s proficiencies on offense and defense in common play types, 
including cuts, off-ball screens, isolation, post-up shooting, spot-up shooting, transition, and the pick and roll. 
Higher values of offensive range indicate that a team performs well on many of these play types. 
Similarly, higher values of defensive range indicate great diversity of defensive skill, while high values of net range indicate
 that a team is proficient in a wide variety of both offensive and defensive scenarios.

I computed offensive/defensive/net range for each team in the 2023–24 season
and examined how these quantities affect offensive rating, defensive rating, net rating, and win percentage.
I came to a few conclusions relevant to roster construction. 
First, teams should prioritize diversity of talent in both offensive and defensive play types.
Second, teams that are constructed to have a wide range of both offensive and defensive skills seem to perform
much better than teams that are designed to place all their chips on one side of the floor.
"""
    st.markdown(summary)


with st.expander(label="Reproducing NBA tracking data with computer vision", expanded=False):
    st.subheader("Reproducing NBA tracking data with computer vision")
    st.markdown("[Link](https://github.com/nehal-chigurupati/CourtVision/blob/main/README.pdf)")

    summary = """
    **This project is in progress**.

    The objective is to use computer vision to generate location and velocity data for players during NBA games, 
    extracted from broadcast footage. One particular application is also explored, introducing a spacing metric
    derived from the convex hull of the defenders' positions during a given halfcourt, five-out possession.
    """

    st.markdown(summary)

with st.expander(label="Using clustering to construct an offensively optimal lineup", expanded=False):
    st.subheader("Using clustering to construct an offensively optimal lineup")
    st.markdown("[Link](https://medium.com/@jxuwrsb/using-clustering-to-determine-crucial-skills-in-crafting-lineups-3b8f35681f5d)")
    summary = """
    The objective of this project is twofold:

    First, to determine clusters of NBA players who perform similarly on certain play types (isolation, cut, off-ball screen, handling in a pick and roll, rolling in a pick and roll, spot-up shooting, and post-up shooting). 
    For the technically inclined, I employed KMeans and Spectral Clustering to determine these groups of players.

    Second, to take the highest performing clusters of each play type,
    and break down which seem to be prevalent in offensively talented 2023–24 lineups (min. 100 minutes played together). 
    The result should explain the skills most important in crafting lineups.

    There were three major conclusions from this exercise:

    **(1)** In lineups with high offensive ratings, every player on the floor is efficient at spot-up shooting in high volumes, 
    suggesting that **teams should establish a high (>.9 PPP) baseline level of shooting** for players on the floor.

    **(2)** There was no clear relationship between isolation talent and offensive rating, suggesting that **teams should de-emphasize 
    isolation-heavy players when crafting lineups**.

    **(3)** Finally, highly efficient lineups often featured deadly pick and roll combos with big men and guards.
    The big men typically were excellent passers, shooters, and finishers, allowing an inverted pick and roll. 
    **Teams should target such versatile big men** during free agency and the trading season.
    """
    st.markdown(summary)


with st.expander(label="Evaluating 2024 free agent 3P shooters", expanded=False):
    st.subheader("Evaluating 2024 free agent 3P shooters")
    st.markdown("[Link](https://medium.com/@jxuwrsb/number-of-possessions-or-efficiency-per-possession-which-better-determines-offensive-success-a9a2282bdc2c)")
    summary = """
    This project aims to find skilled three point shooters available at a discount in 2024 free agency.
    I found free agents that are temporarily “hot” and “cold” from three point range this season by introducing a 
    new three-point efficiency metric called Bayesian 3P%, indicative of a player’s “true” three point skill, 
    and comparing it to 2023–24 season 3P%. 
    Among players whose Bayesian 3P% was higher than their season 3P% (i.e. players who are in a slump), 
    I constructed a model to estimate the discount in 2024–25 salary that a team could expect to get.
    Four players distinguished themselves as great shooters likely available for cheap: 
    Robert Covington, Wesley Matthews, Nicolas Batum, and Danilo Gallinari
    """
    st.write(summary)

with st.expander(label="Does pace matter for offensive success?", expanded=False):
    st.subheader("Does pace matter for offensive success?")
    st.markdown("[Link](https://medium.com/@jxuwrsb/number-of-possessions-or-efficiency-per-possession-which-better-determines-offensive-success-a9a2282bdc2c)")
    summary = """
    This analysis was motivated by the following excerpt from Ben Taylor’s Thinking About Basketball:

    “Basketball is a per-possession game… It does not matter if a team plays
    fast or slow; a team scoring 80 points can run a more efficient offense than
    a team scoring 100 points… if the team scoring 100 points needed more possessions. There is absolutely zero correlation between a team’s pace and its offensive efficiency… Because of alternating possession rules, basketball success is completely determined by per-possession efficiency. There is a near perfect correlation (0.97) between a team’s efficiency and wins” (pg. 32).

    To confirm, I attempted to determine whether there is correlation between pace, offensive rating and wins.
    """
    st.markdown(summary)


with st.expander(label="Can NBA teams win the year after large roster changes?", expanded=False):
    st.subheader("Can NBA teams win the year after large roster changes?")
    st.markdown("[Link](https://medium.com/@jxuwrsb/can-nba-teams-win-the-year-after-large-roster-changes-fd65b2ee783b)")

    summary = """
    This project examines the relationship between sizable off-season roster changes and regular season/playoff win counts, adjusted for gain in net rating. 
    Two conclusions were reached:

    **(1)** A higher proportion of changed personnel leads to a decreased probability of increasing regular season win count.

    **(2)** Teams are unlikely to increase playoff win count the season after changing more than 20 percent of the roster.

    Applied, these results suggest that **front offices should give rosters at least two seasons to develop before evaluating performance**.
    """
    st.markdown(summary)



with st.expander(label="How important is bench production to regular season and playoff success?", expanded=False):
    st.subheader("How important is bench production to regular season and playoff success?")
    st.markdown("[Link](https://medium.com/@jxuwrsb/how-important-is-bench-production-to-regular-season-and-playoff-success-fb2cccab7d83)")

    summary = """
    To determine the offensive importance of bench production on NBA rosters, I looked at four relationships:

    **(1)** Average bench PPG in the regular season and regular season offensive rating\n
    **(2)** Average bench PPG in the regular season and regular season win percentage\n
    **(3)** Average proportion of team points per game that come from the bench and regular season offensive rating\n
    **(4)** In a playoff series, the relationship between the likelihood of winning and the difference between the proportion of team/opponent points coming from the respective benches.\n
    Data for each of these questions was collected from the 2010–11 season to 2022–23.
    All of these variables were measured relative to season average (e.g. “average bench PPG” was measured as the z-score relative to season bench PPG for all teams).

    I found two key results:

    **(1)** The proportion of team points per game that come from the bench has a statistically significant, negative relationship with regular season win percentage.
    In other words, teams that rely heavily on their bench for offense tend to win fewer games.

    **(2)** In a playoff series, generating a higher proportion of total points from the bench or increasing bench production from regular season proportions has no correlation with winning/losing the series. 
    Put simply, bench production in a series does not impact the probability of winning/losing.

    Applied to coaching and roster construction, the lesson contained in the above conclusions is that 
    **the distribution of points between the starting lineup and bench does not impact winning, in the regular season or playoffs**. 
    Teams should not feel the need to switch players from the starting lineup to the bench in order to “equalize” the point production of the two squads.
    """

    st.markdown(summary)



with st.expander(label="Evaluating lineups and players by the quality of looks they generate", expanded=False):
    st.subheader("Evaluating lineups and players by the quality of looks they generate")
    st.markdown("[Link](https://medium.com/@jxuwrsb/evaluating-lineups-by-the-quality-of-looks-generated-e5f7f5b3fa4d)")

    summary = """
    **This project is in progress**. 
    
    The objective is to assign an expected point-per-minute value
    to each lineup. To compute expected point-per-minute, I take every shot a lineup has attempted,
    find the exact location of the shot and the distance to the nearest defender. For the player who attempted the shot,
    I compute their shooting percentage on similar attempts, and multiply the shot value by this quantity. I then sum
    the resulting values over all attempts and divide by the number of minutes a lineup has played together, to get an 
    expected point production per minute. 

    After assigning an expected point per minute value to each lineup, a secondary objective is to run 
    a ridge regression to try and isolate individual player impact. The associated coefficient for each player
    should represent their "skill" at generating good looks for teammates. 
    """
    st.markdown(summary)