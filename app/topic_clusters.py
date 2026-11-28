"""Topic clusters: broad themes that group related speaking topics.

A *topic* is a Part 2 cue card plus the Part 1 and Part 3 questions that go with it. Topics can
belong to several clusters (an app you use is both Technology and Daily Life), and the relatedness
of topics is computed from shared clusters plus shared theme words. Pure data and pure functions.
All wording is original.
"""

import re
from dataclasses import dataclass

# id, name, one-line description
CLUSTERS: list[tuple[str, str, str]] = [
    ("tech", "Technology & Digital Life", "Websites, apps, devices and life online"),
    ("people", "People & Relationships", "Family, friends, teachers and role models"),
    ("money", "Money, Shopping & Decisions", "Buying, saving and choosing"),
    ("time", "Time, Memories & Experiences", "Childhood, events and moments that stayed with you"),
    ("learn", "Education, Learning & Skills", "Schools, teachers, books and new skills"),
    ("nature", "Nature, Environment & Travel", "Journeys, weather, wildlife and green habits"),
    ("work", "Work, Careers & Ambitions", "Jobs, goals, teamwork and challenges"),
    ("culture", "Culture, Art & Entertainment", "Films, music, festivals and hobbies"),
    ("food", "Food, Health & Lifestyle", "Meals, cooking, sport and healthy habits"),
    ("places", "Places, Buildings & Hometowns", "Where you live, visit and relax"),
]

# id | title | cue card prompt | 4 cue points | theme words | 2 Part 1 questions | 2 Part 3 questions | clusters
_RAW: list[tuple[str, str, str, str, str, str, str, str]] = [
    ("tech-website", "A useful website", "Describe a website that you find useful.",
     "what the website is|how often you visit it|what you use it for|why it is useful to you",
     "internet online website search information platform free study research",
     "Do you spend much time on the internet?|What websites do you visit most?",
     "Has the internet made people better informed?|Should children be taught how to check online information?", "tech,learn"),
    ("tech-app", "An app you often use", "Describe an app on your phone that you use often.",
     "what the app is|when you started using it|what you use it for|and explain how it makes your life easier",
     "phone app mobile smartphone daily convenient notification download routine",
     "Do you use your phone a lot?|What apps do you use every day?",
     "Do people depend too much on their phones?|How might mobile apps change in the future?", "tech,food"),
    ("tech-gadget", "A piece of technology you own", "Describe a piece of technology that you own and value.",
     "what it is|when and how you got it|what you use it for|and explain why it is important to you",
     "device gadget laptop computer camera headphones electronic battery screen buy",
     "Are you interested in new technology?|Do you prefer to repair or replace broken devices?",
     "Is technology making life simpler or more complicated?|Why do some people always want the newest gadget?", "tech,money"),
    ("tech-social", "A social media platform", "Describe a social media platform that you know well.",
     "which platform it is|how you use it|who you follow or talk to|and explain what you like or dislike about it",
     "social media post share friends followers online chat message network communication",
     "Do you use social media?|Do you prefer messaging or calling people?",
     "How has social media changed friendships?|Should there be age limits for social media?", "tech,people"),
    ("tech-online-learning", "A time you learned online", "Describe something you learned by using the internet.",
     "what you learned|where you found the lessons|how long it took you|and explain how you felt about learning online",
     "online course video tutorial lesson learn skill study practise free youtube website",
     "Have you ever studied online?|Do you prefer videos or books for learning?",
     "Will online learning replace classrooms?|What makes someone a good self-taught learner?", "tech,learn"),
    ("tech-invention", "A useful invention", "Describe an invention that you think has been very useful.",
     "what the invention is|when it was invented|how people use it|and explain why you think it is so useful",
     "invention machine technology history convenience science tool electricity engine",
     "Do you like finding out how things work?|Which everyday objects could you not live without?",
     "Which invention has changed society most?|Are modern inventions always an improvement?", "tech,time"),

    ("ppl-influential", "A person who influenced you", "Describe a person who has had a strong influence on you.",
     "who the person is|how you know them|what they did or said|and explain how they influenced you",
     "influence role model inspire advice mentor admire guide example character",
     "Who do you ask for advice?|Are you similar to your parents?",
     "Who are the main role models for young people today?|Can a stranger influence your life?", "people,time"),
    ("ppl-helped", "A person who helped you", "Describe a time when someone helped you.",
     "who helped you|what the problem was|how they helped|and explain how you felt afterwards",
     "help support kindness problem friend stranger neighbour grateful thank advice",
     "Do you often help other people?|Who do you turn to when you have a problem?",
     "Why do some people volunteer to help strangers?|Should schools teach children to help others?", "people"),
    ("ppl-admire", "Someone you admire", "Describe someone you admire.",
     "who the person is|how you know about them|what they have achieved|and explain why you admire them",
     "admire respect achievement famous hero qualities courage hard work success",
     "Is there a famous person you like?|What qualities do you value in people?",
     "Do celebrities deserve their influence?|Is it better to admire people you know personally?", "people,culture"),
    ("ppl-job", "A person with an interesting job", "Describe a person who has an interesting job.",
     "who the person is|what their job is|what they do every day|and explain why you find the job interesting",
     "job career profession work daily colleague skill unusual responsibility salary",
     "What jobs did you want when you were small?|Do you know anyone with an unusual job?",
     "Which jobs are most valuable to society?|Will robots take over many jobs?", "people,work"),
    ("ppl-friend", "A person you enjoy spending time with", "Describe a person you enjoy spending time with.",
     "who the person is|how long you have known them|what you do together|and explain why you enjoy their company",
     "friend company together fun conversation weekend hobby close trust laugh",
     "Do you prefer spending time with friends or alone?|How often do you see your friends?",
     "Is it easy to make friends as an adult?|How have friendships changed with technology?", "people,time"),
    ("ppl-family", "A family member you are close to", "Describe a member of your family you are close to.",
     "who the person is|what they are like|what you do together|and explain why you are close",
     "family parent sister brother grandparent relative home generation tradition support",
     "Do you come from a large family?|Do you spend much time with your relatives?",
     "How have family roles changed in recent decades?|Should elderly relatives live with their families?", "people"),

    ("money-expensive", "Something expensive you bought", "Describe something expensive that you bought.",
     "what you bought|why you bought it|how long you thought about it|and explain whether it was worth the money",
     "expensive buy price worth money spend luxury quality decision regret purchase",
     "Do you like spending money?|Do you usually buy things online or in shops?",
     "Why do people buy things they do not need?|Is expensive always better quality?", "money"),
    ("money-saved", "Something you saved money for", "Describe something you saved money for.",
     "what you saved for|how long it took|how you managed to save|and explain how you felt when you finally bought it",
     "save saving money budget patient goal plan reward free cheap spend wisely",
     "Are you good at saving money?|Did you get pocket money as a child?",
     "Should children learn to manage money at school?|Why do some people find it hard to save?", "money,work"),
    ("money-shopping", "A shopping experience", "Describe a shopping trip that you remember.",
     "where you went|who you went with|what you bought or saw|and explain why you remember it",
     "shopping shop market mall sale bargain clothes crowd online customer queue",
     "Do you enjoy shopping?|Do you prefer big shopping centres or small shops?",
     "Is online shopping better than shopping in person?|Why do shops use sales and special offers?", "money,places"),
    ("money-decision", "An important decision", "Describe an important decision you made.",
     "what the decision was|what choices you had|how you decided|and explain whether it was a good decision",
     "decision choice choose option advice risk future change plan consequence think",
     "Do you make decisions quickly or slowly?|Who do you ask when you cannot decide?",
     "Should young people make their own big decisions?|Is it better to follow advice or trust yourself?", "money,time"),
    ("money-want", "Something you want to buy", "Describe something you would like to buy in the future.",
     "what it is|where you would buy it|how much it costs|and explain why you want it",
     "want wish buy future save price dream gift need luxury plan own",
     "Is there anything you really want to buy?|Do you often buy gifts for others?",
     "Are people today more materialistic than before?|How does advertising influence what we buy?", "money"),

    ("time-childhood", "A childhood memory", "Describe a happy memory from your childhood.",
     "when it happened|where you were and who was there|what happened|and explain why you remember it so well",
     "childhood memory remember young school play grandparents toy past happy family",
     "Did you enjoy your childhood?|What did you like to do as a child?",
     "How is childhood today different from the past?|Do childhood experiences shape adult life?", "time,people"),
    ("time-celebration", "A special day or celebration", "Describe a special day that you celebrated.",
     "what the occasion was|who was there|what you did|and explain why it was special",
     "celebration birthday wedding party holiday festival gift together dress food music",
     "How do you usually celebrate your birthday?|Do you like parties?",
     "Why are celebrations important for communities?|Are traditional celebrations disappearing?", "time,culture"),
    ("time-wait", "A time you had to wait", "Describe a time when you had to wait for something.",
     "what you were waiting for|how long you waited|what you did while waiting|and explain how you felt",
     "wait waiting patient late delay queue bus airport time boring annoyed",
     "Are you a patient person?|What do you do when you have to wait?",
     "Why are people less patient today?|Is waiting ever a good thing?", "time"),
    ("time-routine", "A daily routine you enjoy", "Describe part of your daily routine that you enjoy.",
     "what the routine is|when you do it|who you do it with|and explain why you enjoy it",
     "routine daily morning evening habit schedule relax coffee walk time regular",
     "What is your typical morning like?|Do you prefer mornings or evenings?",
     "Do routines make people happier?|Is it good to keep the same routine every day?", "time,food"),
    ("time-photo", "A photo that means a lot to you", "Describe a photograph that is special to you.",
     "where and when it was taken|what it shows|who took it|and explain why it is special to you",
     "photo photograph camera picture memory moment family travel frame album remember",
     "Do you like taking photos?|Do you keep photos on your phone or print them?",
     "Why do people share so many photos online?|Do photos help us remember things better?", "time,tech"),

    ("learn-skill", "A skill you learned", "Describe a useful skill that you learned.",
     "what the skill is|how you learned it|how long it took|and explain how it has been useful to you",
     "skill learn practise lesson teach course improve master hobby free time progress confident",
     "Would you like to learn a new skill?|Do you learn better alone or with others?",
     "Which skills should schools teach more of?|Is it ever too late to learn something new?", "learn,work"),
    ("learn-teacher", "A teacher you remember", "Describe a teacher who was important to you.",
     "who the teacher was|what they taught|what they were like|and explain why you remember them",
     "teacher school lesson class student patient strict kind subject university learn encourage",
     "Did you like your school?|Who was your favourite teacher?",
     "What makes a good teacher?|Should teachers be paid more?", "learn,people"),
    ("learn-subject", "A subject you enjoyed at school", "Describe a school subject you enjoyed.",
     "what the subject was|what you learned|who taught it|and explain why you enjoyed it",
     "subject school science maths history language art class exam homework interest enjoy",
     "What was your favourite subject?|Did you do homework willingly?",
     "Should schools focus on practical subjects?|Are exams the best way to measure learning?", "learn"),
    ("learn-book", "A book you enjoyed", "Describe a book that you enjoyed reading.",
     "what the book is|what it is about|when you read it|and explain why you enjoyed it",
     "book read story novel author character library chapter writer imagination ebook",
     "Do you like reading?|Do you prefer paper books or e-books?",
     "Are people reading less than in the past?|Why do some books become very popular?", "learn,culture"),

    ("nature-journey", "A memorable journey", "Describe a journey that you remember well.",
     "where you went|who you went with|what happened on the way|and explain why it was memorable",
     "journey trip travel train plane road holiday adventure destination memory luggage explore",
     "Do you like travelling?|Do you prefer long trips or short breaks?",
     "How has travel changed in the last fifty years?|Does tourism help or harm popular places?", "nature,time"),
    ("nature-park", "A natural place you like", "Describe a park or natural place that you like to visit.",
     "where it is|how you get there|what you do there|and explain why you like it",
     "park nature garden forest river mountain beach green walk fresh air peaceful trees",
     "Do you spend time outdoors?|Are there many green spaces near you?",
     "Why should cities protect green spaces?|Do people spend too little time in nature?", "nature,places"),
    ("nature-weather", "A time the weather affected your plans", "Describe a time when the weather changed your plans.",
     "what you had planned|what the weather was like|how you changed your plans|and explain how you felt about it",
     "weather rain storm snow hot cold plan change cancel outdoor season sunny wind",
     "What is the weather like where you live?|Does weather affect your mood?",
     "How is climate change affecting daily life?|Should people be prepared for extreme weather?", "nature,time"),
    ("nature-animal", "An animal you like", "Describe an animal that you like.",
     "what the animal is|where you have seen it|what it is like|and explain why you like it",
     "animal pet dog cat wildlife zoo bird farm nature care protect species",
     "Do you have a pet?|Did you have a pet as a child?",
     "Should wild animals be kept in zoos?|Why do some people spend so much on their pets?", "nature"),
    ("nature-green", "Something you do to protect the environment", "Describe something you do to help the environment.",
     "what you do|how often you do it|how you started|and explain why you think it matters",
     "environment recycle plastic waste energy green pollution save planet climate reuse transport",
     "Do you recycle?|Do you think about the environment when you shop?",
     "Who should do more for the environment: people or governments?|Can small actions make a difference?", "nature,money"),
    ("nature-visit", "A place you would like to visit", "Describe a place you would like to visit in the future.",
     "where it is|how you would get there|what you would do there|and explain why you want to go",
     "visit travel destination country city culture sightseeing dream holiday abroad explore future",
     "Which countries have you visited?|Would you like to live abroad?",
     "Why do people enjoy visiting other countries?|Is it better to travel alone or in a group?", "nature,places"),

    ("work-dream-job", "A job you would like to have", "Describe a job you would like to have in the future.",
     "what the job is|what you would do|what skills you need|and explain why it attracts you",
     "job career future work skill salary ambition company profession training qualification dream",
     "Do you work or study?|What do you like about your job or studies?",
     "What makes a job satisfying?|Should people change careers during their lives?", "work,learn"),
    ("work-goal", "A goal you want to achieve", "Describe a goal that you hope to achieve.",
     "what the goal is|why you chose it|what you are doing to reach it|and explain how you will feel if you succeed",
     "goal achieve ambition plan future target progress motivation success effort dream",
     "Do you set goals for yourself?|What do you want to do in five years?",
     "Why do some people achieve their goals while others do not?|Is ambition always positive?", "work,time"),
    ("work-team", "A time you worked with others", "Describe a time you worked in a team.",
     "what the task was|who you worked with|what your role was|and explain how well the team worked",
     "team group project work together colleague role cooperate share task leader deadline",
     "Do you prefer working alone or in a team?|Have you done group projects?",
     "What makes a team successful?|Is competition or cooperation better in the workplace?", "work,people"),
    ("work-challenge", "A time you faced a challenge", "Describe a time you faced a difficult challenge.",
     "what the challenge was|why it was difficult|how you dealt with it|and explain what you learned",
     "challenge difficult problem overcome effort stress solve learn pressure proud brave deadline",
     "Do you enjoy challenges?|How do you deal with stress?",
     "Do difficult experiences make people stronger?|Should schools make tasks harder for students?", "work,time"),
    ("work-busy", "A time you were very busy", "Describe a time when you were very busy.",
     "when it was|what you had to do|how you managed your time|and explain how you felt",
     "busy time manage deadline schedule tired plan task pressure rest balance workload",
     "Are you often busy?|How do you relax after a busy day?",
     "Are people today busier than in the past?|How can employers help workers keep a good balance?", "work,time"),

    ("culture-film", "A film you enjoyed", "Describe a film that you enjoyed watching.",
     "what the film was|what it was about|who you watched it with|and explain why you enjoyed it",
     "film movie cinema actor story director watch plot scene series entertainment",
     "Do you like going to the cinema?|What kinds of films do you prefer?",
     "Do films influence how people behave?|Is cinema still important in the age of streaming?", "culture"),
    ("culture-music", "A piece of music you like", "Describe a piece of music that you like.",
     "what the music is|when you first heard it|when you listen to it|and explain why you like it",
     "music song listen concert band singer instrument rhythm mood playlist artist lyrics",
     "Do you listen to music every day?|Can you play a musical instrument?",
     "Why is music important in every culture?|Should schools make music lessons compulsory?", "culture"),
    ("culture-festival", "A festival or tradition", "Describe a festival or tradition in your country.",
     "what it is|when it takes place|what people do|and explain why it is important to people",
     "festival tradition custom culture celebrate holiday heritage community food costume history",
     "Are there festivals in your hometown?|Which holiday do you like best?",
     "Are traditions important in modern society?|How do festivals affect local businesses?", "culture,time"),
    ("culture-art", "A work of art you like", "Describe a painting, statue or other work of art you like.",
     "what it is|where you saw it|what it looks like|and explain why you like it",
     "art painting museum gallery sculpture artist colour design creative exhibition beautiful",
     "Do you enjoy visiting museums?|Did you draw or paint as a child?",
     "Should governments spend money on art?|Is art a necessary part of education?", "culture,places"),
    ("culture-hobby", "A hobby you enjoy", "Describe a hobby that you enjoy.",
     "what the hobby is|how you started it|how often you do it|and explain why you enjoy it",
     "hobby free time leisure enjoy relax collect craft game weekend interest club passion",
     "What do you do in your free time?|Has your hobby changed since you were younger?",
     "Do people have enough leisure time today?|Should hobbies be shared or personal?", "culture,food"),

    ("food-meal", "A meal you enjoyed", "Describe a meal that you enjoyed.",
     "where you had it|who you were with|what you ate|and explain why you enjoyed it",
     "meal food dinner restaurant taste delicious cook family flavour dish eat table",
     "What is your favourite food?|Do you usually eat at home or eat out?",
     "How have eating habits changed in your country?|Why do families eat together less often?", "food,people"),
    ("food-cook", "A dish you can cook", "Describe a dish that you know how to cook.",
     "what the dish is|how you learned to make it|how you make it|and explain why you like cooking it",
     "cook recipe kitchen ingredients dish prepare taste learn chop fresh homemade",
     "Do you enjoy cooking?|Who cooks in your home?",
     "Should cooking be taught in schools?|Are cooking shows popular for a good reason?", "food,learn"),
    ("food-healthy", "Something you do to stay healthy", "Describe something you do to stay healthy.",
     "what you do|how often you do it|how you started|and explain how it helps you",
     "healthy health exercise diet sleep fitness habit walk vegetables stress energy routine",
     "Do you try to eat healthily?|How much sleep do you usually get?",
     "Whose job is it to keep people healthy?|Why is it hard to keep healthy habits?", "food,time"),
    ("food-sport", "A sport or activity you enjoy", "Describe a sport or physical activity that you enjoy.",
     "what it is|where and when you do it|who you do it with|and explain why you enjoy it",
     "sport exercise team play match fitness gym swimming running football training active",
     "Do you play any sports?|Do you like watching sport?",
     "Should sport be compulsory at school?|Why are professional athletes paid so much?", "food,culture"),
    ("food-restaurant", "A restaurant you like", "Describe a restaurant that you like going to.",
     "where it is|what it is like|what you usually eat there|and explain why you like it",
     "restaurant cafe menu waiter service atmosphere price eat out table dinner friends",
     "How often do you eat out?|Do you prefer cafes or restaurants?",
     "Is eating out becoming more popular?|Why do some restaurants fail?", "food,places"),

    ("place-hometown", "The place where you grew up", "Describe the place where you grew up.",
     "where it is|what it is like|what you did there|and explain how you feel about it now",
     "hometown city village grew up neighbourhood street community childhood change local quiet",
     "Where is your hometown?|Would you like to live there in the future?",
     "Why are young people leaving rural areas?|How do cities change over time?", "places,time"),
    ("place-building", "A building you like", "Describe a building that you like.",
     "where it is|what it looks like|what it is used for|and explain why you like it",
     "building architecture design tower old modern famous history city structure window",
     "Do you live in a house or a flat?|What buildings are there near you?",
     "Should old buildings be kept or replaced?|How does architecture affect the way people feel?", "places,culture"),
    ("place-relax", "A place where you relax", "Describe a place where you like to relax.",
     "where it is|how often you go there|what you do there|and explain why it helps you relax",
     "relax place quiet calm home room garden cafe peaceful rest comfortable escape stress",
     "Which room at home do you like best?|Do you like quiet places?",
     "Why do people need quiet places in busy cities?|Does where you live affect your happiness?", "places,food"),
    ("place-recommend", "A place to recommend to visitors", "Describe a place in your city that you would recommend to visitors.",
     "where it is|what visitors can see or do|how to get there|and explain why you would recommend it",
     "recommend visitor tourist city sightseeing museum market local transport guide attraction",
     "Is your city a good place for visitors?|What do tourists usually do there?",
     "How can cities attract more tourists?|Do tourists change the places they visit?", "places,nature"),
]


@dataclass(frozen=True)
class Topic:
    id: str
    title: str
    prompt: str
    cue_points: tuple[str, ...]
    themes: str
    part1: tuple[str, ...]
    part3: tuple[str, ...]
    cluster_ids: tuple[str, ...]


TOPICS: dict[str, Topic] = {
    r[0]: Topic(r[0], r[1], r[2], tuple(r[3].split("|")), r[4], tuple(r[5].split("|")), tuple(r[6].split("|")), tuple(r[7].split(",")))
    for r in _RAW
}
CLUSTER_NAMES = {cid: name for cid, name, _ in CLUSTERS}

_WORD = re.compile(r"[a-z]+")


def _themes(topic: Topic) -> set[str]:
    return set(_WORD.findall(f"{topic.themes} {topic.title.lower()}"))


def related_topic_ids(topic_id: str, limit: int = 6) -> list[str]:
    """Topics that share clusters (strongest signal) or theme words with this one."""
    base = TOPICS[topic_id]
    base_words = _themes(base)
    scored = []
    for other in TOPICS.values():
        if other.id == topic_id:
            continue
        shared = len(set(base.cluster_ids) & set(other.cluster_ids))
        words = len(base_words & _themes(other))
        score = 3 * shared + words
        if shared or words >= 3:
            scored.append((-score, other.id))
    return [tid for _, tid in sorted(scored)[:limit]]


def validate() -> list[str]:
    """Return a list of data problems (empty when consistent). Used by the test suite."""
    problems = []
    known = set(CLUSTER_NAMES)
    for t in TOPICS.values():
        if not set(t.cluster_ids) <= known:
            problems.append(f"{t.id}: unknown cluster")
        if len(t.cue_points) != 4 or len(t.part1) != 2 or len(t.part3) != 2:
            problems.append(f"{t.id}: expected 4 cue points, 2 Part 1 and 2 Part 3 questions")
    for cid in known:
        if not [t for t in TOPICS.values() if cid in t.cluster_ids]:
            problems.append(f"cluster {cid} is empty")
    if len(TOPICS) != len(_RAW):
        problems.append("duplicate topic id")
    return problems


def catalogue() -> dict:
    """JSON-ready payload for the frontend."""
    return {
        "clusters": [
            {"id": cid, "name": name, "blurb": blurb, "topic_ids": [t.id for t in TOPICS.values() if cid in t.cluster_ids]}
            for cid, name, blurb in CLUSTERS
        ],
        "topics": [
            {
                "id": t.id,
                "title": t.title,
                "prompt": t.prompt,
                "cue_points": list(t.cue_points),
                "part1": list(t.part1),
                "part3": list(t.part3),
                "cluster_ids": list(t.cluster_ids),
                "related_ids": related_topic_ids(t.id),
            }
            for t in TOPICS.values()
        ],
    }
