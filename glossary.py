"""Tooltip text. KPI wording follows the original dashboard notebook; model terms are written for the same readers."""

DEFS = {
    "reviews": ("Reviews",
                "The number of distinct patient reviews in view. A review published under both a brand and a generic "
                "name counts once, because it is one patient's opinion.", ""),
    "mean": ("Average Rating Score",
             "The average of all the rating scores patients gave. Because scores gather at the two ends of the scale, "
             "this figure lands in the middle, where few patients actually scored.", ""),
    "median": ("Typical Patient Rating Score",
               "The middle score once every rating is lined up in order. Half the patients scored at or below it and "
               "half at or above, so it is unmoved by how extreme the extremes are.", ""),
    "mode": ("Most Frequent Patient Rating Score", "The score patients chose more often than any other.", ""),
    "polarshare": ("Polarised Review Share",
                   "The share of reviews that were either the lowest possible score or the highest possible score, with "
                   "nothing in between counted.",
                   "A high share means patients tended to love a medication or hate it, with few landing anywhere in the "
                   "middle."),
    "thinavg": ("Averages Built on One or Two Reviews",
                "How many medications have a published average that rests on only one or two patients.",
                "These averages swing wildly. Nearly four in ten of them show a flawless perfect score, which almost "
                "never happens once a medication has real numbers behind it. Wherever one of these appears on a "
                "ranking, its position is unproven."),
    "spread": ("Spread of averages",
               "How far apart the medication averages in a group sit from each other, in rating points (the standard "
               "deviation).",
               "A wide spread among medications with few reviews means their averages are mostly chance. Once the "
               "spread levels off, an average has enough reviews behind it to compare."),
    "rankmin": ("Ranking threshold",
                "Medications need at least 30 reviews before their average is used to rank or promote them.",
                "Below that, an average still moves a lot with each new review."),
    "high8": ("Rated 8 or above",
              "The share of reviews that gave a score of 8, 9 or 10, the High rating group.",
              "It shows how often patients came away clearly satisfied, without being pulled about by the extremes "
              "the way an average is."),
    "records": ("Records",
                "Every row in the file, including the copies created when the same review appears under a brand name and a "
                "generic name.", "Counts of volume use records; every rating figure uses distinct reviews."),
    "meds": ("Medications",
             "The medication the patient reviewed. Brand and generic names are recorded separately, so each is counted on its own.", ""),
    "conds": ("Conditions", "The condition the patient is taking the treatment for.", ""),
    "avgvotes": ("Average Number of Helpful Votes",
                 "The helpful votes a review collects on average, worked out by dividing every vote cast by every review in view.",
                 "A few reviews are read enormously more than the rest, which pulls this figure above anything a typical review "
                 "receives. Read it as the size of the total rather than as what one review can expect."),
    "polar": ("Rated 1 or 10", "The share of reviews sitting at one extreme of the scale or the other.",
              "It measures how divided reviewers are. People who write drug reviews tend to be either grateful or angry, and "
              "that split is what makes the average misleading."),
    "top10": ("Score Needed to Reach the Top 10%",
              "The rating a medication has to average before it counts among the ten per cent best received.",
              "An average on its own is hard to judge. Knowing the entry price for the top tenth tells you straight away whether "
              "a 7.5 is strong or ordinary."),
    # Model terms
    "balacc": ("Balanced accuracy",
               "The average of the hit rates in the Low, Middle and High groups, so each group counts equally.",
               "Plain accuracy rewards guessing the most common group; balanced accuracy does not."),
    "recall_low": ("Recall on Low", "The share of truly Low reviews (1 to 3 stars) the model finds.",
                   "Low reviews are the ones a pharmacy team must not miss."),
    "severe": ("Severe errors", "The share of reviews put at the opposite end: Low called High, or High called Low.",
               "These are the mistakes that would file a complaint with the praise."),
    "capture": ("Low found reading the top 20%",
                "If messages are sorted by the model's chance of Low and a team reads only the top fifth, this is the "
                "share of all Low reviews it finds. Reading in arrival order finds 20%.", ""),
    "auc": ("ROC AUC",
            "The chance the model ranks a random helpful review above a random unhelpful one. 0.5 is chance, 1.0 is "
            "perfect.", ""),
    "prec10": ("Precision in the top 10%",
               "Among the 10% of reviews the model ranks highest, the share that truly reached the top 25% of their "
               "month.", "The base rate to beat is about 25%."),
    "vader_agree": ("Wording agrees with stars",
                    "The share of reviews where VADER's mood label (positive, neutral, negative) matches the rating "
                    "group the reviewer chose.", ""),
}


def tip_parts(key):
    return DEFS.get(key, (key, "", ""))
