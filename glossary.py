"""Tooltip text. KPI wording follows the original dashboard notebook; model terms are written for the same readers."""

DEFS = {
    "reviews": ("Reviews",
                "The number of patient reviews in view. A review listed under both a brand and a generic "
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
    # Reviews Analysis
    "sentiment": ("Tone of the wording",
                  "Whether the words in a review read as positive, neutral or negative, judged from the text alone and "
                  "not from the star rating.", "The three shares add up to 100%."),
    "vader_agree": ("Wording Matches Rating",
                    "The share of reviews whose tone (positive, neutral or negative) matches the star rating the patient gave.",
                    "When the two disagree, the review is usually mixed, sarcastic or about something other than the medication."),
    "watchlist": ("Topics",
                  "Reviews are scanned for words and phrases in six topics: side effects, switching medication, cost, "
                  "the medication working, the medication not working, and dosage.",
                  "A review can mention several topics, so the shares do not add up to 100%."),
    "themes": ("Themes",
               "Reviews grouped by what they talk about, based on the meaning of the text rather than single words. Each "
               "theme is named by its most typical words.", ""),
    "words": ("Words in low and high ratings",
              "The words that appear far more often in one group than the other.",
              "Larger words rank higher. Size shows rank only, not how much stronger one word is than the next. Words such as years and mg are real results: happy reviewers often write that they have used a medication for years, or name the dose that works."),
    # Predictive and model terms
    "test_reviews": ("Reviews checked",
                     "Reviews posted in 2016 and 2017. The models learned only from earlier reviews, so these show how they "
                     "perform on new messages.", "The year filter does not apply on this page."),
    "groups": ("Rating groups", "Low is a rating of 1 to 3, Middle 4 to 7 and High 8 to 10.",
               "Low messages most likely describe a poor experience and should be read first."),
    "balacc": ("Balanced Accuracy",
               "How often the model picks the right group, averaged so Low, Middle and High count equally.",
               "A model that always guesses the most common group scores well on plain accuracy but poorly here."),
    "recall_low": ("Recall on Low", "Of the reviews patients really rated 1 to 3, the share the model flags as Low.",
                   "These are the messages a pharmacy team must not miss."),
    "severe": ("Severe Errors", "Reviews put at the opposite end of the scale: a poor experience flagged as positive, or the reverse.",
               "These are the mistakes that would file a complaint with the praise."),
    "capture": ("Low Found in the Top 20%",
                "If the inbox is sorted by the model's chance of a poor experience and the team reads only the first fifth, "
                "this is the share of all poor experiences it finds.", "Reading in arrival order finds 20%."),
    "auc": ("ROC AUC",
            "How well the model ranks reviews: the chance a truly helpful review scores higher than one that is not. "
            "0.5 is a coin toss, 1.0 is perfect.", ""),
    "prec10": ("Precision in the Top 10%",
               "Of the 10% of reviews the model ranks highest, the share that really were among the most helpful quarter of their month.",
               "Picking at random would give about 25%."),
    # Data dictionary
    "source_cols": ("Source columns", "The seven columns in the original Drugs.com file, with the known problems in each.", ""),
    "basis": ("How figures are counted",
              "Counts of medications, conditions and records use all 215,063 rows. Every rating figure uses the 130,558 "
              "distinct reviews, so each patient counts once.", ""),
}


def tip_parts(key):
    return DEFS.get(key, (key, "", ""))
