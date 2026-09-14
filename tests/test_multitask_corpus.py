from training.generate_synthetic import generate_records
from training.train_core import record_to_batch, target_operation


def test_generator_contains_multiple_graph_cognition_tasks_and_targets():
    rows = generate_records(seed=19, train_count=24, dev_count=8, blind_count=8)
    train = [r for r in rows if r["split"] == "train"]
    tasks = {r["task"] for r in train}
    assert {"transitive_reasoning", "location_lookup", "ownership_lookup", "world_revision"}.issubset(tasks)

    ops = {target_operation(r) for r in train}
    assert 5 in ops  # ANSWER
    assert 4 in ops  # RETRACT

    for row in train:
        batch = record_to_batch(row)
        assert batch.node_states.shape[0] == 1
        assert batch.node_states.shape[1] == len(row["entities"])
        assert batch.edge_index.shape[-1] == 2
