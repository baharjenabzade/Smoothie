from app.clusters import CLUSTER_SLUGS, CLUSTERS, clusters_for_topic
from app.seed_data import iter_seed_questions


def test_every_cluster_topic_has_a_seeded_question():
    topics = {q["topic"] for q in iter_seed_questions()}
    for cluster in CLUSTERS:
        missing = [t for t in cluster.topics if t not in topics]
        assert not missing, f"{cluster.slug}: {missing}"
        assert len(cluster.topics) == len(set(cluster.topics))


def test_topics_can_belong_to_several_clusters():
    assert set(clusters_for_topic("Gadget you own")) == {"technology", "money"}
    assert clusters_for_topic("nope") == []
    assert len(CLUSTER_SLUGS) == len(CLUSTERS)


