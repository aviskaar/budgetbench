from unittest.mock import MagicMock

from budgetbench.tasks.memory import MemoryUpdateTask


def test_memory_task_dataset_categories():
    task = MemoryUpdateTask()
    items = task.get_dataset(limit=10)
    categories = {item["category"] for item in items}

    assert len(items) == 10
    assert {
        "single_session_fact",
        "knowledge_update",
        "temporal_reasoning",
        "preference",
        "abstention",
    }.issubset(categories)


def test_memory_task_format_and_natural_tokens():
    task = MemoryUpdateTask()
    item = task.get_dataset(limit=1)[0]

    messages = task.format_message(item)
    token_count = task.natural_prompt_token_count(
        item,
        tokenizer_fn=lambda text: len(text.split()),
    )

    assert messages[0]["role"] == "system"
    assert messages[-1]["content"].startswith("Question:")
    assert token_count > 512


def test_memory_task_metric_context_includes_category():
    task = MemoryUpdateTask()
    item = task.get_dataset(limit=1)[0]

    assert task.metric_context(item) == {"memory_category": item["category"]}


def test_memory_task_grade_exact_and_answer_prefix():
    task = MemoryUpdateTask()
    item = task.get_dataset(limit=1)[0]

    assert task.grade(item["answer"], item) is True
    assert task.grade(f"Answer: {item['answer']}", item) is True
    assert task.grade("wrong", item) is False


def test_memory_task_run_uses_strategy_and_extracts_response(tokenizer_fn):
    task = MemoryUpdateTask()
    item = task.get_dataset(limit=1)[0]
    strategy = MagicMock(side_effect=lambda messages, budget: messages)
    llm_client = MagicMock(return_value=f"Answer: {item['answer']}")
    logger = MagicMock()

    prediction = task.run(
        item=item,
        strategy=strategy,
        llm_client=llm_client,
        tokenizer_fn=tokenizer_fn,
        max_tokens=4096,
        logger=logger,
    )

    assert prediction == f"Answer: {item['answer']}"
    assert task.grade(prediction, item) is True
    assert strategy.called
